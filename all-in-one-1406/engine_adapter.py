"""Conservative, unapproved translation for ONE *simple* numeric-addition source slot.
No browser test or production publish implied.
"""
import re

def candidate_engine_payload(question: dict) -> dict | None:
    if question.get('figure_dependency') or question.get('slot_count')!=1:
        return None
    if question.get('question_type','').upper() not in ('MENTAL_ADD','ARITHMETIC','MENTAL_ARITHMETIC','NUMBER_FILL'):
        return None
    slot=question['student_slots'][0]
    if slot.get('answer_type')!='NUMBER':return None
    m=re.fullmatch(r'\s*(\d{1,3})\s*\+\s*(\d{1,3})\s*',slot.get('arithmetic_expression',''))
    if not m:return None
    a,b=map(int,m.groups())
    if str(a+b)!=slot.get('proposed_answer','').strip():return None
    return {
        'question_id':question['source_id'],
        'section_id':'SEC_'+question['lesson_id']+'_DRAFT',
        'question_type':'MENTAL_ADD',
        'sort_order':1,
        'qa_status':'DRAFT_UNVERIFIED',
        'payload':{'n1':a,'n2':b,'op':'+','answer':a+b},
        'release_allowed':False,
        'runtime_N9':'NOT_EXECUTED',
    }