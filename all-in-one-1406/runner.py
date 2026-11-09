#!/usr/bin/env python3
"""LOP2 1406 manifest traversal with durable, fail-closed state.

No OCR, canonical content generation, source sign-off or QA pass is asserted.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from datetime import datetime, timezone

REQUIRED = ("source_id", "lesson_id", "owner_batch", "track", "volume", "pdf_page", "source_sha256")
TERMINAL = {"SOURCE_PROCESSING_REQUIRED", "INPUT_EXCEPTION", "SOURCE_CONFLICT"}

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

def connect(path: Path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS records(
      source_id TEXT PRIMARY KEY, lesson_id TEXT, bqa TEXT,
      input_hash TEXT NOT NULL, status TEXT NOT NULL, reason TEXT NOT NULL,
      source_page TEXT, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS events(
      event_id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_id TEXT NOT NULL, at TEXT NOT NULL, event_type TEXT NOT NULL,
      input_hash TEXT NOT NULL, status TEXT NOT NULL, reason TEXT NOT NULL
    );
    """)
    return conn

def classify(row):
    for field in REQUIRED:
        if not str(row.get(field, "")).strip():
            return "INPUT_EXCEPTION", "MISSING_" + field.upper()
    page = str(row["pdf_page"]).strip()
    if not page.isdigit() or int(page) < 1:
        return "INPUT_EXCEPTION", "PDF_PAGE_INVALID"
    if row["track"] not in ("SGK", "VBT"):
        return "INPUT_EXCEPTION", "TRACK_INVALID"
    if row["volume"] not in ("1", "2"):
        return "INPUT_EXCEPTION", "VOLUME_INVALID"
    if len(row["source_sha256"].strip()) != 64 or any(c not in "0123456789abcdefABCDEF" for c in row["source_sha256"].strip()):
        return "INPUT_EXCEPTION", "SOURCE_SHA256_INVALID"
    return "SOURCE_PROCESSING_REQUIRED", "EXACT_TEXT_SLOTS_ASSETS_VALIDATOR_RUNTIME_NOT_PROVEN"

def append_event_jsonl(path: Path, event: dict):
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        fp.flush()
        os.fsync(fp.fileno())

def export_views(conn, state_dir: Path):
    rows = conn.execute("SELECT source_id,lesson_id,bqa,status,reason,source_page,updated_at FROM records ORDER BY bqa,source_id").fetchall()
    counts = {}
    for row in rows:
        counts[row[3]] = counts.get(row[3], 0) + 1
    groups = {}
    for row in rows:
        group = row[2] or "UNKNOWN"
        groups.setdefault(group, {"total": 0, "by_status": {}})
        groups[group]["total"] += 1
        s = row[3]
        groups[group]["by_status"][s] = groups[group]["by_status"].get(s, 0) + 1
    output = {"generated_at": utc_now(), "total": len(rows), "by_status": counts, "by_bqa": groups,
              "source_verified": 0, "engine_ready": 0, "release_approved": 0,
              "note": "Manifest traversal and metadata checks only. No content proof or release."}
    tmp = state_dir / "summary.json.tmp"
    tmp.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(state_dir / "summary.json")
    tmp_csv = state_dir / "exceptions.csv.tmp"
    with tmp_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(("source_id", "lesson_id", "bqa", "status", "reason", "pdf_page", "updated_at"))
        w.writerows(rows)
    tmp_csv.replace(state_dir / "exceptions.csv")
    return output

def execute(manifest: Path, state_dir: Path, retry: bool = False):
    state_dir.mkdir(parents=True, exist_ok=True)
    conn = connect(state_dir / "state.sqlite3")
    try:
        with manifest.open(encoding="utf-8-sig", newline="") as fp:
            reader = csv.DictReader(fp)
            if not reader.fieldnames or not set(REQUIRED).issubset(reader.fieldnames):
                raise ValueError("Manifest missing columns: " + ", ".join(sorted(set(REQUIRED) - set(reader.fieldnames or []))))
            seen = set()
            for number, row in enumerate(reader, start=2):
                source_id = str(row.get("source_id", "")).strip() or f"INVALID_ROW_{number}"
                identity = digest(row)
                if source_id in seen:
                    status, reason = "SOURCE_CONFLICT", "DUPLICATE_SOURCE_ID_IN_INPUT"
                else:
                    status, reason = classify(row)
                seen.add(source_id)
                old = conn.execute("SELECT input_hash,status FROM records WHERE source_id=?", (source_id,)).fetchone()
                if old and old[0] == identity and not retry:
                    continue
                event = {"source_id": source_id, "at": utc_now(), "event_type": "RECORD_CLASSIFIED",
                         "input_hash": identity, "status": status, "reason": reason}
                # Durable SQLite event/state transaction; JSONL is a secondary audit mirror.
                with conn:
                    conn.execute("""INSERT INTO records(source_id,lesson_id,bqa,input_hash,status,reason,source_page,updated_at)
                       VALUES(?,?,?,?,?,?,?,?)
                       ON CONFLICT(source_id) DO UPDATE SET lesson_id=excluded.lesson_id,
                       bqa=excluded.bqa,input_hash=excluded.input_hash,status=excluded.status,
                       reason=excluded.reason,source_page=excluded.source_page,updated_at=excluded.updated_at""",
                       (source_id, row.get("lesson_id",""), row.get("owner_batch",""), identity,
                        status, reason, row.get("pdf_page",""), event["at"]))
                    conn.execute("INSERT INTO events(source_id,at,event_type,input_hash,status,reason) VALUES(?,?,?,?,?,?)",
                                 (source_id, event["at"], event["event_type"], identity, status, reason))
                append_event_jsonl(state_dir / "events.jsonl", event)
        return export_views(conn, state_dir)
    finally:
        conn.close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--state-dir", required=True, type=Path)
    p.add_argument("--run-all", action="store_true", required=True)
    p.add_argument("--retry", action="store_true")
    a = p.parse_args()
    result = execute(a.manifest, a.state_dir, a.retry)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
