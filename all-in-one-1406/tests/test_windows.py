import argparse
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from windows_store import WindowsAuditStore
from windows_runner import backup_files, execute
from test_pipeline import prepare, DemoExtractor
from source_processor import SourceProcessor
from runner import InterruptedByTest

class WindowsTests(unittest.TestCase):
    def test_atomic_event_and_checkpoint_and_reopen(self):
        with tempfile.TemporaryDirectory() as t:
            s=WindowsAuditStore(Path(t)/'db','winlocal')
            s.commit('SGK_B001_E01','IN_PROGRESS','PAGE_LOCKED',extra={'page':1})
            s.commit('SGK_B001_E01','DRAFT_READY','DRAFT_SAVED')
            self.assertEqual(s.integrity(),'ok')
            self.assertEqual(s.conn.execute('SELECT COUNT(*) FROM events').fetchone()[0],2)
            s.close()
            restored=WindowsAuditStore(Path(t)/'db','winlocal')
            self.assertEqual(restored.load('SGK_B001_E01')['status'],'DRAFT_READY')
            self.assertEqual(restored.summary()['tracked'],1)
            restored.close()
    def test_lock_source_conflict_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            s=WindowsAuditStore(t,'lock')
            s.lock_inputs({'manifest_sha256':'one'})
            s.lock_inputs({'manifest_sha256':'one'})
            with self.assertRaisesRegex(RuntimeError,'FINGERPRINT_CONFLICT'):
                s.lock_inputs({'manifest_sha256':'two'})
            s.close()
    def test_backup_sqlite_and_immutable_evidence_roundtrip(self):
        with tempfile.TemporaryDirectory() as t:
            s=WindowsAuditStore(Path(t)/'state','backup')
            evidence=s.evidence('a','page',b'hello world')
            s.commit('a','IN_PROGRESS','PAGE_LOCKED',extra={'image_key':evidence})
            backup_files(s,Path(t)/'backup')
            with sqlite3.connect(Path(t)/'backup'/'checkpoint.sqlite3') as c:
                self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
                self.assertEqual(c.execute('SELECT COUNT(*) FROM states').fetchone()[0],1)
            self.assertEqual((Path(t)/'backup'/'objects'/evidence).read_bytes(),b'hello world')
            self.assertEqual(len((Path(t)/'backup'/'events.jsonl').read_text().splitlines()),1)
            s.close()
    def test_real_extractor_resume_after_force_interrupt(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);pdf,lock,manifest,rows=prepare(root)
            # Windows CLI expects PDFs and manifest in SAME private root.
            import shutil
            shutil.copy2(manifest,pdf/'SOURCE_1406.csv')
            def arg():return argparse.Namespace(input_dir=pdf,state_dir=root/'state',backup_dir=root/'backup',
                status_file=root/'status.json',campaign='test-run',mode='run',model='local-test',
                ollama_url='http://127.0.0.1:11434',canary_id='SGK_B001_E01',expected_count=2,
                expected_bqas=1,max_items=2,max_seconds=100,chunk_size=2,retry_exceptions=False)
            ex=DemoExtractor()
            with self.assertRaises(InterruptedByTest):
                execute(arg(),extractor_override=ex,source_override=SourceProcessor(pdf,lock),inject_interrupt_after=2)
            self.assertEqual(ex.calls,1)
            # Backup and checkpoint survive completely new process/store instance.
            result=execute(arg(),extractor_override=ex,source_override=SourceProcessor(pdf,lock))
            self.assertEqual(result['by_status'],{'DRAFT_READY':2})
            self.assertEqual(ex.calls,2)
            execute(arg(),extractor_override=ex,source_override=SourceProcessor(pdf,lock))
            self.assertEqual(ex.calls,2)
            self.assertTrue((root/'backup'/'checkpoint.sqlite3').exists())
if __name__=='__main__': unittest.main()