# Bài 21 — Học liệu đối chiếu nguồn công khai (QA, 2026-10-30)

## Xác minh cấu trúc
- Toán 2, Kết nối tri thức với cuộc sống, tập 1: Bài 21 **Luyện tập chung**, SGK trang in 80–82 (được nhiều nguồn thứ cấp xác nhận).
- Vở bài tập Toán 2, tập 1: Bài 21 tiết 2 trang 78–79.
- Chưa có bản trang sách gốc được người kiểm duyệt duyệt trực quan; giữ `SECONDARY_CROSSCHECK_PENDING_PRIMARY`, không dùng `SOURCE_VERIFIED`.

## Học liệu đã ghi vào bản Sheets QA riêng
ID: `10FrW5-R_dnK-ti_u4y2y5he_Ggst6NvjS_CDsg_i6ds`.
- `MATH_B021` / 5 sections / 11 câu: LV1 SGK 6 câu (1 đặt tính 26+66; 3 tính nhẩm 41+19, 67+3, 76+14; 2 toán lời văn con nghé và viên bi); LV2 VBT 5 câu (3 tính 51+29, 72+8, 36+34; 2 toán lời văn trồng cây và mực nước).
- QA math answers: 11/11 PASS. Source refs: `SRC_B21_SGK`, `SRC_B21_VBT`.
- **Chưa phải bản sao đầy đủ Bài 21**: nhiều câu gắn hình, chọn/so sánh và các dạng cộng 2 chữ số với 1 chữ số không tương thích hoàn toàn renderer cột dọc 2 chữ số; LV3 sách tham khảo chưa có nguồn và không được giả tạo nội dung.
- `MATH_B021_QA_ONLY` giữ nguyên để thử nghiệm độc lập.

## Nguồn tham khảo thứ cấp
- SGK Bài 21: https://sachgiaokhoa.aistudybuddy.net/sach-online/lop-2/toan-2-tap-1/bai-21-luyen-tap-chung/
- SGK giải bài: https://vietjack.com/toan-2-ket-noi/bai-21-luyen-tap-chung.jsp
- VBT: https://vietjack.com/vbt-toan-2-kn/bai-21-tiet-2-trang-78-79-tap-1.jsp
- VBT đối chiếu độc lập: https://vndoc.com/giai-vo-bai-tap-toan-lop-2-bai-21-luyen-tap-chung-359335

## Những điều kiện chặn nghiệm thu
1. Đối chiếu bản gốc SGK/VBT đúng phiên bản 2026 và xác minh từng câu theo trang/hình.
2. Triển khai template mới cho các dạng bài theo hình, chọn đáp án, đọc bảng/đại lượng và số có một chữ số, không ép sang mẫu đặt tính hai chữ số.
3. Chạy `runLessonQA('MATH_B021')` trên Apps Script QA; truy cập `?lesson=MATH_B021` và test UI/đáp án.
4. Chỉ sau khi duyệt học liệu mới đổi trạng thái sang `SOURCE_VERIFIED` và cân nhắc nhập production.
