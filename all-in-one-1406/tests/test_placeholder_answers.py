import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from question_builder import ExerciseDraft, StudentSlot, make_question
from source_processor import SourceProcessor
from test_pipeline import DemoExtractor, prepare

class PlaceholderTests(unittest.TestCase):
    def test_question_mark_answers_are_not_answer_key_ready(self):
        with tempfile.TemporaryDirectory() as td:
            pdf,locks,_,rows=prepare(td)
            ev=SourceProcessor(pdf,locks).render(rows[0]);ev.pop('png')
            x=DemoExtractor().extract(rows[0],b'x')
            x.bbox_0_to_1000=[0,0,0,0]
            x.student_slots=[StudentSlot(slot_id=str(i),prompt_context='tens ones',
                observed_blank=True,proposed_answer='?',answer_type='NUMBER',
                arithmetic_expression='0') for i in range(1,5)]
            q=make_question(rows[0],x,ev,None)
            self.assertFalse(q['qa']['answer_key_ready'])
            self.assertEqual(sum(s.startswith('SLOT_ANSWER_UNRESOLVED:') for s in q['qa']['uncertainties']),4)
            self.assertEqual(sum(s.startswith('ARITHMETIC_EXPRESSION_UNVERIFIABLE:') for s in q['qa']['uncertainties']),4)
            self.assertIsNone(q['source_crop_bbox'])
            self.assertFalse(q['release_allowed'])
    def test_numeric_answer_can_pass_candidate_validation(self):
        with tempfile.TemporaryDirectory() as td:
            pdf,locks,_,rows=prepare(td)
            ev=SourceProcessor(pdf,locks).render(rows[0]);ev.pop('png')
            x=DemoExtractor().extract(rows[0],b'x')
            q=make_question(rows[0],x,ev,'b'*64)
            self.assertTrue(q['qa']['answer_key_ready'])

if __name__=='__main__':unittest.main()
