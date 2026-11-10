"""Ollama local vision backend. No API key, no PDF upload to third parties.
Requires a user-installed Ollama multimodal model which obeys the schema.
"""
import base64
import json
import urllib.request
import urllib.error
from question_builder import ExerciseDraft,PROMPT

class OllamaExtractor:
    def __init__(self,model='qwen2.5vl:7b',endpoint='http://127.0.0.1:11434',timeout=600):
        self.model=model;self.endpoint=endpoint.rstrip('/');self.timeout=timeout
        if not (self.endpoint.startswith('http://127.0.0.1:') or self.endpoint.startswith('http://localhost:')):
            raise RuntimeError('OLLAMA_LOCALHOST_ONLY')
    def _request(self,path,payload=None):
        data=json.dumps(payload).encode() if payload is not None else None
        req=urllib.request.Request(self.endpoint+path,data=data,headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=self.timeout) as res:return json.load(res)
    def preflight(self):
        try:r=self._request('/api/tags')
        except (OSError,urllib.error.URLError) as ex:raise RuntimeError('OLLAMA_NOT_REACHABLE') from ex
        models=[x.get('name','') for x in r.get('models',[])]
        if self.model not in models:raise RuntimeError('OLLAMA_MODEL_NOT_INSTALLED:'+self.model)
        return {'model':self.model,'present':True,'local_only':True}
    def extract(self,record,png):
        content=PROMPT.format(**record)
        response=self._request('/api/chat',{'model':self.model,'stream':False,
           'messages':[{'role':'user','content':content,'images':[base64.b64encode(png).decode()]}],
           'format':ExerciseDraft.model_json_schema(),'options':{'temperature':0}})
        value=response.get('message',{}).get('content','')
        return ExerciseDraft.model_validate_json(value)