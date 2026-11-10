from pathlib import Path
import argparse
from windows_store import WindowsAuditStore
from windows_runner import backup_files
p=argparse.ArgumentParser()
p.add_argument('--state-dir',type=Path,required=True);p.add_argument('--backup-dir',type=Path,required=True)
p.add_argument('--campaign',default='lop2-local-1406-v1')
a=p.parse_args()
s=WindowsAuditStore(a.state_dir,a.campaign)
try:print(backup_files(s,a.backup_dir))
finally:s.close()