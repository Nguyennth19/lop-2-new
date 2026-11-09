"""Source-locked PDF ingestion. Never infer source truth from a file hash alone."""
from __future__ import annotations
import hashlib
from pathlib import Path
import fitz

SOURCE_LOCKS = {
    ("SGK", "1"): ("SGK_T1.pdf", "cb8cb303294edc0be2f36a9507965b59345c0d53c296d610858e7454dfa8321e"),
    ("VBT", "1"): ("VBT_T1.pdf", "7c77820bb52a9f59b790180a16adc8231993768f59a16bb86084bb2f65f171cf"),
    ("SGK", "2"): ("SGK_T2.pdf", "044142f31fa94769a143dd029422ee74c49480ad9304e567cc8d97efa4c42f36"),
    ("VBT", "2"): ("VBT_T2.pdf", "9f3b4d9ff793e4280de7e72d1854a7492d77c88809c9bd9c2be4fa9af3b732c2"),
}
SOURCE_FILE_IDS = {
    ("SGK", "1"): "1Zfiw7VMZ_34cW1ZfaY3iuoRJLmaEuvfr",
    ("VBT", "1"): "1YIWc2IJtyQQ-e5w6-Zrzwwik7-EEyqoW",
    ("SGK", "2"): "1T8RaavitX03_f0VvxjO1zOiXjnMBhrrs",
    ("VBT", "2"): "15XyTPJBRMHXGikjGyZ_o4vWzQWTOtVCU",
}

class SourceError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)

def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()

class SourceProcessor:
    def __init__(self, pdf_root: Path, locks=None):
        self.root = Path(pdf_root)
        self.locks = locks or SOURCE_LOCKS
        self._verified = {}

    def verify_all(self, require_all=True):
        result = {}
        for key, (filename, expected) in self.locks.items():
            path = self.root / filename
            if not path.exists():
                if require_all: raise SourceError(f"PDF_NOT_FOUND:{filename}")
                continue
            actual = sha256_file(path)
            if actual.lower() != expected.lower(): raise SourceError(f"PDF_SHA_MISMATCH:{filename}")
            self._verified[key] = path
            result[f"{key[0]}_T{key[1]}"] = {"file": filename, "sha256": actual}
        return result

    def render(self, record: dict, dpi=155) -> dict:
        key = (record["track"], str(record["volume"]))
        if key not in self.locks: raise SourceError("TRACK_VOLUME_UNKNOWN")
        if key not in self._verified: self.verify_all(require_all=False)
        if key not in self._verified: raise SourceError("PDF_NOT_FOUND")
        filename, expected = self.locks[key]
        if str(record.get("source_sha256", "")).lower() != expected.lower():
            raise SourceError("ROW_SOURCE_SHA_MISMATCH")
        expected_id = SOURCE_FILE_IDS.get(key)
        if record.get("source_file_id") and expected_id and record["source_file_id"] != expected_id:
            raise SourceError("ROW_SOURCE_FILE_ID_MISMATCH")
        page = record.get("page", "")
        if not str(page).isdigit() or int(page) < 1: raise SourceError("PDF_PAGE_MISSING_OR_INVALID")
        with fitz.open(self._verified[key]) as pdf:
            if int(page) > len(pdf): raise SourceError("PDF_PAGE_OUT_OF_RANGE")
            p = pdf[int(page) - 1]
            # Source pages are often scanned. Text is advisory; image is authoritative.
            png = p.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False).tobytes("png")
            text_layer = p.get_text("text")
        return {
            "png": png, "image_sha256": sha256_bytes(png),
            "pdf_sha256": expected, "pdf_file": filename,
            "page": int(page), "text_layer_chars": len(text_layer.strip()),
        }

    @staticmethod
    def crop(png: bytes, box_norm: list[int]) -> bytes:
        from PIL import Image
        import io
        if len(box_norm) != 4: raise SourceError("BBOX_INVALID")
        x0,y0,x1,y1 = box_norm
        if not (0 <= x0 < x1 <= 1000 and 0 <= y0 < y1 <= 1000):
            raise SourceError("BBOX_INVALID")
        img = Image.open(io.BytesIO(png))
        bbox=(int(x0*img.width/1000),int(y0*img.height/1000),int(x1*img.width/1000),int(y1*img.height/1000))
        out=io.BytesIO()
        img.crop(bbox).save(out,format="PNG")
        return out.getvalue()