#!/usr/bin/env python3
"""Windows one-shot/local runner with ACID SQLite and resumable evidence blobs.
Does not claim source validation/release. Full scan requires local Ollama vision model.
"""
import argparse
import csv
import csv
import json
import os
from pathlib import Path
import shutil
import sys
import time
import uuid
from source_processor import SourceProcessor, sha256_file
from runner import load_manifest,run_pipeline,TERMINAL
from windows_store import WindowsAuditStore
from local_vision import OllamaExtractor
from runlock import exclusive_run_lock

DEFAULT_CAMPAIGN='lop2-local-1406-v1'

def export_reports(store,state_dir):
    """Regenerate human-readable, source-text-free audit views from durable SQLite."""
    state_dir=Path(state_dir);state_dir.mkdir(parents=True,exist_ok=True)
    path=state_dir/"records.csv";tmp=path.with_suffix(".tmp")
    with tmp.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.writer(f);writer.writerow(("source_id","stage","status","reason_code","updated_at","draft_key"))
        for row in store.states():
            writer.writerow((row["source_id"],row["stage"],row["status"],row.get("reason_code",""),row.get("updated_at",""),row.get("extra",{}).get("draft_key","")))
        f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
    store.journal_export(state_dir/"events.jsonl")

def backup_files(store,backup_root,copy_blobs=True):
    """Consistent SQLite snapshot + read-only immutable evidence blobs copied incrementally.
    Backup is NOT disaster-proof when backup_root is on the same physical SSD.
    """
    backup_root=Path(backup_root).resolve();backup_root.mkdir(parents=True,exist_ok=True)
    db=store.backup_database(backup_root/'checkpoint.sqlite3')
    if copy_blobs:
        src=store.state_dir/'objects'; dst=backup_root/'objects'
        if src.exists():
            for item in src.rglob('*'):
                if not item.is_file():continue
                target=dst/item.relative_to(src)
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists() and target.stat().st_size==item.stat().st_size:continue
                tmp=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
                shutil.copy2(item,tmp);os.replace(tmp,target)
    store.journal_export(backup_root/'events.jsonl')
    proof={'campaign':store.campaign,'database_integrity':'ok','db_bytes':db.stat().st_size,
           'backup_folder':str(backup_root)}
    (backup_root/'BACKUP_INFO.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
    return proof

def execute(args, extractor_override=None, source_override=None, inject_interrupt_after=None):
    input_root=Path(args.input_dir).resolve()
    manifest=input_root/'SOURCE_1406.csv'
    rows=load_manifest(manifest,args.expected_count,args.expected_bqas)
    source=source_override or SourceProcessor(input_root)
    store=WindowsAuditStore(Path(args.state_dir),args.campaign)
    try:
        verified=source.verify_all(True)
        lock={'schema':1,'manifest_sha256':sha256_file(manifest),'count':len(rows),
              'source_pdfs':{k:v['sha256'] for k,v in verified.items()}}
        store.lock_inputs(lock)
        if store.integrity()!='ok':raise RuntimeError('STATE_SQLITE_CORRUPTED')
        extractor=extractor_override or OllamaExtractor(model=args.model,endpoint=args.ollama_url)
        status={'campaign':args.campaign,'input_records':len(rows),'bqas':len({x['bqa'] for x in rows}),
                'source_pdfs':len(verified),'source_manifest_sha256':lock['manifest_sha256'],
                'sqlite_integrity':'ok','mode':args.mode}
        if args.mode in ('run','canary'):
            # Before calling an AI: fail fast, rather than marking 1406 rows as exceptions.
            if not extractor_override:status['ollama']=extractor.preflight()
            candidates=rows if args.mode=='run' else [x for x in rows if x['source_id']==args.canary_id]
            if not candidates:raise ValueError('CANARY_ID_NOT_IN_MANIFEST')
            # One invocation traverses all 1406; periodic checkpoint already each stage.
            # Chunk loop triggers snapshot every N items, and on exceptions/finally.
            done=0;max_items=min(args.max_items,len(candidates))
            for start in range(0,len(candidates),args.chunk_size):
                if done>=max_items:break
                chunk=candidates[start:start+min(args.chunk_size,max_items-done)]
                result=run_pipeline(chunk,source,store,extractor,max_items=len(chunk),max_seconds=args.max_seconds,
                                    retry_exceptions=args.retry_exceptions,inject_interrupt_after=inject_interrupt_after)
                done+=len(chunk)
                if args.backup_dir:
                    backup_files(store,args.backup_dir)
                _write_status(args.status_file,store,len(rows),result)
                export_reports(store,args.state_dir)
            status.update(store.summary(len(rows)))
            status['this_invocation_scanned']=done
        elif args.mode=='preflight':
            status['ollama_configuration']='not required for source preflight'
            status.update(store.summary(len(rows)))
        else:raise ValueError('MODE_INVALID')
        _write_status(args.status_file,store,len(rows),status)
        export_reports(store,args.state_dir)
        return status
    finally:
        # Any interruption should produce an immediately restorable copy.
        try:
            if args.backup_dir:backup_files(store,args.backup_dir)
        finally:store.close()

def _write_status(path,store,total,detail):
    if not path:return
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    summary=store.summary(total)
    summary.update({'last_segment':detail.get('this_invocation_processed',0),'run_type':'DRAFT_ONLY_NOT_N9_N10_RELEASE'})
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(tmp,path)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input-dir',required=True,type=Path)
    p.add_argument('--state-dir',required=True,type=Path)
    p.add_argument('--backup-dir',type=Path)
    p.add_argument('--status-file',type=Path)
    p.add_argument('--campaign',default=DEFAULT_CAMPAIGN)
    p.add_argument('--mode',choices=['preflight','canary','run'],default='preflight')
    p.add_argument('--model',default=os.environ.get('LOP2_LOCAL_MODEL','qwen2.5vl:7b'))
    p.add_argument('--ollama-url',default='http://127.0.0.1:11434')
    p.add_argument('--canary-id',default='SGK_B001_K1_E01')
    p.add_argument('--expected-count',type=int,default=1406)
    p.add_argument('--expected-bqas',type=int,default=21)
    p.add_argument('--max-items',type=int,default=1406)
    p.add_argument('--max-seconds',type=int,default=31536000)
    p.add_argument('--chunk-size',type=int,default=5)
    p.add_argument('--retry-exceptions',action='store_true')
    args=p.parse_args()
    if args.chunk_size<1 or args.chunk_size>100:raise ValueError('CHUNK_SIZE_OUT_OF_RANGE')
    if args.max_items<1:raise ValueError('MAX_ITEMS_OUT_OF_RANGE')
    if args.backup_dir and args.state_dir.resolve()==args.backup_dir.resolve():raise ValueError('BACKUP_DIR_MUST_DIFFER')
    with exclusive_run_lock(args.state_dir):
        output=execute(args)
    print(json.dumps(output,ensure_ascii=False,indent=2))
if __name__=='__main__':main()