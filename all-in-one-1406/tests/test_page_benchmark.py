import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from page_benchmark import PageBatch, PageItem, choose_group,validate_batch
from test_pipeline import prepare,DemoExtractor

class PageBatchTests(unittest.TestCase):
    def test_page_selected_exact_group_only(self):
        with tempfile.TemporaryDirectory() as td:
            _,_,_,rows=prepare(td)
            g=choose_group(rows,'SGK_B001_E01',max_ids=3)
            self.assertEqual(g['count'],2)
            self.assertEqual(g['pdf_page_1based'],1)
            self.assertEqual(set(g['source_ids']),{r['source_id'] for r in rows})
            with self.assertRaisesRegex(ValueError,'PAGE_GROUP_NOT_IN'):
                choose_group(rows,'SGK_B001_E01',max_ids=1)
    def test_batch_fails_closed_if_missing_or_extra_id(self):
        draft=DemoExtractor().extract({'source_id':'x'},b'png')
        good=PageBatch(items=[PageItem(source_id='a',extraction=draft)],unresolved_source_ids=['b'])
        self.assertTrue(validate_batch(good,['a','b']))
        with self.assertRaisesRegex(ValueError,'MISSING_SOURCE_ID'):
            validate_batch(PageBatch(items=[PageItem(source_id='a',extraction=draft)]),['a','b'])
        with self.assertRaisesRegex(ValueError,'DUPLICATE_OR_UNEXPECTED'):
            validate_batch(PageBatch(items=[PageItem(source_id='a',extraction=draft),
                                           PageItem(source_id='a',extraction=draft)]),['a','b'])
        with self.assertRaisesRegex(ValueError,'BOTH_EXTRACTED_AND_UNRESOLVED'):
            validate_batch(PageBatch(items=[PageItem(source_id='a',extraction=draft)],
                                      unresolved_source_ids=['a','b']),['a','b'])
if __name__=='__main__':unittest.main()
