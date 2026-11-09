import csv
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import fitz
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runner import load_manifest, run_pipeline, InterruptedByTest
from source_processor import SourceProcessor, SourceError, sha256_file
from question_builder import ExerciseDraft, StudentSlot, make_question, BuildError
from state_store import AuditStore, LocalObjects, S3Objects
from engine_adapter import candidate_engine_payload

class DemoExtractor:
    def __init__(self):self.calls=0
    def extract(self,rec,png):
        self.calls+=1
        return ExerciseDraft(found=True,identity_confident=True,printed_exercise_marker='1',
           match_rationale='SYNTHETIC_TEST_ONLY',verbatim_prompt='Tính 2 + 3',question_type='MENTAL_ADD',
           bbox_0_to_1000=[10,10,900,900],worked_example_summary='',
           student_slots=[StudentSlot(slot_id='a',prompt_context='2 + 3',observed_blank=True,
              proposed_answer='5',answer_type='NUMBER',arithmetic_expression='2+3')],
           figures_required=False,unresolved_visuals=[],uncertainties=[])

def prepare(tmp):
    tmp=Path(tmp);pdfdir=tmp/'pdf';pdfdir.mkdir()
    doc=fitz.open();page=doc.new_page(width=400,height=400)
    page.insert_text((40,40),'Test fixture 2 + 3 = ...',fontsize=14)
    fn=pdfdir/'SGK_T1.pdf';doc.save(fn);doc.close()
    lock={('SGK','1'):('SGK_T1.pdf',sha256_file(fn))}
    manifest=tmp/'SOURCE_1406.csv'
    rows=[]
    for i in range(1,3):
        rows.append(dict(source_id=f'SGK_B001_E0{i}',lesson_id='B001',bqa='BQA-01',
                         track='SGK',volume='1',page='1',source_sha256=lock[('SGK','1')][1]))
    with manifest.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return pdfdir,lock,manifest,rows

class PipelineTests(unittest.TestCase):
    def test_manifest_schema_and_count(self):
        with tempfile.TemporaryDirectory() as td:
            _,_,manifest,rows=prepare(td)
            self.assertEqual(len(load_manifest(manifest,2,1)),2)
            with self.assertRaisesRegex(ValueError,'COUNT_MISMATCH'):
                load_manifest(manifest,1406,21)
            rows[1]['source_id']=rows[0]['source_id']
            with manifest.open('w',newline='',encoding='utf8') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
            with self.assertRaisesRegex(ValueError,'DUPLICATE'):
                load_manifest(manifest,2,1)
    def test_source_sha_and_visual_page(self):
        with tempfile.TemporaryDirectory() as td:
            pdf,lock,_,rows=prepare(td)
            s=SourceProcessor(pdf,lock)
            s.verify_all()
            rendered=s.render(rows[0]);self.assertGreater(len(rendered['png']),100)
            crop=s.crop(rendered['png'],[10,10,900,900]);self.assertGreater(len(crop),100)
            with self.assertRaisesRegex(SourceError,'ROW_SOURCE_SHA_MISMATCH'):
                s.render({**rows[0],'source_sha256':'0'*64})
    def test_killed_at_page_checkpoint_then_resume(self):
        with tempfile.TemporaryDirectory() as td:
            pdf,lock,_,rows=prepare(td)
            source=SourceProcessor(pdf,lock)
            extractor=DemoExtractor();objects=LocalObjects(Path(td)/'storage')
            store=AuditStore(objects,'interrupt-test')
            with self.assertRaises(InterruptedByTest):
                run_pipeline(rows,source,store,extractor,max_items=2,inject_interrupt_after=1)
            self.assertEqual(store.load(rows[0]['source_id'])['stage'],'PAGE_LOCKED')
            # A brand-new store instance represents another process/job.
            store2=AuditStore(LocalObjects(Path(td)/'storage'),'interrupt-test')
            result=run_pipeline(rows,SourceProcessor(pdf,lock),store2,extractor,max_items=2)
            self.assertEqual(result['by_status'],{'DRAFT_READY':2})
            self.assertEqual(result['remaining'],0)
            self.assertEqual(extractor.calls,2)
            for row in rows:
                state=store2.load(row['source_id']);self.assertEqual(state['stage'],'DRAFT_SAVED')
                draft=json.loads(objects.get(state['extra']['draft_key']))
                self.assertEqual(draft['slot_count'],1)
                self.assertFalse(draft['qa']['n10_reviewer_signed'])
                self.assertFalse(draft['release_allowed'])
                self.assertEqual(draft['engine_candidate']['question_type'],'MENTAL_ADD')
                self.assertFalse(draft['engine_candidate']['release_allowed'])
            # Running once more is idempotent.
            r=run_pipeline(rows,SourceProcessor(pdf,lock),store2,extractor)
            self.assertEqual(r['this_invocation_processed'],0)
            self.assertEqual(extractor.calls,2)
    def test_killed_after_vision_checkpoint_resume_without_extra_call(self):
        with tempfile.TemporaryDirectory() as td:
            pdf,lock,_,rows=prepare(td)
            ext=DemoExtractor();store=AuditStore(LocalObjects(Path(td)/'store'),'visionkill')
            with self.assertRaises(InterruptedByTest):
                run_pipeline(rows,SourceProcessor(pdf,lock),store,ext,inject_interrupt_after=2)
            self.assertEqual(ext.calls,1)
            result=run_pipeline(rows,SourceProcessor(pdf,lock),AuditStore(LocalObjects(Path(td)/'store'),'visionkill'),ext)
            self.assertEqual(result['by_status'],{'DRAFT_READY':2})
            self.assertEqual(ext.calls,2)  # only the 2nd row triggers an additional model call
    def test_arithmetic_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            pdf,lock,_,rows=prepare(td)
            source=SourceProcessor(pdf,lock);ev=source.render(rows[0]);ev.pop('png')
            ex=DemoExtractor().extract(rows[0],b'fixture');ex.student_slots[0].proposed_answer='9'
            with self.assertRaisesRegex(BuildError,'ARITHMETIC_ANSWER_CONFLICT'):
                make_question(rows[0],ex,ev,'a'*64)
            ex.student_slots[0].proposed_answer='5'
            q=make_question(rows[0],ex,ev,'a'*64)
            self.assertFalse(q['release_allowed'])
            self.assertFalse(q['qa']['n9_engine_browser_pass'])
            self.assertFalse(q['qa']['source_to_id_independently_verified'])

class FakeS3:
    def __init__(self):self.data={}
    def put_object(self,**kw):self.data[(kw['Bucket'],kw['Key'])]=kw['Body']
    def get_object(self,**kw):
        from botocore.exceptions import ClientError
        import io
        key=(kw['Bucket'],kw['Key'])
        if key not in self.data:raise ClientError({'Error':{'Code':'NoSuchKey','Message':'missing'}},'GetObject')
        return {'Body':io.BytesIO(self.data[key])}
    def delete_object(self,**kw):
        self.data.pop((kw['Bucket'],kw['Key']),None)
    def list_objects_v2(self,**kw):
        keys=[key for (bucket,key) in self.data if bucket==kw['Bucket'] and key.startswith(kw['Prefix'])]
        return {'Contents':[{'Key':key} for key in keys],'IsTruncated':False}

class ExternalCheckpointTests(unittest.TestCase):
    def test_new_job_reads_remote_checkpoint(self):
        fake=FakeS3()
        first=AuditStore(S3Objects('private-bucket','lop2',client=fake),'campaign1')
        first.commit('SGK_B001_K1_E01','IN_PROGRESS','PAGE_LOCKED',extra={'image_key':'ref'})
        second=AuditStore(S3Objects('private-bucket','lop2',client=fake),'campaign1')
        saved=second.load('SGK_B001_K1_E01')
        self.assertEqual(saved['stage'],'PAGE_LOCKED')
        second.commit('SGK_B001_K1_E01','DRAFT_READY','DRAFT_SAVED')
        third=AuditStore(S3Objects('private-bucket','lop2',client=fake),'campaign1')
        self.assertEqual(third.summary()['by_status']['DRAFT_READY'],1)
        self.assertEqual(len(fake.data),3)  # immutable events (2) and record pointer (1) and same record update


class CloudGateTests(unittest.TestCase):
    def test_s3_roundtrip_exercises_read_write_list_delete(self):
        from cloud_gates import connectivity_probe
        fake = FakeS3()
        obj = S3Objects('private-lop2','lop2',client=fake)
        result = connectivity_probe(obj,'test-campaign')
        self.assertEqual(result,{'remote_write':True,'remote_read':True,
                                 'remote_list':True,'remote_delete':True})
        self.assertFalse(fake.data)

    def test_canary_draft_gate_pins_model_manifest_and_hash(self):
        from cloud_gates import validate_canary, check_canary_gate
        fake = FakeS3()
        store = AuditStore(S3Objects('private-lop2','lop2',client=fake),'source-test')
        sid = 'SGK_B001_K1_E01'
        draft = {'source_id':sid,'student_slots':[{'slot_id':'a','proposed_answer':'5'}],
                 'verbatim_prompt_candidate':'Tính 2 + 3',
                 'evidence':{'pdf_sha256':'a'*64,'page_image_sha256':'b'*64,'crop_sha256':'c'*64},
                 'release_allowed':False,'slot_count':1,
                 'qa':{'extraction_method':'AI_VISION_DRAFT',
                       'n9_engine_browser_pass':False,'n10_reviewer_signed':False,
                       'n12_release_allowed':False}}
        draft_key=store.save_draft(sid,draft)
        store.commit(sid,'DRAFT_REVIEW_REQUIRED','DRAFT_SAVED',extra={'draft_key':draft_key})
        out=validate_canary(store,sid,'e'*64,'vision-model')
        self.assertTrue(out['canary_ready']); self.assertFalse(out['release_allowed'])
        check_canary_gate(store,'e'*64,'vision-model')
        with self.assertRaisesRegex(RuntimeError,'CANARY_GATE_SOURCE_OR_MODEL_MISMATCH'):
            check_canary_gate(store,'e'*64,'other-model')
        with self.assertRaisesRegex(RuntimeError,'CANARY_GATE_SOURCE_OR_MODEL_MISMATCH'):
            check_canary_gate(store,'f'*64,'vision-model')
        changed={**draft,'verbatim_prompt_candidate':'altered'}
        changed_key=store.save_draft(sid,changed)
        store.commit(sid,'DRAFT_REVIEW_REQUIRED','DRAFT_SAVED',extra={'draft_key':changed_key})
        with self.assertRaisesRegex(RuntimeError,'CANARY_GATE_DRAFT_HASH_DRIFT'):
            check_canary_gate(store,'e'*64,'vision-model')

    def test_canary_refuses_unproven_or_unreleased_payload(self):
        from cloud_gates import validate_canary
        store=AuditStore(LocalObjects(tempfile.mkdtemp()),'canary-negative')
        sid='SGK_B001_K1_E01'
        with self.assertRaisesRegex(RuntimeError,'CANARY_NO_SOURCE_BASED_DRAFT'):
            validate_canary(store,sid,'a'*64,'vision-model')
        key=store.save_draft(sid,{'source_id':sid,'student_slots':[], 'release_allowed':False})
        store.commit(sid,'DRAFT_READY','DRAFT_SAVED',extra={'draft_key':key})
        with self.assertRaisesRegex(RuntimeError,'CANARY_INSUFFICIENT_DRAFT_EVIDENCE'):
            validate_canary(store,sid,'a'*64,'vision-model')

if __name__=='__main__':unittest.main()