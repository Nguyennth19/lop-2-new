"""Cross-platform exclusive single-writer advisory lock for one local installation."""
from contextlib import contextmanager
from pathlib import Path
import os

@contextmanager
def exclusive_run_lock(folder):
    path=Path(folder)/'runner.lock';path.parent.mkdir(parents=True,exist_ok=True)
    fp=open(path,'a+b')
    try:
        fp.seek(0,2)
        if fp.tell()==0:fp.write(b'0')
        fp.flush();fp.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(fp.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(fp.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as ex:raise RuntimeError('ANOTHER_WINDOWS_RUNNER_IS_ACTIVE') from ex
        yield
    finally:
        try:
            fp.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(fp.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(fp.fileno(),fcntl.LOCK_UN)
        except OSError:pass
        fp.close()