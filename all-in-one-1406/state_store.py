"""Durable external checkpoint protocol: immutable event objects + last-record pointer.
One active writer per campaign is REQUIRED (GitHub Actions concurrency). Never put credentials here.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import uuid


def jbytes(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def sha(x): return hashlib.sha256(x).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def clean_id(source_id): return hashlib.sha256(source_id.encode()).hexdigest()

class LocalObjects:
    def __init__(self, directory): self.root=Path(directory);self.root.mkdir(parents=True,exist_ok=True)
    def get(self,key):
        path=self.root/key
        return path.read_bytes() if path.is_file() else None
    def put(self,key, data):
        p=self.root/key;p.parent.mkdir(parents=True,exist_ok=True)
        tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp')
        with tmp.open('wb') as f: f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    def list(self,prefix):
        p=self.root/prefix
        return [str(x.relative_to(self.root)) for x in p.rglob('*') if x.is_file()] if p.exists() else []

class S3Objects:
    def __init__(self,bucket,prefix='',endpoint_url=None,client=None):
        if not bucket: raise ValueError('S3_BUCKET_REQUIRED')
        self.bucket=bucket
        self.prefix=prefix.strip('/')
        if client is None:
            import boto3
            client=boto3.client('s3',endpoint_url=endpoint_url or None)
        self.client=client
    def _key(self,k):return '/'.join(p for p in (self.prefix,k.lstrip('/')) if p)
    def get(self,key):
        from botocore.exceptions import ClientError
        try:return self.client.get_object(Bucket=self.bucket,Key=self._key(key))['Body'].read()
        except ClientError as exc:
            if exc.response['Error']['Code'] in ('NoSuchKey','404','NotFound'):return None
            raise
    def put(self,key,data):
        self.client.put_object(Bucket=self.bucket,Key=self._key(key),Body=data,ContentType='application/json' if key.endswith('.json') else 'application/octet-stream',ServerSideEncryption='AES256')
    def list(self,prefix):
        result=[];token=None
        while True:
            kw=dict(Bucket=self.bucket,Prefix=self._key(prefix))
            if token:kw['ContinuationToken']=token
            r=self.client.list_objects_v2(**kw)
            result.extend(x['Key'][len(self.prefix)+1:] if self.prefix else x['Key'] for x in r.get('Contents',[]))
            if not r.get('IsTruncated'):break
            token=r['NextContinuationToken']
        return result

class AuditStore:
    def __init__(self,objects,campaign):
        if not campaign or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.' for c in campaign):
            raise ValueError('INVALID_CAMPAIGN_ID')
        self.objects=objects;self.root=f'campaigns/{campaign}'
    def key(self,source_id): return clean_id(source_id)
    def load(self,source_id):
        data=self.objects.get(f'{self.root}/records/{self.key(source_id)}.json')
        return json.loads(data) if data else None
    def event(self,source_id,stage,status,reason='',info=None):
        event={"source_id":source_id,"timestamp":now(),"stage":stage,"status":status,
               "reason_code":reason,"details":info or {},"event_id":uuid.uuid4().hex}
        key=f'{self.root}/events/{self.key(source_id)}/{event["event_id"]}.json'
        self.objects.put(key,jbytes(event))
        return event
    def commit(self,source_id,status,stage,reason='',extra=None):
        previous=self.load(source_id)
        progress={"source_id":source_id,"stage":stage,"status":status,
                  "reason_code":reason,"updated_at":now(),"extra":extra or {},
                  "previous_sha256":sha(jbytes(previous)) if previous else None}
        # Append event FIRST; update checkpoint pointer second. Interrupted between these
        # writes produces a repeatable stage, not an invented completion.
        self.event(source_id,stage,status,reason,{"record_sha256":sha(jbytes(progress)),"previous":progress['previous_sha256']})
        self.objects.put(f'{self.root}/records/{self.key(source_id)}.json',jbytes(progress))
        return progress
    def evidence(self,source_id,label,data,extension='bin'):
        key=f'{self.root}/evidence/{self.key(source_id)}/{label}-{sha(data)}.{extension}'
        if self.objects.get(key) is None:self.objects.put(key,data)
        return key
    def save_draft(self,source_id,payload):
        data=jbytes(payload)
        key=f'{self.root}/drafts/{self.key(source_id)}-{sha(data)}.json'
        if self.objects.get(key) is None:self.objects.put(key,data)
        return key
    def states(self):
        for path in self.objects.list(f'{self.root}/records/'):
            data=self.objects.get(path)
            if data:yield json.loads(data)
    def summary(self,total_source_ids=0):
        stats={};items=list(self.states())
        for i in items: stats[i['status']]=stats.get(i['status'],0)+1
        return {"campaign":self.root.split('/')[-1],"tracked":len(items),"expected":total_source_ids,
                "by_status":stats,"source_independently_certified":0,"n9_pass":0,
                "n10_signed":0,"releasable":0,"timestamp":now()}