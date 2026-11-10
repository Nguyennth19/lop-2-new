#!/usr/bin/env python3
"""Privacy-preserving, read-only Windows readiness report for LOP2.

No private source content, keys, machine/user names, or PDF text are written.
Never installs anything; Ollama is probed only on the loopback interface.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

MIN_PYTHON=(3,11)
MIN_FREE_GB=20


def available_gb(directory: Path):
    """Find the nearest existing ancestor to support not-yet-created folders."""
    p=directory.expanduser().resolve()
    while not p.exists() and p != p.parent:
        p=p.parent
    return round(shutil.disk_usage(p).free/(1024**3),1)


def system_memory_gb():
    if os.name!='nt':
        try:
            return round(os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')/(1024**3),1)
        except (AttributeError,ValueError,OSError):
            return None
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_=[('dwLength',ctypes.c_ulong),('dwMemoryLoad',ctypes.c_ulong),
                     ('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),
                     ('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),
                     ('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),
                     ('ullAvailExtendedVirtual',ctypes.c_ulonglong)]
        v=MEMORYSTATUSEX();v.dwLength=ctypes.sizeof(v)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(v)):
            return round(v.ullTotalPhys/(1024**3),1)
    except Exception:
        pass
    return None


def windows_gpu_names():
    """Only hardware model names, no serial numbers or user information."""
    if os.name!='nt':return []
    try:
        command=['powershell','-NoProfile','-NonInteractive','-Command',
                 'Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name']
        p=subprocess.run(command,capture_output=True,text=True,timeout=12,check=False)
        if p.returncode==0:
            return [x.strip()[:120] for x in p.stdout.splitlines() if x.strip()][:5]
    except (OSError,subprocess.TimeoutExpired):
        pass
    return []


def probe_ollama(model='qwen2.5vl:7b', url='http://127.0.0.1:11434'):
    if url not in ('http://127.0.0.1:11434','http://localhost:11434'):
        return {'status':'BLOCKED','reason':'OLLAMA_LOOPBACK_REQUIRED'}
    try:
        with urllib.request.urlopen(url+'/api/tags',timeout=4) as result:
            data=json.load(result)
    except (OSError,ValueError,urllib.error.URLError,TimeoutError):
        return {'status':'BLOCKED','reason':'OLLAMA_NOT_RUNNING','model':model}
    models=[x.get('name','') for x in data.get('models',[]) if isinstance(x,dict)]
    if model not in models:
        return {'status':'BLOCKED','reason':'VISION_MODEL_NOT_INSTALLED','model':model}
    return {'status':'READY','model':model,'local_only':True}


def check(root:Path, model='qwen2.5vl:7b', probe=probe_ollama,
          mem=system_memory_gb, gpu=windows_gpu_names):
    root=root.resolve()
    private=root/'PRIVATE_INPUTS'
    names=('SOURCE_1406.csv','SGK_T1.pdf','SGK_T2.pdf','VBT_T1.pdf','VBT_T2.pdf')
    found=[n for n in names if (private/n).is_file()]
    missing=sorted(set(names)-set(found))
    try:free=available_gb(root)
    except OSError:free=None
    memory=mem()
    py_ok=sys.version_info[:2]>=MIN_PYTHON
    disk_ok=free is not None and free>=MIN_FREE_GB
    # 32GB is a recommendation, not a hard gate: small CPU-only models may still run.
    ollama=probe(model)
    checks={'python':'READY' if py_ok else 'BLOCKED',
            'private_inputs':'READY' if not missing else 'BLOCKED',
            'ssd_space':'READY' if disk_ok else 'BLOCKED',
            'ollama':'READY' if ollama['status']=='READY' else 'BLOCKED'}
    return {'schema':'LOP2_PC_READINESS_1','checked_at':datetime.now(timezone.utc).isoformat(),
            'system':platform.system(), 'python_version':platform.python_version(),
            'ram_gb':memory, 'gpu_models':gpu(), 'free_space_gb':free,
            'required_free_gb':MIN_FREE_GB,'source_file_count':len(found),
            'missing_input_file_names':missing, 'ollama':ollama,
            'checks':checks,'ready_for_source_preflight':py_ok and not missing and disk_ok,
            'ready_for_canary':all(x=='READY' for x in checks.values()),
            'source_sha256_verified':False,
            'note':'This PC report does not replace CHECK_ONLY source hash verification or live canary QA.'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--model',default=os.environ.get('LOP2_LOCAL_MODEL','qwen2.5vl:7b'))
    p.add_argument('--report',type=Path)
    args=p.parse_args()
    report=check(args.root,args.model)
    raw=json.dumps(report,ensure_ascii=False,indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        temp=args.report.with_suffix('.tmp')
        temp.write_text(raw,encoding='utf-8')
        os.replace(temp,args.report)
    print(raw)
    if not report['ready_for_canary']:raise SystemExit(2)

if __name__=='__main__':main()