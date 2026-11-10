import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from question_builder import ExerciseDraft, StudentSlot, make_question
from runner import run_pipeline
from state_store import AuditStore,LocalObjects
from source_processor import SourceProcessor
from test_pipeline import DemoExtractor,prepare

class InvalidBboxExtractor(DemoExtractor):
    def extract(self,rec,png):
        ex=super().extract(rec,png)
        ex.bbox_0_to_1000=[0,0,0,0]
        return ex

class BboxRecoveryTests(unittest.TestCase):
    def test_bbox_invalid_draft_requires_review_without_fabricated_crop(self):
        with tempfile.TemporaryDirectory() as td:
            pdf,lock,manifest,rows=prepare(td)
            source=SourceProcessor(pdf,lock)
            evidence=source.render(rows[0]);evidence.pop('png')
            ex=InvalidBboxExtractor().extract(rows[0],b'test')
            q=make_question(rows[0],ex,evidence,None)
            self.assertIsNone(q['source_crop_bbox'])
            self.assertIsNone(q['source_crop_sha256'])
            self.assertIn('SOURCE_BBOX_INVALID_REQUIRES_REVIEW',q['qa']['uncertainties'])
            self.assertFalse(q['release_allowed'])
            self.assertFalse(q['qa']['n9_engine_browser_pass'])

    def test_retry_existing_bbox_exception_reuses_vision(self):
        with tempfile.TemporaryDirectory() as td:
            pdf,lock,manifest,rows=prepare(td)
            source=SourceProcessor(pdf,lock)
            ext=InvalidBboxExtractor()
            objects=LocalObjects(Path(td)/'store')
            store=AuditStore(objects,'bbox-recovery')
            # First simulate the previous buggy validator rejecting the vision bbox.
            from unittest.mock import patch
            from question_builder import BuildError
            with patch('runner.make_question', side_effect=BuildError('BBOX_INVALID')):
                first=run_pipeline(rows[:1],source,store,ext,max_items=1)
            self.assertEqual(first['by_status']['EXCEPTION'],1)
            self.assertEqual(ext.calls,1)
            # A new process using the repaired builder recovers the immutable draft.
            reopened=AuditStore(LocalObjects(Path(td)/'store'),'bbox-recovery')
            second=run_pipeline(rows[:1],SourceProcessor(pdf,lock),reopened,ext,
                                max_items=1,retry_exceptions=True)
            self.assertEqual(ext.calls,1)
            self.assertEqual(second['by_status']['DRAFT_REVIEW_REQUIRED'],1)
            st=reopened.load(rows[0]['source_id'])
            doc=json.loads(objects.get(st['extra']['draft_key']))
            self.assertIn('SOURCE_BBOX_INVALID_REQUIRES_REVIEW',doc['qa']['uncertainties'])
            self.assertFalse(doc['release_allowed'])

if __name__=='__main__':unittest.main()
