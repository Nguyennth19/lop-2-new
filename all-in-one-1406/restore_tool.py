"""Offline restore of a Windows local checkpoint from an existing backup.
Run only after closing all LOP2 runner and backup processes.
"""
import argparse
import os
from pathlib import Path
import shutil
import sqlite3
import time
from runlock import exclusive_run_lock

p=argparse.ArgumentParser()
p.add_argument('--state-dir',type=Path,required=True)
p.add_argument('--backup-dir',type=Path,required=True)
p.add_argument('--confirm',action='store_true')
a=p.parse_args()
if not a.confirm:raise SystemExit('RESTORE_REQUIRES_EXPLICIT_CONFIRM')
backup=a.backup_dir.resolve(); state=a.state_dir.resolve()
if state==backup or state in backup.parents or backup in state.parents:raise SystemExit('BACKUP_STATE_PATH_OVERLAP')
source_db=backup/'checkpoint.sqlite3'
if not source_db.is_file():raise SystemExit('BACKUP_DATABASE_MISSING')
with sqlite3.connect(str(source_db)) as test:
    if test.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise SystemExit('BACKUP_CORRUPTED')
if not (backup/'objects').is_dir():raise SystemExit('BACKUP_EVIDENCE_MISSING')
state.mkdir(parents=True,exist_ok=True)
with exclusive_run_lock(state):
    # Preserve previous state before touching it, allowing the owner to roll back.
    if (state/'checkpoint.sqlite3').exists():
        keep=state.parent/(state.name+'-before-restore-'+time.strftime('%Y%m%d-%H%M%S'))
        keep.mkdir(exist_ok=False)
        shutil.copy2(state/'checkpoint.sqlite3',keep/'checkpoint.sqlite3')
        if (state/'objects').exists():shutil.copytree(state/'objects',keep/'objects')
    tmp=state/'checkpoint.restore.tmp'
    shutil.copy2(source_db,tmp);os.replace(tmp,state/'checkpoint.sqlite3')
    for src in (backup/'objects').rglob('*'):
        if not src.is_file():continue
        rel=src.relative_to(backup/'objects')
        dest=state/'objects'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists() or dest.stat().st_size!=src.stat().st_size:
            tmp=dest.with_suffix(dest.suffix+'.restore.tmp');shutil.copy2(src,tmp);os.replace(tmp,dest)
print('RESTORE_OK: rerun RUN_ALL.bat to continue from restored checkpoints')