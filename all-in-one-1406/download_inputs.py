#!/usr/bin/env python3
"""Fetch private SOURCE_1406.csv + four original PDFs from a private S3-compatible bucket.

Only run on a protected Actions environment; never publish the input directory as CI artifacts.
"""
from __future__ import annotations
import os
from pathlib import Path
import boto3
from source_processor import SOURCE_LOCKS, sha256_file

def fetch_inputs(out:Path,bucket:str,prefix:str,endpoint=None,client=None):
    if not bucket:raise ValueError('BUCKET_REQUIRED')
    if client is None:client=boto3.client('s3',endpoint_url=endpoint)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    paths=['SOURCE_1406.csv']+[v[0] for v in SOURCE_LOCKS.values()]
    for name in paths:
        key='/'.join(p for p in (prefix.strip('/'),'inputs',name) if p)
        dest=out/name
        tmp=out/(name+'.partial')
        try:
            client.download_file(bucket,key,str(tmp))
            expected=next((sha for _,(filename,sha) in SOURCE_LOCKS.items() if filename==name),None)
            if expected and sha256_file(tmp)!=expected:
                raise ValueError('DOWNLOADED_PDF_SHA_MISMATCH:'+name)
            tmp.replace(dest)
        finally:
            tmp.unlink(missing_ok=True)
    return paths

if __name__=='__main__':
    names=fetch_inputs(Path(os.environ['LOP2_INPUT_DIR']),os.environ['LOP2_S3_BUCKET'],os.environ.get('LOP2_S3_PREFIX','lop2'),os.getenv('LOP2_S3_ENDPOINT'))
    print(f'Private source input files verified: {len(names)}')