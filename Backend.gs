/**
 * ============================================================================
 * KHỐI MÁY CHỦ (BACKEND) - HỆ THỐNG KIDLEARN (Code.gs)
 * ============================================================================
 */

// Nếu bạn mở Apps Script từ menu Tiện ích mở rộng -> Apps Script trong Google Sheets thì ĐỂ TRỐNG ('').
// Nếu bạn tạo file Apps Script độc lập bên ngoài, hãy dán ID của Google Sheets vào giữa 2 dấu nháy đơn:
const SPREADSHEET_ID = '1RR8mdHv6vT9Y7tqF0moy1gSUhoDpLx7GilPwqayqt9s';

function getSpreadsheetInstance() {
  if (SPREADSHEET_ID && SPREADSHEET_ID.trim() !== '') {
    return SpreadsheetApp.openById(SPREADSHEET_ID.trim());
  }
  return SpreadsheetApp.getActiveSpreadsheet();
}

function doGet(e) {
  var template = HtmlService.createTemplateFromFile('Index');
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
    var required = ['LESSONS', 'SECTIONS', 'QUESTIONS', 'CONTENT', 'SOURCES', 'ASSETS'];
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
