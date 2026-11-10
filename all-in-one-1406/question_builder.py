"""Structured visual-source draft extraction and conservative question validation.

A machine-generated draft is never source certified, N9 passed, N10 signed or released.
"""
from __future__ import annotations
import base64
import json
import re
from typing import Literal
from pydantic import BaseModel, Field

class StudentSlot(BaseModel):
    slot_id: str
    prompt_context: str
    observed_blank: bool
    proposed_answer: str
    answer_type: Literal["NUMBER", "TEXT", "CHOICE", "MATCH", "DRAW", "UNKNOWN"]
    arithmetic_expression: str  # empty if not independently calculable

class ExerciseDraft(BaseModel):
    found: bool
    identity_confident: bool
    printed_exercise_marker: str
    match_rationale: str
    verbatim_prompt: str
    question_type: str
    bbox_0_to_1000: list[int]
    worked_example_summary: str
    student_slots: list[StudentSlot]
    figures_required: bool
    unresolved_visuals: list[str]
    uncertainties: list[str]

PROMPT = """You are a conservative visual transcriber of a Vietnamese grade-2 math schoolbook page.
The page image is authoritative; previous third-party question data is NOT an authoritative source.
The given source_id is a database identifier, not a printed book identifier. Locate the exact exercise ONLY
if its section and exercise order can be identified unambiguously from the printed page. If ambiguous return
found=false and identity_confident=false. Never invent missing words, student blanks, labels, figures or answers.
Preserve verbatim Vietnamese prompt as printed. Extract EVERY visible student-answer slot, and distinguish
worked examples from student work. A pre-filled example is NEVER a student slot. Give bbox for the specific
exercise in page-normalized coordinates 0..1000. Put uncertain facts in uncertainties.
Proposed answers are guesses to be checked, NOT canonical truth. Provide arithmetic_expression ONLY for
an unambiguous elementary arithmetic operation present in the source. Avoid reading non-visible content.
The source_id target is: {source_id}. Page is {page}. Lesson is {lesson_id}.
"""

class VisionExtractor:
    def __init__(self, client=None, model="gpt-4.1", enabled=True):
        self.model = model
        self.enabled = enabled
        self.client = client

    def extract(self, record: dict, png: bytes) -> ExerciseDraft:
        if not self.enabled: raise RuntimeError("VISION_DISABLED")
        if self.client is None:
            from openai import OpenAI
            self.client = OpenAI(timeout=90.0, max_retries=2)
        img = base64.b64encode(png).decode("ascii")
        response = self.client.responses.parse(
            model=self.model,
            store=False,
            input=[{"role":"user","content":[
                {"type":"input_text", "text":PROMPT.format(**record)},
                {"type":"input_image", "detail":"high", "image_url":"data:image/png;base64,"+img}
            ]}],
            text_format=ExerciseDraft,
            max_output_tokens=2200,
        )
        if response.output_parsed is None: raise RuntimeError("VISION_RESPONSE_UNPARSEABLE")
        return response.output_parsed

class BuildError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)

def calculate_basic(expr: str) -> str|None:
    # Verify the model's candidate answer only when the expression is simple and source asserted it.
    m=re.fullmatch(r"\s*(\d{1,5})\s*([+\-×*:÷])\s*(\d{1,5})\s*",expr or "")
    if not m: return None
    a,op,b=int(m[1]),m[2],int(m[3])
    if op=="+": return str(a+b)
    if op=="-": return str(a-b)
    if op in ("×","*"): return str(a*b)
    if op in (":","÷") and b and a%b==0: return str(a//b)
    return None

def make_question(record:dict, extraction:ExerciseDraft, evidence:dict, crop_hash:str|None)->dict:
    if not extraction.found: raise BuildError("EXERCISE_NOT_FOUND_ON_PAGE")
    if not extraction.identity_confident: raise BuildError("SOURCE_TO_EXERCISE_MAPPING_AMBIGUOUS")
    box=extraction.bbox_0_to_1000
    # A model's malformed crop rectangle must NOT become fabricated coordinates.
    # Preserve the unapproved draft without a crop, and flag it for review.
    bbox_valid = len(box)==4 and (0<=box[0]<box[2]<=1000 and 0<=box[1]<box[3]<=1000)
    if not extraction.verbatim_prompt.strip(): raise BuildError("PROMPT_NOT_READABLE")
    if not extraction.student_slots: raise BuildError("NO_STUDENT_SLOTS_LOCATED")
    ids=[s.slot_id for s in extraction.student_slots]
    if len(ids)!=len(set(ids)) or any(not x.strip() for x in ids): raise BuildError("SLOT_IDS_INVALID_OR_DUPLICATE")
    checks=[]
    qa_flags=list(extraction.uncertainties)+list(extraction.unresolved_visuals)
    ready_answers=True
    for slot in extraction.student_slots:
        if not slot.observed_blank: raise BuildError("SLOT_NOT_SHOWN_IN_SOURCE")
        answer=slot.proposed_answer.strip()
        placeholders={"", "?", "？", "??", "...", "…", "unknown", "n/a", "none", "null", "chưa rõ", "không rõ"}
        if answer.lower() in placeholders:
            qa_flags.append("SLOT_ANSWER_UNRESOLVED:"+slot.slot_id)
            ready_answers=False
        if slot.answer_type=="NUMBER" and answer.lower() not in placeholders:
            if not re.fullmatch(r"-?\\d+(?:[.,]\\d+)?",answer):
                qa_flags.append("NUMBER_ANSWER_INVALID:"+slot.slot_id)
                ready_answers=False
        if slot.arithmetic_expression:
            computed=calculate_basic(slot.arithmetic_expression)
            if computed is None:
                qa_flags.append("ARITHMETIC_EXPRESSION_UNVERIFIABLE:"+slot.slot_id)
                ready_answers=False
            elif slot.answer_type=="NUMBER" and answer.lower() not in placeholders and computed!=answer:
                raise BuildError("ARITHMETIC_ANSWER_CONFLICT")
            checks.append({"slot_id":slot.slot_id,"expression":slot.arithmetic_expression,"independent_result":computed})
    return {
       "source_id":record["source_id"],"lesson_id":record["lesson_id"],"bqa":record["bqa"],
       "track":record["track"],"volume":record["volume"],"source_pdf_page":evidence["page"],
       "question_type":extraction.question_type,"verbatim_prompt_candidate":extraction.verbatim_prompt,
       "printed_exercise_marker":extraction.printed_exercise_marker,
       "student_slots":[s.model_dump() for s in extraction.student_slots],
       "slot_count":len(extraction.student_slots),"worked_example_summary":extraction.worked_example_summary,
       "figure_dependency":extraction.figures_required,
       "source_crop_bbox":box if bbox_valid else None,"source_crop_sha256":crop_hash if bbox_valid else None,
       "evidence":{"pdf_sha256":evidence["pdf_sha256"],"page_image_sha256":evidence["image_sha256"],
                   "crop_sha256":crop_hash,"source_file":evidence["pdf_file"]},
       "mapping_rationale":extraction.match_rationale,
       "qa":{"extraction_method":"AI_VISION_DRAFT","source_text_independently_certified":False,
             "all_slots_independently_certified":False,"source_to_id_independently_verified":False,
             "math_cross_checks":checks,"answer_key_ready":ready_answers,"uncertainties":qa_flags+([] if bbox_valid else ["SOURCE_BBOX_INVALID_REQUIRES_REVIEW"]),
             "n9_engine_browser_pass":False,"n10_reviewer_signed":False,"n12_release_allowed":False},
       "release_allowed":False,
    }