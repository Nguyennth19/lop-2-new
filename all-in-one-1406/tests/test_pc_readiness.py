import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE=Path(__file__).resolve().parents[1]/'pc_readiness.py'
spec=importlib.util.spec_from_file_location('pc_readiness',MODULE)
pm=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pm)

class ReadinessTests(unittest.TestCase):
    def test_missing_inputs_block_canary(self):
        with tempfile.TemporaryDirectory() as td:
            r=pm.check(Path(td),probe=lambda x:{'status':'READY'},mem=lambda:32,gpu=lambda:[])
            self.assertFalse(r['ready_for_canary'])
            self.assertEqual(len(r['missing_input_file_names']),5)
            self.assertFalse(r['source_sha256_verified'])
    def test_all_inputs_can_pass(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'PRIVATE_INPUTS';src.mkdir()
            for n in ('SOURCE_1406.csv','SGK_T1.pdf','SGK_T2.pdf','VBT_T1.pdf','VBT_T2.pdf'):(src/n).write_bytes(b'x')
            r=pm.check(Path(td),probe=lambda x:{'status':'READY'},mem=lambda:32,gpu=lambda:['test GPU'])
            self.assertTrue(r['ready_for_canary'])
            self.assertEqual(r['source_file_count'],5)
    def test_model_not_installed_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'PRIVATE_INPUTS';src.mkdir()
            for n in ('SOURCE_1406.csv','SGK_T1.pdf','SGK_T2.pdf','VBT_T1.pdf','VBT_T2.pdf'):(src/n).write_bytes(b'x')
            r=pm.check(Path(td),probe=lambda x:{'status':'BLOCKED','reason':'VISION_MODEL_NOT_INSTALLED'},mem=lambda:16,gpu=lambda:[])
            self.assertFalse(r['ready_for_canary'])
    def test_nonlocal_endpoint_disallowed(self):
        self.assertEqual(pm.probe_ollama(url='http://192.168.1.5:11434')['reason'],'OLLAMA_LOOPBACK_REQUIRED')

if __name__=='__main__':unittest.main()