#!/usr/bin/env python3
"""Live, private cloud connection checks and a fail-closed canary gate.

Preflight is deliberately distinct from content QA: a successful probe does NOT
claim source transcription, N9 browser coverage, N10 approval or production readiness.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets

from state_store import AuditStore, S3Objects, jbytes
from source_processor import sha256_file

CANARY_ID = "SGK_B001_K1_E01"


def connectivity_probe(objects: S3Objects, campaign: str) -> dict:
    """Verify real remote credentials: write/read/list/delete a random private object."""
    if not isinstance(objects, S3Objects):
        raise ValueError("REMOTE_S3_STORAGE_REQUIRED")
    key = f"campaigns/{campaign}/health/{secrets.token_hex(16)}.json"
    payload = jbytes({"test": "lop2-private-storage-roundtrip", "nonce": secrets.token_hex(16)})
    # The probe never contains source book data or credentials.
    objects.put(key, payload)
    try:
        readback = objects.get(key)
        if readback != payload:
            raise RuntimeError("REMOTE_PROBE_READBACK_MISMATCH")
        if key not in objects.list(f"campaigns/{campaign}/health/"):
            raise RuntimeError("REMOTE_PROBE_LIST_MISMATCH")
    finally:
        objects.delete(key)
    if objects.get(key) is not None:
        raise RuntimeError("REMOTE_PROBE_DELETE_MISMATCH")
    return {"remote_write": True, "remote_read": True,
            "remote_list": True, "remote_delete": True}


def validate_canary(store: AuditStore, source_id: str, manifest_sha256: str, model: str) -> dict:
    state = store.load(source_id)
    if not state or state.get("status") not in ("DRAFT_READY", "DRAFT_REVIEW_REQUIRED"):
        raise RuntimeError("CANARY_NO_SOURCE_BASED_DRAFT")
    key = state.get("extra", {}).get("draft_key")
    if not key:
        raise RuntimeError("CANARY_DRAFT_OBJECT_MISSING")
    raw = store.objects.get(key)
    if not raw:
        raise RuntimeError("CANARY_DRAFT_READBACK_FAILED")
    draft = json.loads(raw)
    evidence = draft.get("evidence") or {}
    if (draft.get("source_id") != source_id or not draft.get("student_slots")
        or not draft.get("verbatim_prompt_candidate")
        or not evidence.get("pdf_sha256") or not evidence.get("page_image_sha256")
        or not evidence.get("crop_sha256")
        or draft.get("slot_count") != len(draft.get("student_slots",[]))
        or draft.get("qa",{}).get("extraction_method") != "AI_VISION_DRAFT"):
        raise RuntimeError("CANARY_INSUFFICIENT_DRAFT_EVIDENCE")
    if (draft.get("release_allowed") is not False
        or draft.get("qa", {}).get("n9_engine_browser_pass") is not False
        or draft.get("qa", {}).get("n10_reviewer_signed") is not False
        or draft.get("qa", {}).get("n12_release_allowed") is not False):
        raise RuntimeError("CANARY_UNSAFE_RELEASE_FLAG")
    gate = {"schema": 1, "source_id": source_id, "model": model,
            "manifest_sha256": manifest_sha256, "draft_sha256": hashlib.sha256(raw).hexdigest(),
            "gate_type": "LIVE_VISION_DRAFT_CREATED_NOT_N9_N10_N12", "status": "PASSED"}
    gate_key = f"{store.root}/control/canary_gate.json"
    existing = store.objects.get(gate_key)
    if existing and json.loads(existing) != gate:
        raise RuntimeError("CANARY_GATE_CONFLICT_NEW_CAMPAIGN_REQUIRED")
    if not existing:
        store.objects.put(gate_key, jbytes(gate))
    if json.loads(store.objects.get(gate_key)) != gate:
        raise RuntimeError("CANARY_GATE_REMOTE_READBACK_FAILED")
    return {"canary_ready": True, "draft_source_id": source_id,
            "source_verified_by_reviewer": False, "n9": False, "n10": False, "release_allowed": False}


def check_canary_gate(store: AuditStore, manifest_sha256: str, model: str, source_id: str = CANARY_ID) -> None:
    key = f"{store.root}/control/canary_gate.json"
    raw = store.objects.get(key)
    if raw is None:
        raise RuntimeError("CANARY_GATE_NOT_PRESENT")
    gate = json.loads(raw)
    if (gate.get("status") != "PASSED" or gate.get("manifest_sha256") != manifest_sha256
        or gate.get("model") != model or gate.get("source_id") != source_id
        or gate.get("gate_type") != "LIVE_VISION_DRAFT_CREATED_NOT_N9_N10_N12"):
        raise RuntimeError("CANARY_GATE_SOURCE_OR_MODEL_MISMATCH")
    state = store.load(source_id)
    if not state or state.get("status") not in ("DRAFT_READY", "DRAFT_REVIEW_REQUIRED"):
        raise RuntimeError("CANARY_GATE_STATE_DRIFT")
    raw_draft = store.objects.get(state.get("extra", {}).get("draft_key", ""))
    if not raw_draft or hashlib.sha256(raw_draft).hexdigest() != gate.get("draft_sha256"):
        raise RuntimeError("CANARY_GATE_DRAFT_HASH_DRIFT")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--campaign", required=True)
    p.add_argument("--action", choices=["probe", "mark-canary", "check-canary"], required=True)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--canary-source-id", default=CANARY_ID)
    a = p.parse_args()
    if a.action != 'probe' and (not a.manifest or not a.manifest.is_file()):
        raise SystemExit("PRIVATE_MANIFEST_REQUIRED")
    obj = S3Objects(os.environ.get('LOP2_S3_BUCKET'), os.getenv('LOP2_S3_PREFIX', 'lop2'),
                    os.getenv('LOP2_S3_ENDPOINT'))
    store = AuditStore(obj, a.campaign)
    model = os.getenv('LOP2_VISION_MODEL', '')
    if a.action == 'probe':
        print(json.dumps(connectivity_probe(obj, a.campaign)))
    else:
        manifest_sha = sha256_file(a.manifest)
        if a.action == 'mark-canary':
            print(json.dumps(validate_canary(store, a.canary_source_id, manifest_sha, model)))
        else:
            check_canary_gate(store, manifest_sha, model, a.canary_source_id)
            print('{"canary_gate_verified": true, "n9": false, "n10": false}')

if __name__ == "__main__":
    main()