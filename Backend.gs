/**
 * ============================================================================
 * KHỐI MÁY CHỦ (BACKEND) - HỆ THỐNG KIDLEARN (Code.gs)
 * ============================================================================
 */

// Nếu bạn mở Apps Script từ menu Tiện ích mở rộng -> Apps Script trong Google Sheets thì ĐỂ TRỐNG ('').
// Nếu bạn tạo file Apps Script độc lập bên ngoài, hãy dán ID của Google Sheets vào giữa 2 dấu nháy đơn:
const SPREADSHEET_ID = '1RR8mdHv6vT9Y7tqF0moy1gSUhoDpLx7GilPwqayqt9s';

function getSpreadsheetInstance() {
  // Isolated Phase-3 test deployment may override the source via Script Properties.
  // Never accept spreadsheet IDs from browser requests.
  var qaId = PropertiesService.getScriptProperties().getProperty('PHASE3_QA_SPREADSHEET_ID');
  if (qaId && /^[A-Za-z0-9_-]{20,}$/.test(qaId)) return SpreadsheetApp.openById(qaId);
  if (SPREADSHEET_ID && SPREADSHEET_ID.trim() !== '') {
    return SpreadsheetApp.openById(SPREADSHEET_ID.trim());
  }
  return SpreadsheetApp.getActiveSpreadsheet();
}

function doGet(e) {
  var template = HtmlService.createTemplateFromFile('Index');
  var requested = e && e.parameter && e.parameter.lesson;
  var lessonId = /^[A-Z0-9_]{3,64}$/.test(String(requested || '')) ? requested : 'MATH_B020';
  template.activeLessonIdJson = JSON.stringify(lessonId);
  return template.evaluate()
    .setTitle('KidLearn Lớp 2 - Hệ Thống Phiếu Bài Tập Tương Tác')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

/**
 * API: Đọc dữ liệu từ 2 Sheet 'BaiTap_PhepTinh' và 'BaiTap_LoiVan'
 */
function getLegacyLessonData() {
  try {
    var ss = getSpreadsheetInstance();
    if (!ss) {
      return { status: "fallback", message: "Sử dụng bộ dữ liệu chuẩn tích hợp." };
    }

    var sheetPhepTinh = ss.getSheetByName('BaiTap_PhepTinh');
    var sheetLoiVan = ss.getSheetByName('BaiTap_LoiVan');

    var rowsPhepTinh = [];
    var rowsLoiVan = [];

    if (sheetPhepTinh) {
      rowsPhepTinh = sheetPhepTinh.getDataRange().getValues();
      if (rowsPhepTinh.length > 0) rowsPhepTinh.shift(); // Bỏ dòng tiêu đề
    }

    if (sheetLoiVan) {
      rowsLoiVan = sheetLoiVan.getDataRange().getValues();
      if (rowsLoiVan.length > 0) rowsLoiVan.shift(); // Bỏ dòng tiêu đề
    }

    return {
      status: "success",
      rowsPhepTinh: rowsPhepTinh,
      rowsLoiVan: rowsLoiVan
    };
  } catch (error) {
    return {
      status: "error",
      message: error.toString()
    };
  }
}

/**
 * API: Lưu lịch sử làm bài của bé vào Sheet 'Lich_Su_Hoc_Tap'
 */
function saveStudentProgress(studentData) {
  try {
    var ss = getSpreadsheetInstance();
    if (!ss) return { status: "skipped" };

    var sheetLichSu = ss.getSheetByName('Lich_Su_Hoc_Tap');
    if (!sheetLichSu) {
      sheetLichSu = ss.insertSheet('Lich_Su_Hoc_Tap');
      sheetLichSu.appendRow([
        "Thời Gian", "Tên Bé", "Lớp", "Tổng Sao",
        "Thời Gian Học (giây)", "Tỷ Lệ Đúng Lần Đầu",
        "Lỗi Quên Nhớ", "Lỗi Viết Ngược"
      ]);
      sheetLichSu.getRange("A1:H1").setFontWeight("bold").setBackground("#fef08a");
    }

    sheetLichSu.appendRow([
      new Date(),
      studentData.name || "Chưa nhập",
      studentData.class || "Lớp 2",
      studentData.stars || 0,
      studentData.activeStudySeconds || 0,
      (studentData.firstTryRate || 0) + "%",
      studentData.errorForgotCarry || 0,
      studentData.errorReversed || 0
    ]);

    return { status: "success" };
  } catch (error) {
    return { status: "error", message: error.toString() };
  }
}

/**
 * PHASE 1: Structured lesson API. Old two-sheet API is retained as
 * getLegacyLessonData() so original demo can be restored from main.
 * Read-only lesson content; no changes to student progress endpoint.
 */
function getLessonData(lessonId) {
  // Backward compatibility: old client invokes getLessonData() without an ID.
  if (!lessonId) return getLegacyLessonData();
  var id = String(lessonId).trim();
  if (!/^[A-Z0-9_]{3,64}$/.test(id)) return { status: 'error', code: 'INVALID_LESSON_ID' };
  try {
    var ss = getSpreadsheetInstance();
    var required = ['LESSONS', 'SECTIONS', 'QUESTIONS', 'CONTENT', 'SOURCES', 'ASSETS', 'CURRICULUM_RULES'];
    var tables = {};
    required.forEach(function(name) {
      var sheet = ss.getSheetByName(name);
      if (!sheet) throw new Error('MISSING_SHEET: ' + name);
      var values = sheet.getDataRange().getValues();
      var headings = values.shift().map(String);
      tables[name] = values.filter(function(r) { return r.some(function(c) { return c !== ''; }); })
        .map(function(row) { var o = {}; headings.forEach(function(h, i) { o[h] = row[i]; }); return o; });
    });
    var lesson = tables.LESSONS.filter(function(x) { return x.lesson_id === id; })[0];
    if (!lesson) return { status: 'error', code: 'LESSON_NOT_FOUND', lessonId: id };
    var sections = tables.SECTIONS.filter(function(s) { return s.lesson_id === id; });
    var sectionIds = {};
    sections.forEach(function(s) { sectionIds[s.section_id] = true; });
    var questions = tables.QUESTIONS.filter(function(q) { return !!sectionIds[q.section_id]; });
    var content = tables.CONTENT.filter(function(c) { return c.lesson_id === id; });
    var errors = validateLessonRecords_(lesson, sections, questions);
    errors = errors.concat(validateCurriculumRules_(lesson, questions, tables.CURRICULUM_RULES));
    if (errors.length) return { status: 'error', code: 'VALIDATION_FAILED', errors: errors, lessonId: id };
    questions.forEach(function(q) {
      if (q.payload_json) { q.payload = JSON.parse(q.payload_json); }
      delete q.payload_json;
    });
    sections.sort(function(a,b) { return Number(a.sort_order)-Number(b.sort_order); });
    questions.sort(function(a,b) { return Number(a.sort_order)-Number(b.sort_order); });
    return {status:'success', schemaVersion:'1.0', lessonId:id, lesson:lesson,
      sections:sections, questions:questions, content:content,
      sources:tables.SOURCES, assets:tables.ASSETS};
  } catch(e) { return {status:'error', code:'READ_FAILED', message:String(e)}; }
}
function validateLessonRecords_(lesson, sections, questions) {
  var errors=[], seen={};
  function unique(id, kind) { if (!id) errors.push(kind+': MISSING_ID'); else if (seen[kind+':'+id]) errors.push(kind+': DUPLICATE_ID '+id); else seen[kind+':'+id]=true; }
  unique(lesson.lesson_id,'LESSON');
  var sectionIds={};
  sections.forEach(function(s) {
    unique(s.section_id,'SECTION'); sectionIds[s.section_id]=true;
    if (!s.exercise_type || !s.level) errors.push('SECTION '+s.section_id+': MISSING_REQUIRED');
  });
  questions.forEach(function(q) {
    unique(q.question_id,'QUESTION');
    if (!sectionIds[q.section_id]) errors.push('QUESTION '+q.question_id+': INVALID_SECTION');
    if (!q.question_type || q.answer === '' || q.answer === null || q.answer === undefined || !q.payload_json) errors.push('QUESTION '+q.question_id+': MISSING_REQUIRED');
    try {
      var p=JSON.parse(q.payload_json || '{}');
      if (Array.isArray(p.terms) && p.answer !== undefined) {
        if (p.terms.reduce(function(a,b){return a+Number(b);},0)!==Number(p.answer)) errors.push('QUESTION '+q.question_id+': WRONG_THREE_TERM_ANSWER');
      } else if (p.n1 !== undefined && p.n2 !== undefined && p.op && p.answer !== undefined) {
        var a=Number(p.n1), b=Number(p.n2), expected=p.op==='+'?a+b:p.op==='-'?a-b:NaN;
        if (!Number.isFinite(expected) || expected!==Number(p.answer)) errors.push('QUESTION '+q.question_id+': WRONG_ANSWER');
      }
      // Structured interaction payloads must be coherent; no implicit math scope change.
      if (lesson.lesson_id==='MATH_B021' &&
        ['CHOICE','MATCH_PAIRS','DRAG_TAP'].indexOf(q.question_type)!==-1) {
        if (!p.prompt || typeof p.prompt!=='string')errors.push('QUESTION '+q.question_id+': INTERACTIVE_PROMPT_REQUIRED');
        if(q.question_type==='MATCH_PAIRS'){
          if(!Array.isArray(p.options)||p.options.length<2||!Array.isArray(p.pairs)||p.pairs.length<2 ||
            p.pairs.some(function(pair){return typeof pair.left!=='string' ||
              !Number.isInteger(pair.rightIndex)||pair.rightIndex<0||pair.rightIndex>=p.options.length;}))
            errors.push('QUESTION '+q.question_id+': INVALID_MATCH_PAYLOAD');
        }else{
          var opts=q.question_type==='CHOICE'?p.options:p.tokens;
          if(!Array.isArray(opts)||opts.length<2||!Number.isInteger(p.correctIndex) ||
            p.correctIndex<0||p.correctIndex>=opts.length)
            errors.push('QUESTION '+q.question_id+': INVALID_CHOICE_PAYLOAD');
        }
      }
      // B021: review of carrying addition in 100; unlike B020, a one-digit addend is allowed.
      if (lesson.lesson_id === 'MATH_B021') {
        if (['VERTICAL_ADD','MENTAL_ADD','WORD_PROBLEM'].indexOf(q.question_type) !== -1) {
          var n21a=Number(p.n1),n21b=Number(p.n2);
          if (p.op !== '+' || Array.isArray(p.terms) || !Number.isInteger(n21a) ||
              !Number.isInteger(n21b) || n21a < 1 || n21b < 1 ||
              n21a > 99 || n21b > 99 || Math.max(n21a,n21b) < 10 ||
              n21a % 10 + n21b % 10 < 10 || n21a + n21b > 100 ||
              n21a + n21b !== Number(q.answer)) {
            errors.push('QUESTION '+q.question_id+': B021_CURRICULUM_FORMAT_MISMATCH');
          }
        } else if (['MISSING_DIGIT','CHOICE','MATCH_PAIRS','DRAG_TAP'].indexOf(q.question_type) === -1) {
          errors.push('QUESTION '+q.question_id+': B021_UNSUPPORTED_FORMAT');
        }
      }
      // B020 curriculum gate: exactly two two-digit addends with carrying, result <= 99.
      if (lesson.lesson_id === 'MATH_B020') {
        var n1, n2;
        if (p.rows && p.rows.length === 3) {
          var numberFromRow = function(row) { return Number(row.slice(0,2).map(function(c){return typeof c==='object'?c.ans:c;}).join('')); };
          n1 = numberFromRow(p.rows[0]); n2 = numberFromRow(p.rows[1]);
        } else {
          n1=Number(p.n1); n2=Number(p.n2);
        }
        var isTwoDigit = function(n){return Number.isInteger(n) && n >= 10 && n <= 99;};
        if (p.op !== '+' || Array.isArray(p.terms) || !isTwoDigit(n1) || !isTwoDigit(n2) ||
            n1 % 10 + n2 % 10 < 10 || n1 + n2 > 99 ||
            n1 + n2 !== Number(q.answer)) {
          errors.push('QUESTION '+q.question_id+': B020_CURRICULUM_FORMAT_MISMATCH');
        }
      }
      if (p.rows) {
        var v=function(row){return Number(row.slice(0,2).map(function(c){return typeof c==='object'?c.ans:c;}).join(''));};
        if (v(p.rows[0])+v(p.rows[1])!==Number(p.sum)) errors.push('QUESTION '+q.question_id+': WRONG_PUZZLE_ANSWER');
      }
    } catch(e) { errors.push('QUESTION '+q.question_id+': INVALID_JSON'); }
  });
  return errors;
}

/** Administrator QA: run from Apps Script editor; returns report, never modifies data. */
function runLessonQA(lessonId) {
  var result=getLessonData(lessonId || 'MATH_B020');
  return {lessonId:lessonId || 'MATH_B020',status:result.status,code:result.code || '',
    sections:result.sections?result.sections.length:0,
    questions:result.questions?result.questions.length:0,
    errors:result.errors || [], checkedAt:new Date().toISOString()};
}

/** Phase 3: available lesson metadata only; does not imply pedagogical approval. */
function getLessonCatalog() {
  try {
    var sheet = getSpreadsheetInstance().getSheetByName('LESSONS');
    if (!sheet) return {status:'error',code:'MISSING_SHEET'};
    var rows = sheet.getDataRange().getValues();
    var headings = rows.shift().map(String);
    var allowed = ['lesson_id','title','subject','status','qa_status'];
    var lessons = rows.filter(function(r){return r.some(function(v){return v!=='';});})
      .map(function(r){var o={};headings.forEach(function(h,i){if(allowed.indexOf(h)!==-1)o[h]=r[i];});return o;})
      .filter(function(o){return !!o.lesson_id;});
    return {status:'success',lessons:lessons};
  } catch(e) {return {status:'error',code:'CATALOG_READ_FAILED',message:String(e)};}
}

/** Server-only deep QA: no changes to data, student history, or stars. */
function testPhase3CurriculumQA() {
  var report={checkedAt:new Date().toISOString(),lessons:[],status:'PASS'};
  ['MATH_B020','MATH_B021'].forEach(function(id){
    var a=getLessonData(id);
    var row={lessonId:id,status:a.status,sections:a.sections?a.sections.length:0,
      questions:a.questions?a.questions.length:0,errors:a.errors||[],code:a.code||''};
    if(a.status!=='success')report.status='FAIL';
    report.lessons.push(row);
  });
  console.log('PHASE3_CURRICULUM_QA '+JSON.stringify(report));
  return report;
}
function testPhase3NegativeCases() {
  var cases=[
    {id:'B021_INVALID_MINUS',type:'MENTAL_ADD',p:{n1:41,n2:19,op:'-',answer:22},ans:22},
    {id:'B021_INVALID_THREE',type:'MENTAL_ADD',p:{n1:41,n2:19,op:'+',terms:[41,19,5],answer:65},ans:65},
    {id:'B021_INVALID_NO_CARRY',type:'MENTAL_ADD',p:{n1:41,n2:12,op:'+',answer:53},ans:53},
    {id:'B021_VALID_ONE_DIGIT',type:'MENTAL_ADD',p:{n1:67,n2:3,op:'+',answer:70},ans:70}
  ];
  var report=cases.map(function(t){
    var q={question_id:t.id,section_id:'QA_S',question_type:t.type,
      answer:t.ans,payload_json:JSON.stringify(t.p)};
    var issues=validateLessonRecords_({lesson_id:'MATH_B021'},
      [{section_id:'QA_S',exercise_type:'MENTAL_ADD',level:1}], [q]);
    var shouldPass=t.id==='B021_VALID_ONE_DIGIT';
    return {caseId:t.id,passed:shouldPass?issues.length===0:
      issues.some(function(x){return x.indexOf('B021_CURRICULUM_FORMAT_MISMATCH')!==-1;}),issues:issues};
  });
  console.log('PHASE3_NEGATIVE_CASES '+JSON.stringify(report));
  return {status:report.every(function(x){return x.passed;})?'PASS':'FAIL',cases:report};
}

/** Sheet-driven rule gate. Rule changes in CURRICULUM_RULES become effective on next API call. */
function validateCurriculumRules_(lesson, questions, allRules) {
  var errors=[],rules=(allRules||[]).filter(function(r){return r.lesson_id===lesson.lesson_id&&r.status==='ACTIVE';});
  if (!rules.length){errors.push('CURRICULUM_RULES_MISSING: '+lesson.lesson_id);return errors;}
  questions.forEach(function(q){
    var rule=rules.filter(function(r){return String(r.question_type).split(',').indexOf(q.question_type)!==-1;})[0];
    if (!rule){errors.push(q.question_id+': TYPE_NOT_APPROVED_BY_RULES');return;}
    var p;
    try{p=JSON.parse(q.payload_json);}catch(e){errors.push(q.question_id+': INVALID_RULES_PAYLOAD');return;}
    if (rule.allowed_skills && String(rule.allowed_skills).split(',').indexOf(p.skill)===-1)
      errors.push(q.question_id+': SKILL_OUTSIDE_LESSON');
    if(rule.operation){
      var n1,n2;
      if(p.rows){
        var asNum=function(row){return Number(row.slice(0,2).map(function(c){return typeof c==='object'?c.ans:c;}).join(''));};
        n1=asNum(p.rows[0]);n2=asNum(p.rows[1]);
      }else{n1=Number(p.n1);n2=Number(p.n2);}
      var minD=Number(rule.min_digits),maxD=Number(rule.max_digits);
      var validDigit=function(n){return Number.isInteger(n)&&n>=Math.pow(10,minD-1)&&n<Math.pow(10,maxD);};
      var expected=Number(p.rows?p.sum:p.answer);
      if(p.op!==rule.operation||Array.isArray(p.terms)||Number(rule.min_addends)!==2||
        Number(rule.max_addends)!==2||!validDigit(n1)||!validDigit(n2)||
        (lesson.lesson_id==='MATH_B021'&&Math.max(n1,n2)<10)||
        (String(rule.carry_required).toUpperCase()==='TRUE'&&n1%10+n2%10<10)||
        n1+n2>Number(rule.max_result)||n1+n2!==expected||expected!==Number(q.answer)){
        errors.push(q.question_id+': CURRICULUM_RULE_VIOLATION');
      }
    }
  });
  return errors;
}
function testCurriculumRulesTable() {
  var ss=getSpreadsheetInstance(),sheet=ss.getSheetByName('CURRICULUM_RULES');
  if(!sheet)throw Error('Missing CURRICULUM_RULES sheet');
  var cells=sheet.getDataRange().getValues(),header=cells.shift().map(String);
  var rules=cells.filter(function(r){return r[0];}).map(function(r){var o={};header.forEach(function(h,i){o[h]=r[i]});return o;});
  var a=['MATH_B020','MATH_B021'].map(function(id){
    var api=getLessonData(id);
    return {id:id,status:api.status,questions:(api.questions||[]).length,errors:api.errors||[]};
  });
  var report={status:a.every(function(x){return x.status==='success';})?'PASS':'FAIL',rules:rules.length,lessons:a};
  console.log('CURRICULUM_RULES_TABLE_QA '+JSON.stringify(report));return report;
}

/** Opt-in QA-only installable trigger. Never installs against production Sheets. */
function installCurriculumAuditTriggerQA() {
  var id=PropertiesService.getScriptProperties().getProperty('PHASE3_QA_SPREADSHEET_ID');
  if(id!=='10FrW5-R_dnK-ti_u4y2y5he_Ggst6NvjS_CDsg_i6ds')
    throw Error('QA_ONLY: Wrong or missing isolated spreadsheet ID');
  var exists=ScriptApp.getProjectTriggers().some(function(t){
    return t.getHandlerFunction()==='curriculumAuditOnEdit';
  });
  if(!exists)ScriptApp.newTrigger('curriculumAuditOnEdit').forSpreadsheet(id).onEdit().create();
  console.log('QA CURRICULUM AUDIT TRIGGER INSTALLED or ALREADY PRESENT');
  return {status:'PASS',alreadyInstalled:exists};
}
/** Every edited row remains editable; API will reject invalid records, audit shows reasons. */
function curriculumAuditOnEdit(e) {
  if(!e || !e.range || !e.source)return;
  var qaId=PropertiesService.getScriptProperties().getProperty('PHASE3_QA_SPREADSHEET_ID');
  if(qaId!=='10FrW5-R_dnK-ti_u4y2y5he_Ggst6NvjS_CDsg_i6ds' || e.source.getId()!==qaId)return;
  var name=e.range.getSheet().getName();
  if(['QUESTIONS','CURRICULUM_RULES','SECTIONS'].indexOf(name)===-1)return;
  var lock=LockService.getScriptLock();
  if(!lock.tryLock(5000))return;
  try{runCurriculumAuditQA();}finally{lock.releaseLock();}
}
function runCurriculumAuditQA() {
  var qaId=PropertiesService.getScriptProperties().getProperty('PHASE3_QA_SPREADSHEET_ID');
  if(qaId!=='10FrW5-R_dnK-ti_u4y2y5he_Ggst6NvjS_CDsg_i6ds')
    throw Error('QA_ONLY: wrong spreadsheet');
  var ss=SpreadsheetApp.openById(qaId),sheet=ss.getSheetByName('CURRICULUM_AUDIT');
  if(!sheet)throw Error('Missing CURRICULUM_AUDIT sheet');
  var now=new Date().toISOString(),ids=['MATH_B020','MATH_B021'],rows=[];
  ids.forEach(function(id){
    var api=getLessonData(id),errors=api.errors||[];
    rows.push([now,id,api.status==='success'?'PASS':'FAIL',
      api.sections?api.sections.length:0,api.questions?api.questions.length:0,
      api.code||'',errors.join(' | '),'This is a lesson-scope audit; see API for per-question errors']);
  });
  sheet.getRange(1,1,1,8).setValues([['checked_at','lesson_id','status','section_count',
    'question_count','api_code','errors','note']]);
  sheet.getRange(2,1,rows.length,8).setValues(rows);
  sheet.getRange(1,1,1,8).setFontWeight('bold');
  var status=rows.every(function(r){return r[2]==='PASS';})?'PASS':'FAIL';
  console.log('CURRICULUM_AUDIT_QA '+JSON.stringify({status:status,lessons:rows}));
  return {status:status,lessons:rows};
}

function testInteractivePayloadNegativeQA() {
  var sections=[{section_id:'S',exercise_type:'CHOICE',level:1}],base=function(id,type,p,ans){
    return {question_id:id,section_id:'S',question_type:type,answer:ans,payload_json:JSON.stringify(p)};
  };
  var cases=[
    {id:'VALID_CHOICE',q:base('VALID_CHOICE','CHOICE',{prompt:'Chọn đường bay',options:['Ong','Chuồn chuồn'],correctIndex:1,skill:'COMPARE_ADDITION_LENGTH'},1),valid:true},
    {id:'INVALID_CHOICE_INDEX',q:base('INVALID_CHOICE_INDEX','CHOICE',{prompt:'Chọn',options:['A','B'],correctIndex:5,skill:'COMPARE_ADDITION_LENGTH'},5),valid:false},
    {id:'INVALID_MATCH_PAIR',q:base('INVALID_MATCH_PAIR','MATCH_PAIRS',{prompt:'Nối',options:['51','90'],pairs:[{left:'45+6',rightIndex:3},{left:'81+9',rightIndex:1}],skill:'PAIR_ADDITION'},0),valid:false},
    {id:'INVALID_DRAG_TOKENS',q:base('INVALID_DRAG_TOKENS','DRAG_TAP',{prompt:'Kéo',tokens:['61'],correctIndex:0,skill:'DRAG_ADDITION_LENGTH'},0),valid:false}
  ];
  var result=cases.map(function(t){
    var issues=validateLessonRecords_({lesson_id:'MATH_B021'},sections,[t.q]);
    return {caseId:t.id,pass:t.valid?issues.length===0:issues.length>0,issues:issues};
  });
  var report={status:result.every(function(x){return x.pass;})?'PASS':'FAIL',cases:result};
  console.log('INTERACTIVE_NEGATIVE_QA '+JSON.stringify(report));return report;
}
