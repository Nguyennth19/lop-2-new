import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from page_inventory import build_inventory
from test_pipeline import prepare

class V24InventoryTests(unittest.TestCase):
    def test_two_ids_same_pdf_page_count_as_one_call_upper_bound(self):
        with tempfile.TemporaryDirectory() as t:
            _,_,_,rows=prepare(t)
            out=build_inventory(rows)
            self.assertEqual(out['records_total'],2)
            self.assertEqual(out['unique_pdf_pages'],1)
            self.assertEqual(out['pages_with_multiple_records'],1)
            self.assertEqual(out['potential_calls_saved_upper_bound'],1)
            self.assertEqual(out['theoretical_call_reduction_fraction'],0.5)
            self.assertEqual(len(out['page_groups'][0]['source_ids']),2)
    def test_missing_page_is_explicit_exception_not_automatic_mapping(self):
        with tempfile.TemporaryDirectory() as t:
            _,_,_,rows=prepare(t)
            rows[1]['page']=''
            out=build_inventory(rows)
            self.assertEqual(out['unique_pdf_pages'],1)
            self.assertEqual(out['records_with_valid_page'],1)
            self.assertEqual(out['invalid_page_count'],1)
            self.assertEqual(out['potential_calls_saved_upper_bound'],0)
            self.assertEqual(out['invalid_pages'][0]['source_id'],rows[1]['source_id'])
    def test_different_book_must_never_merge_same_page_number(self):
        with tempfile.TemporaryDirectory() as t:
            _,_,_,rows=prepare(t)
            rows[1]['volume']='2'
            out=build_inventory(rows)
            self.assertEqual(out['unique_pdf_pages'],2)
            self.assertEqual(out['potential_calls_saved_upper_bound'],0)
if __name__=='__main__':unittest.main()
