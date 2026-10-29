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
function getLessonData() {
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