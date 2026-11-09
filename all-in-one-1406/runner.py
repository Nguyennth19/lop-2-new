#!/usr/bin/env python3
"""One invocation / 1406 candidates with durable source-first per-stage checkpoints.

This runner emits MACHINE DRAFTS and EXCEPTIONS, not N9/N10 PASS or release approvals.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from source_processor import SourceProcessor, SourceError, sha256_bytes, sha256_file
from question_builder import VisionExtractor, ExerciseDraft, BuildError, make_question
from state_store import AuditStore, LocalObjects, S3Objects, now
from engine_adapter import candidate_engine_payload

TERMINAL = {"DRAFT_READY", "DRAFT_REVIEW_REQUIRED", "EXCEPTION"}
MANDATORY = {"source_id", "lesson_id", "bqa", "track", "volume", "page", "source_sha256"}

class InterruptedByTest(Exception):pass

def normalize_row(raw):
    """Accept original V1 manifest columns without rewriting private source data."""
    r={k:(v or '').strip() for k,v in raw.items() if k}
    r['bqa']=r.get('bqa') or r.get('owner_batch','')
    r['page']=r.get('page') or r.get('pdf_page','')
    r['volume']=r.get('volume') or ('1' if r.get('source_file_id') in ('1Zfiw7VMZ_34cW1ZfaY3iuoRJLmaEuvfr','1YIWc2IJtyQQ-e5w6-Zrzwwik7-EEyqoW') else '2' if r.get('source_file_id') else '')
    return r

def load_manifest(path:Path,expected_count:int=1406,expected_bqas:int=21):
    with path.open('r',encoding='utf-8-sig',newline='') as f: rows=[normalize_row(r) for r in csv.DictReader(f)]
    if len(rows)!=expected_count: raise ValueError(f'MANIFEST_COUNT_MISMATCH:{len(rows)}!={expected_count}')
    ids=[r.get('source_id','') for r in rows]
    if len(set(ids))!=len(ids) or '' in ids: raise ValueError('MANIFEST_SOURCE_ID_DUPLICATE_OR_EMPTY')
    bqas={r.get('bqa','') for r in rows}
    if len(bqas)!=expected_bqas or '' in bqas: raise ValueError(f'MANIFEST_BQA_COUNT_MISMATCH:{len(bqas)}!={expected_bqas}')
    for r in rows:
        missing=MANDATORY-set(k for k,v in r.items() if v)
        # Missing PDF page is a row-level exception, not global failure.
        if missing-{'page'}: raise ValueError('MANIFEST_REQUIRED_FIELD_MISSING:'+r['source_id']+':'+','.join(sorted(missing)))
    return sorted(rows,key=lambda r:(r['bqa'],r['lesson_id'],r['source_id']))

def classify_error(exc):
    if isinstance(exc, (SourceError, BuildError)):return exc.code
    if isinstance(exc, (TimeoutError, ConnectionError)):return 'TRANSIENT_NETWORK_OR_TIMEOUT'
    message=str(exc).upper()
    if 'RATE_LIMIT' in message or '429' in message:return 'VISION_RATE_LIMIT'
    if 'INSUFFICIENT_QUOTA' in message:return 'VISION_QUOTA_EXCEEDED'
    if 'AUTHENTICATION' in message or '401' in message:return 'VISION_AUTH_FAILED'
    if 'VISION_DISABLED' in message:return 'VISION_NOT_CONFIGURED'
    return 'UNEXPECTED_PROCESSING_ERROR'

def run_pipeline(rows, source, store:AuditStore, extractor, max_items=35, max_seconds=15000,
                 retry_exceptions=False, inject_interrupt_after=None):
    started=time.monotonic(); processed=0; repeated=0; skipped=0; commits=0
    for rec in rows:
        if processed>=max_items or time.monotonic()-started>max_seconds:break
        sid=rec['source_id']
        current=store.load(sid)
        if current and current['status'] in TERMINAL and not (retry_exceptions and current['status']=='EXCEPTION'):
            skipped+=1; continue
        if current and current['status']=='EXCEPTION' and retry_exceptions: current=None
        processed+=1
        try:
            if current and current['stage'] in ('PAGE_LOCKED','VISION_EXTRACTED'):
                image_key=current['extra'].get('image_key')
                png=store.objects.get(image_key) if image_key else None
                if not png: raise SourceError('PAGE_IMAGE_CHECKPOINT_MISSING')
                evidence=current['extra']['evidence']
                if sha256_bytes(png)!=evidence['image_sha256']:
                    raise SourceError('PAGE_IMAGE_CHECKPOINT_HASH_CONFLICT')
                repeated+=1
            else:
                evidence=source.render(rec)
                png=evidence.pop('png')
                image_key=store.evidence(sid,'page',png,'png')
                current=store.commit(sid,'IN_PROGRESS','PAGE_LOCKED',extra={"image_key":image_key,"evidence":evidence})
                commits+=1
                if inject_interrupt_after==commits:raise InterruptedByTest('SYNTHETIC_KILL_AFTER_DURABLE_CHECKPOINT')
            if current['stage']=='VISION_EXTRACTED':
                raw_key=current['extra'].get('vision_key')
                saved=store.objects.get(raw_key) if raw_key else None
                if not saved: raise SourceError('VISION_CHECKPOINT_MISSING')
                extracted=ExerciseDraft.model_validate_json(saved)
            else:
                extracted=extractor.extract(rec,png)
                vision_key=store.save_draft(sid,extracted.model_dump())
                current=store.commit(sid,'IN_PROGRESS','VISION_EXTRACTED',extra={"image_key":image_key,"evidence":evidence,"vision_key":vision_key})
                commits+=1
                if inject_interrupt_after==commits:raise InterruptedByTest('SYNTHETIC_KILL_AFTER_DURABLE_CHECKPOINT')
            box=extracted.bbox_0_to_1000
            # The evidence crop is only generated for plausible source coordinates.
            crop_key=None;crop_hash=None
            if len(box)==4 and 0<=box[0]<box[2]<=1000 and 0<=box[1]<box[3]<=1000:
                crop=source.crop(png,box)
                crop_hash=sha256_bytes(crop)
                crop_key=store.evidence(sid,'crop',crop,'png')
            q=make_question(rec,extracted,evidence,crop_hash)
            q['source_crop_key']=crop_key
            q['engine_candidate']=candidate_engine_payload(q)
            q['qa']['n9_engine_browser_pass']=False
            # Drafts have no release privileges; nonempty uncertainty always goes to review.
            draft_key=store.save_draft(sid,q)
            status='DRAFT_REVIEW_REQUIRED' if q['qa']['uncertainties'] else 'DRAFT_READY'
            store.commit(sid,status,'DRAFT_SAVED',extra={"draft_key":draft_key,"source_crop_key":crop_key,
                       "slots":q['slot_count'],"image_key":image_key,"evidence":evidence})
            commits+=1
        except InterruptedByTest: raise
        except Exception as exc:
            # Do not log untrusted source text, API replies, credentials or stack traces.
            reason=classify_error(exc)
            if reason in {'VISION_AUTH_FAILED','VISION_QUOTA_EXCEEDED','VISION_RATE_LIMIT','TRANSIENT_NETWORK_OR_TIMEOUT','VISION_NOT_CONFIGURED'}:
                store.event(sid,'INFRASTRUCTURE_BLOCK','BLOCKED',reason)
                raise RuntimeError('INFRASTRUCTURE_BLOCK:'+reason) from None
            store.commit(sid,'EXCEPTION','PROCESSING_EXCEPTION',reason,extra={"source_page":rec.get('page',''),"bqa":rec.get('bqa','')})
            commits+=1
    summary=store.summary(len(rows))
    summary.update({"this_invocation_processed":processed,"checkpoint_reused":repeated,
                    "already_terminal_skipped":skipped,"commits_this_invocation":commits,
                    "remaining":max(0,len(rows)-sum(summary['by_status'].get(s,0) for s in TERMINAL)),
                    "run_type":"CONTENT_DRAFT_PIPELINE_NOT_RELEASE_APPROVAL"})
    return summary

def setup_store(kind,state_dir,campaign,bucket=None,prefix='',endpoint=None,s3_client=None):
    if kind=='s3': objects=S3Objects(bucket,prefix,endpoint,client=s3_client)
    else: objects=LocalObjects(state_dir)
    return AuditStore(objects,campaign)

def preflight(rows,source,store,vision_enabled,manifest_hash):
    if not vision_enabled: raise ValueError('OPENAI_API_KEY_OR_VISION_MODEL_NOT_CONFIGURED')
    locks=source.verify_all(True)
    # Live external read/write probe. No private page data or credentials are logged.
    lock_key=f'{store.root}/control/manifest_lock.json'
    lock={"schema":1,"manifest_sha256":manifest_hash,"source_count":len(rows),
          "source_pdfs":{k:v['sha256'] for k,v in locks.items()}}
    existing=store.objects.get(lock_key)
    if existing is not None:
        if json.loads(existing)!=lock:raise RuntimeError('CAMPAIGN_INPUT_FINGERPRINT_CONFLICT')
    else:
        store.objects.put(lock_key,json.dumps(lock,sort_keys=True).encode())
    if json.loads(store.objects.get(lock_key))!=lock:
        raise RuntimeError('CHECKPOINT_REMOTE_READBACK_FAILED')
    return {"ready":True,"source_rows":len(rows),"source_locks":len(locks),
            "bqa_count":len({r['bqa'] for r in rows}),"external_readback":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--pdf-root',type=Path,required=True)
    p.add_argument('--campaign',default='lop2-v2-campaign')
    p.add_argument('--mode',choices=['preflight','run'],default='preflight')
    p.add_argument('--store',choices=['s3','local'],default='s3')
    p.add_argument('--state-dir',type=Path,default=Path('state'))
    p.add_argument('--s3-bucket',default=os.getenv('LOP2_S3_BUCKET'))
    p.add_argument('--s3-prefix',default=os.getenv('LOP2_S3_PREFIX','lop2'))
    p.add_argument('--s3-endpoint',default=os.getenv('LOP2_S3_ENDPOINT'))
    p.add_argument('--max-items',type=int,default=35)
    p.add_argument('--max-seconds',type=int,default=15000)
    p.add_argument('--expected-count',type=int,default=1406)
    p.add_argument('--expected-bqas',type=int,default=21)
    p.add_argument('--retry-exceptions',action='store_true')
    p.add_argument('--summary-file',type=Path)
    a=p.parse_args()
    if a.max_items<1 or a.max_items>1406:raise ValueError('MAX_ITEMS_OUT_OF_RANGE')
    rows=load_manifest(a.manifest,a.expected_count,a.expected_bqas)
    source=SourceProcessor(a.pdf_root)
    store=setup_store(a.store,a.state_dir,a.campaign,a.s3_bucket,a.s3_prefix,a.s3_endpoint)
    model=os.getenv('LOP2_VISION_MODEL','')
    enabled=bool(os.getenv('OPENAI_API_KEY') and model)
    status=preflight(rows,source,store,enabled,sha256_file(a.manifest))
    if a.mode=='run':
        if os.getenv('LOP2_ALLOW_RUN')!='YES':raise ValueError('RUN_BLOCKED_LOP2_ALLOW_RUN_NOT_YES')
        summary=run_pipeline(rows,source,store,VisionExtractor(model=model),a.max_items,a.max_seconds,a.retry_exceptions)
        status.update(summary)
    if a.summary_file:
        a.summary_file.parent.mkdir(parents=True,exist_ok=True)
        a.summary_file.write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    # Public CI logs only numeric stats; no original content, image, prompts or proposed answers.
    print(json.dumps(status,ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__':sys.exit(main())