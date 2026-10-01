# Research Gap — nghiên cứu tạm, CHƯA đưa vào Copy.final.docx

Ghi lại kết quả tìm nguồn thật cho mục "Công trình nghiên cứu liên quan" + "Research Gap" (phản
hồi mục 5, 6 của giảng viên hướng dẫn). Đã xác minh chéo qua nhiều nguồn độc lập (Semantic Scholar,
ResearchGate, IEEE/ACM, arXiv - arXiv fetch trực tiếp được, xác nhận đúng tiêu đề/tác giả/abstract).
Đây là mục MỚI, ngoài phạm vi Việc 1-6 đã làm trước đó - **để đó tạm thời, chưa viết vào file Word
cho tới khi người dùng duyệt lại và đồng ý.**

## 3 nguồn đã xác minh

### A. Thử kính ảo / AR try-on

**An Augmented Reality Virtual Glasses Try-On System**
Tác giả: Pedro Azevedo, Thiago Oliveira Dos Santos, Edilson De Aguiar
Nguồn: IEEE, XVIII Symposium on Virtual and Augmented Reality (SVR), Gramado, Brazil
Năm: 2016
Link: https://ieeexplore.ieee.org/document/7517246/

### B. Phân loại cảm xúc tiếng Việt

**A Systematic Literature Review on Vietnamese Aspect-based Sentiment Analysis**
Tác giả: Van Thin D., Hao D.N., Nguyen N.L.-T.
Nguồn: ACM Transactions on Asian and Low-Resource Language Information Processing (TALLIP), vol. 22, số 8
Năm: 2023
Link: https://dl.acm.org/doi/10.1145/3610226

### C. Bình luận thương mại điện tử tiếng Việt (miền dữ liệu liên quan)

**Vietnamese Complaint Detection on E-Commerce Websites**
Tác giả: Nhung Thi-Hong Nguyen, Phuong Phan-Dieu Ha, Luan Thanh Nguyen, Kiet Van Nguyen, Ngan Luu-Thuy Nguyen
Nguồn: arXiv:2104.11969
Năm: 2021
Link: https://arxiv.org/abs/2104.11969

## Khoảng trống nghiên cứu (Research Gap) ứng với từng nguồn

- **A** — hệ thống thử kính AR tương tự nhưng dùng camera/thiết bị AR chuyên dụng, xử lý
  offline/desktop, không tích hợp vào một website thương mại điện tử thật. Khoảng trống: đồ án làm
  thử kính thời gian thực ngay trên trình duyệt web qua WebSocket, không cần cài app hay thiết bị
  AR riêng, tích hợp thẳng vào luồng mua hàng.
- **B** — tổng quan hệ thống hoá cho thấy phần lớn nghiên cứu ABSA tiếng Việt đi theo hướng mô hình
  ngày càng phức tạp (deep learning, hybrid). Khoảng trống: đồ án chọn hướng ngược lại, mô hình học
  máy truyền thống (TF-IDF + Logistic Regression) nhẹ, dễ giải thích, nhưng tích hợp THẬT vào luồng
  gửi đánh giá của một website đang chạy, thay vì chỉ dừng ở thí nghiệm offline trên notebook.
- **C** — cùng miền dữ liệu (bình luận TMĐT tiếng Việt) nhưng giải quyết bài toán khác (phát hiện
  khiếu nại, không phải phân loại cảm xúc 3 lớp). Dùng để lập luận: nghiên cứu về bình luận tiếng
  Việt trong TMĐT đang phát triển nhưng mỗi hướng giải quyết một bài toán riêng lẻ, chưa thấy hệ
  thống nào kết hợp cả thử đồ ảo lẫn phân tích cảm xúc trong cùng một website bán hàng thật.

## Draft nội dung (chưa áp dụng) nếu sau này đồng ý đưa vào báo cáo

Có thể thêm một mục mới trong Chương 1 (vd 1.1 mở rộng hoặc mục 1.1.1 mới) tên "Công trình nghiên
cứu liên quan và khoảng trống nghiên cứu", nội dung phác thảo:

> Về thử kính ảo, Azevedo, Oliveira Dos Santos và De Aguiar (2016) [nguồn A] xây dựng hệ thống AR
> tự động khớp kính 3D lên khuôn mặt qua thiết bị và camera chuyên dụng, đạt kết quả tốt về độ
> chính xác định vị nhưng chưa hướng tới tích hợp vào một nền tảng bán hàng trực tuyến thật. Về
> phân tích cảm xúc, Van Thin và cộng sự (2023) [nguồn B] tổng hợp nghiên cứu ABSA tiếng Việt và
> chỉ ra xu hướng dùng mô hình học sâu ngày càng phức tạp; trong khi đó Nguyen và cộng sự (2021)
> [nguồn C] cho thấy bài toán xử lý bình luận TMĐT tiếng Việt (phát hiện khiếu nại) vẫn đang được
> nghiên cứu tích cực nhưng mỗi công trình giải quyết một bài toán con riêng lẻ.
>
> Khoảng trống chung của các công trình trên: (1) các giải pháp thử kính ảo hiện có thường tách rời
> khỏi một hệ thống bán hàng thật, đòi hỏi thiết bị hoặc ứng dụng riêng; (2) các nghiên cứu phân
> loại cảm xúc tiếng Việt phần lớn dừng ở mức thực nghiệm ngoại tuyến trên tập dữ liệu tĩnh, chưa
> gắn liền với một luồng nghiệp vụ thật nơi mô hình phải chạy đồng bộ mỗi khi có dữ liệu mới. Đề tài
> hướng tới lấp một phần khoảng trống này bằng cách đưa cả hai bài toán vào cùng một hệ thống
> thương mại điện tử đang vận hành thật, tích hợp trực tiếp vào luồng mua hàng và luồng đánh giá.

## Việc CHƯA làm

- Chưa đưa nội dung này vào `Copy.final.docx` - đang chờ người dùng xem lại, xác nhận 3 nguồn ổn,
  rồi mới viết chính thức (kèm trích dẫn [13][14][15] nối tiếp 12 mục hiện có trong Tài liệu tham
  khảo, và đánh số lại mục nếu chèn vào giữa Chương 1).
- Nếu người dùng muốn tìm thêm nguồn khác hoặc thay nguồn, cần tìm/xác minh lại tương tự (xác minh
  chéo qua ít nhất 2 nguồn độc lập trước khi dùng, tuyệt đối không tự bịa tên tác giả/link).
