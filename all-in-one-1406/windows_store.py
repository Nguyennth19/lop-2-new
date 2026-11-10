"""SQLite ACID checkpoint/event journal + fsync'd, content-addressed local evidence.
One active local process per campaign. No network, no third-party storage.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid
from state_store import AuditStore, LocalObjects, jbytes, now, clean_id, sha

class WindowsAuditStore(AuditStore):
    def __init__(self, state_dir, campaign):
        state_dir=Path(state_dir).resolve();state_dir.mkdir(parents=True,exist_ok=True)
        self.state_dir=state_dir
        self.db_path=state_dir/'checkpoint.sqlite3'
        conn=sqlite3.connect(str(self.db_path),timeout=60,isolation_level="IMMEDIATE")
        conn.execute('PRAGMA journal_mode=WAL');conn.execute('PRAGMA synchronous=FULL');conn.execute('PRAGMA busy_timeout=60000')
        conn.executescript('''CREATE TABLE IF NOT EXISTS states (
            campaign TEXT NOT NULL, source_id TEXT NOT NULL, payload BLOB NOT NULL,
            PRIMARY KEY(campaign,source_id));
          CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, campaign TEXT NOT NULL,
            source_id TEXT NOT NULL, at TEXT NOT NULL, stage TEXT NOT NULL,
            status TEXT NOT NULL, reason TEXT NOT NULL, event_json BLOB NOT NULL);
          CREATE INDEX IF NOT EXISTS idx_events_campaign ON events(campaign,seq);
          CREATE TABLE IF NOT EXISTS control (campaign TEXT NOT NULL, k TEXT NOT NULL,
            value BLOB NOT NULL, PRIMARY KEY(campaign,k));''')
        self.conn=conn
        super().__init__(LocalObjects(state_dir/'objects'),campaign)
        self.campaign=campaign
    def close(self):self.conn.close()
    def load(self,source_id):
        result=self.conn.execute('SELECT payload FROM states WHERE campaign=? AND source_id=?',(self.campaign,source_id)).fetchone()
        return json.loads(result[0]) if result else None
    def event(self,source_id,stage,status,reason='',info=None):
        value={'source_id':source_id,'timestamp':now(),'stage':stage,'status':status,
               'reason_code':reason,'details':info or {},'event_id':uuid.uuid4().hex}
        with self.conn:
            self.conn.execute('INSERT INTO events(campaign,source_id,at,stage,status,reason,event_json) VALUES(?,?,?,?,?,?,?)',
                (self.campaign,source_id,value['timestamp'],stage,status,reason,jbytes(value)))
        return value
    def commit(self,source_id,status,stage,reason='',extra=None):
        previous=self.load(source_id)
        progress={'source_id':source_id,'stage':stage,'status':status,'reason_code':reason,
                  'updated_at':now(),'extra':extra or {},'previous_sha256':sha(jbytes(previous)) if previous else None}
        event={'source_id':source_id,'timestamp':now(),'stage':stage,'status':status,
               'reason_code':reason,'details':{'record_sha256':sha(jbytes(progress)),
                'previous':progress['previous_sha256']},'event_id':uuid.uuid4().hex}
        # State pointer and event are ATOMIC; evidence was persisted first.
        with self.conn:
            self.conn.execute('INSERT INTO events(campaign,source_id,at,stage,status,reason,event_json) VALUES(?,?,?,?,?,?,?)',
                (self.campaign,source_id,event['timestamp'],stage,status,reason,jbytes(event)))
            self.conn.execute('INSERT INTO states(campaign,source_id,payload) VALUES(?,?,?) ON CONFLICT(campaign,source_id) DO UPDATE SET payload=excluded.payload',
                (self.campaign,source_id,jbytes(progress)))
        return progress
    def states(self):
        for (value,) in self.conn.execute('SELECT payload FROM states WHERE campaign=? ORDER BY source_id',(self.campaign,)):
            yield json.loads(value)
    def lock_inputs(self,lock:dict):
        b=jbytes(lock)
        with self.conn:
            current=self.conn.execute('SELECT value FROM control WHERE campaign=? AND k=?',(self.campaign,'source_lock')).fetchone()
            if current is not None and current[0]!=b:raise RuntimeError('CAMPAIGN_INPUT_FINGERPRINT_CONFLICT')
            self.conn.execute('INSERT OR IGNORE INTO control(campaign,k,value) VALUES(?,?,?)',(self.campaign,'source_lock',b))
        assert self.conn.execute('SELECT value FROM control WHERE campaign=? AND k=?',(self.campaign,'source_lock')).fetchone()[0]==b
    def backup_database(self,destination:Path):
        destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
        temp=destination.with_name(destination.name+'.'+uuid.uuid4().hex+'.tmp')
        with sqlite3.connect(str(temp)) as target:self.conn.backup(target)
        with sqlite3.connect(str(temp)) as check:
            if check.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('BACKUP_SQLITE_INTEGRITY_FAIL')
        os.replace(temp,destination)
        return destination
    def journal_export(self,dest:Path):
        dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
        tmp=dest.with_suffix(dest.suffix+'.tmp')
        with tmp.open('w',encoding='utf-8') as f:
            for (value,) in self.conn.execute('SELECT event_json FROM events WHERE campaign=? ORDER BY seq',(self.campaign,)):
                f.write(value.decode('utf-8')+'\n')
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,dest)
    def integrity(self):return self.conn.execute('PRAGMA integrity_check').fetchone()[0]