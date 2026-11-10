#!/usr/bin/env python3
"""Isolated V2.4 page-batch benchmark. NEVER writes production SQLite.

One local Ollama request for 2-4 manifest IDs on exactly one PDF page.
This is an EXPERIMENT: returned source-ID associations remain unverified drafts.
"""
from __future__ import annotations
import argparse
import base64
import json
import os
import time
import uuid
from pathlib import Path
from pydantic import BaseModel, Field
from page_inventory import build_inventory
from runner import load_manifest, classify_error
from source_processor import SourceProcessor, sha256_bytes
from local_vision import OllamaExtractor
from question_builder import ExerciseDraft, make_question
from engine_adapter import candidate_engine_payload

class PageItem(BaseModel):
    source_id: str
    extraction: ExerciseDraft

class PageBatch(BaseModel):
    items: list[PageItem]
    unresolved_source_ids: list[str] = Field(default_factory=list)

def validate_batch(response:PageBatch, expected_ids:list[str]):
    ids=[x.source_id for x in response.items]
    if len(ids)!=len(set(ids)) or any(x not in expected_ids for x in ids):
        raise ValueError('PAGE_BATCH_DUPLICATE_OR_UNEXPECTED_SOURCE_ID')
    unresolved=response.unresolved_source_ids
    if len(unresolved)!=len(set(unresolved)) or any(x not in expected_ids for x in unresolved):
        raise ValueError('PAGE_BATCH_UNRESOLVED_ID_INVALID')
    if set(ids)&set(unresolved):
        raise ValueError('PAGE_BATCH_ID_BOTH_EXTRACTED_AND_UNRESOLVED')
    if set(ids)|set(unresolved)!=set(expected_ids):
        raise ValueError('PAGE_BATCH_MISSING_SOURCE_ID')
    return True

def choose_group(rows,source_id,max_ids):
    inventory=build_inventory(rows)
    groups=inventory['page_groups']
    if source_id:
        matched=[g for g in groups if source_id in g['source_ids']]
        if len(matched)!=1:raise ValueError('SOURCE_ID_NOT_FOUND_ON_VALID_PAGE')
        group=matched[0]
    else:
        eligible=[g for g in groups if 2<=g['count']<=max_ids]
        if not eligible:raise ValueError('NO_PAGE_WITH_2_TO_MAX_IDS')
        group=eligible[0]
    if not (2<=group['count']<=max_ids):
        raise ValueError('PAGE_GROUP_NOT_IN_2_TO_MAX_IDS')
    return group

def benchmark(rows, source, model, group, timeout=600):
    ids=group['source_ids']
    records={r['source_id']:r for r in rows}
    selected=[records[sid] for sid in ids]
    first=selected[0]
    evidence=source.render(first)
    png=evidence.pop('png')
    if group['track']!=first['track'] or str(group['volume'])!=str(first['volume']) or group['pdf_page_1based']!=int(first['page']):
        raise ValueError('PAGE_GROUP_SOURCE_INCONSISTENT')
    targets=[{'source_id':r['source_id'],'lesson_id':r['lesson_id']} for r in selected]
    prompt=(
        'Conservative transcription of ONE photographed Vietnamese Grade 2 schoolbook PDF page. '
        'Database source IDs are NOT printed identifiers. For every requested source_id, map to a printed '
        'exercise ONLY when exercise number, lesson and order on this page make identification unambiguous. '
        'Never infer the exercise from the database ID alone. If ambiguous, report it in unresolved_source_ids '
        'and do NOT invent an exercise. Return each requested ID exactly once, either as items or unresolved. '
        'Separate worked examples from fillable student blanks. Preserve original Vietnamese verbatim; '
        'do not invent answers or missing words. The source image is authoritative. '
        'Mark all uncertain data, missing bboxes and pictures. Each item extraction obeys the provided JSON schema. '
        'All output is unapproved DRAFT for independent comparison, never verified truth. '
        'PDF page (1-based): '+str(group['pdf_page_1based'])+'. '
        'Requested IDs and lesson IDs: '+json.dumps(targets,ensure_ascii=False)
    )
    extractor=OllamaExtractor(model=model,timeout=timeout)
    extractor.preflight()
    started=time.monotonic()
    print('[PAGE] requesting one Ollama call for',len(ids),'records on PDF page',group['pdf_page_1based'],flush=True)
    response=extractor._request('/api/chat',{'model':model,'stream':False,
        'messages':[{'role':'user','content':prompt,'images':[base64.b64encode(png).decode('ascii')]}],
        'format':PageBatch.model_json_schema(),'options':{'temperature':0}})
    elapsed=round(time.monotonic()-started,2)
    content=response.get('message',{}).get('content','')
    parsed=PageBatch.model_validate_json(content)
    validate_batch(parsed,ids)
    results=[]
    for item in parsed.items:
        record=records[item.source_id]
        try:
            ex=item.extraction
            bbox=ex.bbox_0_to_1000
            ch=None
            if len(bbox)==4 and 0<=bbox[0]<bbox[2]<=1000 and 0<=bbox[1]<bbox[3]<=1000:
                ch=sha256_bytes(source.crop(png,bbox))
            q=make_question(record,ex,evidence,ch)
            q['engine_candidate']=candidate_engine_payload(q)
            status='DRAFT_REVIEW_REQUIRED' if q['qa']['uncertainties'] else 'DRAFT_READY'
            results.append({'source_id':item.source_id,'status':status,'slot_count':q['slot_count'],
                            'uncertainties':q['qa']['uncertainties'],
                            'candidate':q})
        except Exception as exc:
            results.append({'source_id':item.source_id,'status':'EXCEPTION',
                            'reason_code':classify_error(exc)})
    for sid in parsed.unresolved_source_ids:
        results.append({'source_id':sid,'status':'EXCEPTION',
                        'reason_code':'PAGE_BATCH_SOURCE_MAPPING_UNRESOLVED'})
    return {'schema':'lop2_v2.4_page_benchmark_1','model':model,'source_pdf':evidence['pdf_file'],
            'pdf_page_1based':evidence['page'],'image_sha256':evidence['image_sha256'],
            'source_ids':ids,'one_request_elapsed_seconds':elapsed,
            'source_to_id_independently_certified':False,'releasable':False,
            'status':'EXPERIMENTAL_NOT_PRODUCTION','results':results}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input-dir',required=True,type=Path)
    p.add_argument('--output-dir',required=True,type=Path)
    p.add_argument('--model',default='qwen2.5vl:7b')
    p.add_argument('--source-id')
    p.add_argument('--max-ids',type=int,default=3)
    p.add_argument('--timeout',type=int,default=900)
    p.add_argument('--expected-count',type=int,default=1406)
    p.add_argument('--expected-bqas',type=int,default=21)
    a=p.parse_args()
    if not (2<=a.max_ids<=4):raise ValueError('MAX_IDS_MUST_BE_2_TO_4')
    if not (120<=a.timeout<=3600):raise ValueError('TIMEOUT_OUT_OF_RANGE')
    inputs=a.input_dir.resolve();out=a.output_dir.resolve()
    if out==inputs or inputs in out.parents:raise ValueError('OUTPUT_INSIDE_PRIVATE_SOURCE')
    rows=load_manifest(inputs/'SOURCE_1406.csv',a.expected_count,a.expected_bqas)
    src=SourceProcessor(inputs);src.verify_all(True)
    group=choose_group(rows,a.source_id,a.max_ids)
    report=benchmark(rows,src,a.model,group,a.timeout)
    out.mkdir(parents=True,exist_ok=True)
    destination=out/('page_batch_'+a.model.replace(':','_')+'_'+group['track']+'_T'+group['volume']+'_p'+str(group['pdf_page_1based'])+'.json')
    temp=destination.with_name(destination.name+'.'+uuid.uuid4().hex+'.tmp')
    temp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(temp,destination)
    print(json.dumps({'model':a.model,'pdf_page':group['pdf_page_1based'],
          'source_ids':group['source_ids'],'time_seconds':report['one_request_elapsed_seconds'],
          'statuses':[{k:r.get(k) for k in ('source_id','status','slot_count','reason_code')} for r in report['results']],
          'result_file':str(destination),'release_allowed':False},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
