import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_pipeline import DemoExtractor, prepare
from runner import run_pipeline
from source_processor import SourceProcessor
from state_store import AuditStore, LocalObjects
from local_vision import OllamaExtractor
from windows_runner import export_reports

class TimeoutOnceExtractor(DemoExtractor):
    def extract(self,rec,png):
        if rec['source_id'].endswith('E01'):
            raise TimeoutError('synthetic 600-second Ollama timeout')
        return super().extract(rec,png)

class V22Tests(unittest.TestCase):
    def test_one_item_timeout_does_not_stop_next_item(self):
        with tempfile.TemporaryDirectory() as td:
            pdf,lock,_,rows=prepare(td)
            store=AuditStore(LocalObjects(Path(td)/'objects'),'timeout-campaign')
            result=run_pipeline(rows,SourceProcessor(pdf,lock),store,
                                TimeoutOnceExtractor(),max_items=2)
            self.assertEqual(result['by_status'],{'EXCEPTION':1,'DRAFT_READY':1})
            self.assertEqual(store.load(rows[0]['source_id'])['reason_code'],'VISION_REQUEST_TIMEOUT')
            self.assertEqual(store.load(rows[1]['source_id'])['status'],'DRAFT_READY')

    def test_vision_heartbeat_is_source_text_free(self):
        with tempfile.TemporaryDirectory() as td:
            extract=OllamaExtractor(timeout=10)
            draft=DemoExtractor().extract({'source_id':'synthetic'},b'abc')
            record={'source_id':'SGK_FAKE','page':'1','lesson_id':'B001'}
            with patch.dict('os.environ',{'LOP2_HEARTBEAT_FILE':str(Path(td)/'heartbeat.json')}):
                with patch.object(extract,'_request',return_value={'message':{'content':draft.model_dump_json()}}):
                    response=extract.extract(record,b'synthetic image')
            self.assertTrue(response.found)
            heartbeat=json.loads((Path(td)/'heartbeat.json').read_text())
            self.assertEqual(heartbeat['source_id'],'SGK_FAKE')
            self.assertNotIn('verbatim_prompt',heartbeat)
            self.assertNotIn('proposed_answer',heartbeat)

    def test_locked_csv_does_not_fail_export(self):
        from windows_store import WindowsAuditStore
        with tempfile.TemporaryDirectory() as td:
            store=WindowsAuditStore(Path(td)/'state','csv-lock')
            try:
                store.commit('sample','DRAFT_REVIEW_REQUIRED','DRAFT_SAVED')
                from unittest.mock import patch
                import os
                real=os.replace
                def locked_replace(src,dst):
                    if str(dst).endswith('records.csv'):raise PermissionError(5,'locked by Excel')
                    return real(src,dst)
                with patch('windows_runner.os.replace',side_effect=locked_replace):
                    export_reports(store,Path(td)/'state')
                self.assertEqual(len(list((Path(td)/'state').glob('records_snapshot_*.csv'))),1)
                self.assertTrue((Path(td)/'state'/'events.jsonl').exists())
            finally:
                store.close()
if __name__=='__main__': unittest.main()
