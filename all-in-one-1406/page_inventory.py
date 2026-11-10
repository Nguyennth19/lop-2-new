#!/usr/bin/env python3
"""Read-only V2.4 inventory of exercise-to-PDF-page mapping.

Does not call Ollama, mutate checkpoints, store book text or upload PDF data.
Pages in the manifest are 1-based PDF indexes, NOT necessarily printed page labels.
"""
from __future__ import annotations
import argparse
import json
from collections import defaultdict,Counter
from pathlib import Path
from runner import load_manifest
from source_processor import SOURCE_LOCKS, sha256_file

def build_inventory(rows):
    pages=defaultdict(list)
    invalid=[]
    for rec in rows:
        page=str(rec.get('page','')).strip()
        key=(rec.get('track',''),str(rec.get('volume','')))
        if key not in SOURCE_LOCKS or not page.isdigit() or int(page)<1:
            invalid.append({'source_id':rec['source_id'],'reason':'INVALID_OR_MISSING_PAGE_REFERENCE'})
            continue
        pages[(key[0],key[1],int(page))].append(rec['source_id'])
    groups=sorted(pages.items(),key=lambda item:(item[0][0],item[0][1],item[0][2]))
    by_book={}
    for (track,volume,page),ids in groups:
        bucket=by_book.setdefault(f'{track}_T{volume}',{'unique_pdf_pages':0,'records_with_valid_page':0,
                 'pages_with_multiple_records':0,'potential_calls_saved_upper_bound':0})
        bucket['unique_pdf_pages']+=1
        bucket['records_with_valid_page']+=len(ids)
        if len(ids)>1:bucket['pages_with_multiple_records']+=1
        bucket['potential_calls_saved_upper_bound']+=len(ids)-1
    count=sum(map(len,pages.values()))
    return {
        'schema':'lop2_page_inventory_v2.4_a',
        'records_total':len(rows),'records_with_valid_page':count,
        'invalid_page_count':len(invalid),'invalid_pages':invalid,
        'unique_pdf_pages':len(pages),
        'pages_with_multiple_records':sum(len(ids)>1 for ids in pages.values()),
        'records_on_shared_pages':sum(len(ids) for ids in pages.values() if len(ids)>1),
        'potential_calls_saved_upper_bound':count-len(pages),
        'theoretical_call_reduction_fraction':round((count-len(pages))/count,4) if count else 0,
        'caution':'Upper bound only. A page request can be slower, ambiguous or incomplete; source-to-ID matching is NOT certified.',
        'by_book':by_book,
        'page_groups':[{'track':t,'volume':v,'pdf_page_1based':p,'source_ids':ids,'count':len(ids)}
                       for (t,v,p),ids in groups],
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input-dir',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--expected-count',type=int,default=1406)
    p.add_argument('--expected-bqas',type=int,default=21)
    p.add_argument('--verify-source-hashes',action='store_true')
    args=p.parse_args()
    rows=load_manifest(args.input_dir/'SOURCE_1406.csv',args.expected_count,args.expected_bqas)
    if args.verify_source_hashes:
        for (track,volume),(filename,expected) in SOURCE_LOCKS.items():
            fp=args.input_dir/filename
            if not fp.is_file() or sha256_file(fp)!=expected:
                raise RuntimeError(f'SOURCE_HASH_MISMATCH_OR_MISSING:{track}_T{volume}')
    result=build_inventory(rows)
    dest=args.output.resolve()
    inputs=args.input_dir.resolve()
    if dest==inputs or inputs in dest.parents:
        raise ValueError('OUTPUT_MUST_BE_OUTSIDE_PRIVATE_INPUTS')
    dest.parent.mkdir(parents=True,exist_ok=True)
    tmp=dest.with_name(dest.name+'.tmp')
    tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp.replace(dest)
    summary={k:v for k,v in result.items() if k not in ('page_groups','invalid_pages')}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('DETAIL_REPORT:',dest)
if __name__=='__main__':main()
