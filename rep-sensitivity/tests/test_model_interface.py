"""Check native tokens, fixed template dates and explicit context failures."""
from datetime import datetime
from types import SimpleNamespace, ModuleType
import sys
import unittest
from unittest.mock import patch
from rep_sensitivity.models import LocalModel


class TemplateFixture:
    def apply_chat_template(self,messages,**kwargs):
        assert kwargs['strftime_now']('%Y-%m-%d')=='2026-10-16'
        assert kwargs['tokenize'] is False
        assert kwargs['enable_thinking'] is False
        return '<BOS>'+messages[0]['content']
    def encode(self,text,add_special_tokens=True):
        return ([1] if add_special_tokens else [])+[1]+list(text[5:].encode())


class EngineFixture:
    def __init__(self):self.inputs=[]
    def generate(self,inputs,params,**kwargs):
        self.inputs.extend(inputs)
        return [SimpleNamespace(prompt_token_ids=x['prompt_token_ids'],metrics=None,
                  outputs=[SimpleNamespace(text='{}',finish_reason='stop',token_ids=[123,125])]) for x in inputs]


class NativeInterfaceTests(unittest.TestCase):
    def model(self):
        m=LocalModel.__new__(LocalModel);m.alias='qwen3'
        m.tokenizer=TemplateFixture();m.engine=EngineFixture()
        m.settings={'max_output_tokens':20,'max_model_len':100,'temperature':0.3,'top_p':0.95,'guided_decoding':False}
        return m

    def modules(self):
        v=ModuleType('vllm');v.SamplingParams=lambda **kw:kw
        s=ModuleType('vllm.sampling_params');s.GuidedDecodingParams=lambda **kw:kw
        return {'vllm':v,'vllm.sampling_params':s}

    def test_native_bos_is_not_added_twice(self):
        m=self.model();request={'prompt':'abc','seed':7,'stage':'root'}
        with patch.dict(sys.modules,self.modules()):out=m.run([request])
        self.assertEqual(m.engine.inputs,[{'prompt_token_ids':[1,97,98,99]}])
        self.assertEqual(out[0]['input_tokens'],4)
        self.assertEqual(out[0]['output_tokens'],2)
        self.assertEqual(len(out[0]['prompt_token_ids_sha256']),64)

    def test_context_limit_fails_before_inference(self):
        m=self.model()
        with patch.dict(sys.modules,self.modules()),self.assertRaisesRegex(ValueError,'No silent truncation'):
            m.run([{'prompt':'x'*90,'seed':7,'stage':'root'}])
        self.assertFalse(m.engine.inputs)


if __name__=='__main__':unittest.main()
