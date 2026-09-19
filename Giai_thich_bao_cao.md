# Giải thích báo cáo Astraea (đọc kèm Bao_cao_do_an_phan_tich.docx)

File này giải thích từng phần của báo cáo bằng lời dễ hiểu: đoạn đó nói gì, vì sao nó có mặt trong báo cáo, và các từ chuyên môn nghĩa là gì. Đánh số mục khớp đúng với file docx để bạn dò song song hai file khi cần.

---

## Phần đầu (bìa, mục lục, danh mục viết tắt)

Đây là các trang thủ tục bắt buộc của một báo cáo tốt nghiệp: trang bìa ghi tên đề tài và thông tin sinh viên, trang nhận xét để giảng viên chấm điền tay, mục lục tự động (mở file trong Word rồi bấm chuột phải vào mục lục, chọn Update Field, để số trang tự điền đúng), danh mục hình vẽ và danh mục bảng để tra nhanh, danh mục từ viết tắt để người đọc không rành kỹ thuật vẫn tra được MVT, ORM, ASGI... nghĩa là gì. Phần này không mang nội dung học thuật, chỉ là hình thức trình bày chuẩn.

---

## Chương 1: Tổng quan

### 1.1. Lý do chọn đề tài
Ý chính: mua kính online thiếu một bước quan trọng là "đeo thử", nên đồ án làm ra tính năng thử kính ảo để bù vào chỗ thiếu đó. Ngoài ra web bán hàng nào cũng có nhiều đánh giá, đọc tay không xuể, nên làm thêm máy tự đọc và phân loại cảm xúc đánh giá. Đây là đoạn "tại sao làm" của cả đồ án, hội đồng thường hỏi câu này đầu tiên.

### 1.2. Mục tiêu đề tài
Liệt kê đồ án phải làm được gì. Nhớ đơn giản: một website bán kính bình thường (giỏ hàng, đặt hàng...) cộng thêm 2 điểm nhấn AI là thử kính ảo và phân loại cảm xúc. Mục tiêu cụ thể là danh sách các đầu việc kỹ thuật cụ thể hơn để tự kiểm tra đã làm đủ chưa.

### 1.3. Phạm vi đề tài
Đây là phần "nói rõ luôn từ đầu cái gì có, cái gì không có" để tránh hội đồng hỏi vặn sau này. Đáng chú ý nhất: thanh toán là giả (bấm xong coi như thành công luôn, không có cổng thanh toán thật), và ví điện tử có code nhưng chưa có giao diện dùng được. Nói thẳng những giới hạn này ra trước là để chủ động, tránh bị hỏi mà lúng túng.

---

## Chương 2: Cơ sở lý thuyết

Chương này giải thích từng công nghệ dùng trong đồ án. Cách nhớ nhanh từng mục:

- **2.1 Django**: framework viết web bằng Python. Nhớ 3 chữ MVT: Model (dữ liệu), View (xử lý), Template (giao diện). Giống bếp nhà hàng: kho nguyên liệu, đầu bếp, cách bày món.
- **2.2 MySQL, PyMySQL**: nơi lưu dữ liệu. Dùng PyMySQL vì cài đặt trên Windows dễ hơn driver mặc định.
- **2.3 WebSocket**: lý do phải dùng cái này thay vì HTTP thường, vì thử kính ảo cần gửi rất nhiều khung hình mỗi giây, HTTP thường (mỗi lần hỏi một câu) quá chậm, WebSocket giữ một đường dây mở sẵn như cuộc gọi điện thoại.
- **2.4 MediaPipe**: công cụ có sẵn của Google để tìm khuôn mặt trong ảnh. Đồ án chỉ lấy đúng 2 điểm (khoé 2 mắt) từ hàng trăm điểm mà nó trả về, đủ để biết mắt ở đâu, cách nhau bao xa, đầu nghiêng bao nhiêu.
- **2.5 OpenCV**: thư viện xử lý ảnh, dùng để xoay/co giãn ảnh kính và dán nó chồng lên ảnh mặt sao cho khớp.
- **2.6 One-Euro Filter**: bộ lọc chống rung. Nếu không có nó, kính sẽ rung nhẹ liên tục trên mặt vì máy nhận diện mắt hơi lệch vài pixel giữa các khung hình dù mặt đứng yên.
- **2.7 Phân loại cảm xúc**: 3 bước để máy hiểu một câu tiếng Việt là khen hay chê: tách câu thành từ, đổi từ thành số (TF-IDF), rồi cho một mô hình toán học (Logistic Regression) đoán nhãn.

Nếu hội đồng hỏi "sao chọn công nghệ X mà không chọn Y", câu trả lời nằm ngay trong lý do ở từng mục này.

---

## Chương 3: Phân tích và thiết kế hệ thống

### 3.1 Quy trình tổng quát
Đây là hành trình một khách hàng đi qua: tìm sản phẩm, thử kính, thêm giỏ, đặt hàng, theo dõi đơn, đánh giá. Cứ hình dung đây là "câu chuyện" của một lần mua hàng thật.

### 3.2 Bảng đặc tả use case
Đây là bảng liệt kê từng chức năng của hệ thống, ai được dùng, cần điều kiện gì trước, làm gì thì hệ thống phản ứng ra sao, và có những trường hợp lỗi nào. Đây là tài liệu "hợp đồng" giữa yêu cầu và code, thường bị hội đồng hỏi để kiểm tra sinh viên có hiểu đúng hệ thống mình làm hay không.

### 3.3 và 3.5 Các bảng dữ liệu
Đây là danh sách các "bảng" trong cơ sở dữ liệu (giống các sheet Excel có liên kết với nhau), ví dụ bảng User lưu tài khoản, bảng Product lưu sản phẩm. Bảng 3.3 đến 3.10 mô tả từng cột trong từng bảng: tên cột, kiểu dữ liệu, và ghi chú ràng buộc. Phần này đã được đối chiếu trực tiếp với code models.py thật, không phải suy đoán.

### 3.4 Sơ đồ ERD
Là hình vẽ thể hiện các bảng dữ liệu ở trên nối với nhau như thế nào bằng đường kẻ, ví dụ một User có nhiều Order. Bạn cần tự vẽ hình này bằng công cụ như dbdiagram.io rồi chèn vào đúng vị trí đã đánh dấu trong docx.

---

## Chương 4: Triển khai và thực hiện

Đây là chương kỹ thuật nặng nhất, cũng là chương ghi điểm nhiều nhất vì có số liệu thực nghiệm thật.

### 4.1 đến 4.3
Hướng dẫn cài đặt, danh sách URL của website, và bảng liệt kê các hàm quan trọng nhất trong code kèm giải thích logic. Đây là phần tra cứu, không cần học thuộc, cần khi hội đồng hỏi "hàm nào xử lý việc X".

### 4.4 Thử kính ảo, phần quan trọng nhất
Giải thích cách hiểu nhanh:
1. **Giao thức WebSocket (4.4.1)**: trình duyệt gửi ảnh, server trả ảnh đã dán kính. Chỉ vậy thôi.
2. **Luồng xử lý (4.4.2)**: một khung hình đi qua 8 bước, từ lúc chụp ở trình duyệt tới lúc hiển thị lại. Bảng 4.4 là "lưu đồ" viết dưới dạng bảng.
3. **Thuật toán dán kính (4.4.3)**: máy tìm 2 tâm tròng kính trên ảnh PNG, rồi tính toán xoay/co giãn sao cho 2 tâm đó khớp đúng vào 2 con mắt trên khuôn mặt thật. Nếu không tìm được tâm tròng kính (ảnh xấu, gọng quá mảnh) thì dùng cách dự phòng đơn giản hơn.
4. **Tối ưu tốc độ (4.4.4), phần quan trọng nhất để ghi điểm**: đồ án đo tốc độ xử lý bằng số thật (FPS, khung hình mỗi giây) trước và sau khi áp dụng 5 mẹo tối ưu, rồi TẮT RIÊNG từng mẹo để xem mẹo nào quan trọng nhất. Kết quả: mẹo "bớt gọi máy nhận diện khuôn mặt liên tục" (kỹ thuật 2) quan trọng nhất, không phải mẹo "giảm độ phân giải ảnh" như dự đoán ban đầu. Đây chính là điểm mạnh nhất của đồ án: không chỉ làm cho chạy được, mà còn đo và hiểu tại sao nó nhanh hơn.
5. **Sửa lỗi thực tế (4.4.5)**: kể lại 2 lỗi chỉ phát hiện được khi test bằng webcam thật (không phát hiện được khi test bằng ảnh tĩnh), và cách tìm ra nguyên nhân gốc rồi sửa. Đây là minh chứng cho quá trình làm việc khoa học, không phải chỉnh bừa cho hết lỗi.

### 4.5 Phân loại cảm xúc
Giải thích nhanh: có gần 27 nghìn câu bình luận tiếng Việt đã gán nhãn sẵn (khen/trung lập/chê) để "dạy" máy. Sau khi dạy xong, đồ án thử 3 cách học khác nhau rồi so sánh, chọn Logistic Regression không phải vì nó đoán đúng nhiều nhất tổng thể, mà vì nó đoán cân bằng hơn giữa 3 loại cảm xúc (đặc biệt là loại "trung lập", vốn ít gặp và khó đoán nhất). Đoạn code trong báo cáo cho thấy mô hình này được gọi thật mỗi khi có người gửi đánh giá mới trên web, không chỉ chạy thử trong notebook rồi thôi.

---

## Chương 5: Giao diện và demo chức năng

Mỗi mục 5.1 đến 5.7 mô tả một màn hình của website: trang đăng nhập, trang chủ, tìm kiếm, trang sản phẩm, giỏ hàng, đơn hàng, yêu thích. Bạn cần tự mở web thật, chụp màn hình, chèn vào đúng vị trí đã đánh dấu `[ Chèn ảnh chụp: ... ]` trước khi nộp.

### 5.8 Trang quản trị (Django Admin), phần hay bị hỏi nhất
Đây là trang riêng cho quản trị viên (không phải khách hàng), vào bằng đường dẫn /admin/. Bảng 5.1 liệt kê chính xác 7 mục quản lý được: Tài khoản, Danh mục, Sản phẩm, Đơn hàng, Đánh giá, Ảnh kính AR, Ví điện tử. Hai mục Giỏ hàng và Yêu thích KHÔNG có trong trang quản trị, vì đó là dữ liệu riêng tư/tạm thời của từng khách, quản trị viên không cần thấy. Điểm hay: trang Đơn hàng chỉ cho sửa đúng 1 ô là "trạng thái giao hàng", còn lại khoá cứng để không ai sửa nhầm giá hay số lượng đã bán. Trang Đánh giá không cho thêm/sửa bình luận giả, chỉ được xem và xoá nếu vi phạm. Và có sẵn 1 biểu đồ nhỏ cho thấy tỉ lệ khen/chê theo từng sản phẩm ngay trên trang danh sách.

---

## Chương 6: Kết luận

### 6.1 Tóm tắt
Nhắc lại ngắn gọn đã làm được gì, không có thông tin mới, chỉ tổng kết.

### 6.2 Đối chiếu tài liệu đặc tả gốc với code thật
Đây là phần thể hiện tính trung thực và cẩn thận của đồ án: so sánh những gì đề bài/tài liệu ban đầu yêu cầu với những gì code thực sự làm được, chia thành 4 nhóm rõ ràng:
- **6.2.1 Đã làm đúng**: những yêu cầu đã hoàn thành, có bằng chứng là dòng code cụ thể.
- **6.2.2 Làm một phần hoặc lệch**: ví dụ nhãn cảm xúc lẽ ra chỉ người viết và admin xem được, nhưng code hiện tại lại cho MỌI người xem công khai. Đây là chỗ nên nhớ kỹ vì hội đồng rất hay hỏi "sao làm sai với đặc tả ở đây".
- **6.2.3 Chưa làm**: ví dụ ví điện tử chưa có giao diện, thanh toán chưa nối cổng thật.
- **6.2.4 Có nhưng đặc tả không yêu cầu**: những thứ phát sinh trong lúc làm, như tính năng quên mật khẩu, không có trong đề bài gốc nhưng vẫn làm vì cần thiết.

### 6.3 Đóng góp của đề tài
Điểm nhấn "vì sao đồ án này không chỉ là làm cho chạy": đo đạc số liệu thật, tối ưu có căn cứ, tích hợp AI vào luồng thật của web chứ không để riêng một chỗ.

### 6.4 Hạn chế và 6.5 Hướng phát triển
Đây là câu trả lời có sẵn cho câu hỏi kinh điển "đồ án còn thiếu gì, nếu làm tiếp sẽ làm gì". Nên đọc kỹ phần này trước khi bảo vệ vì gần như chắc chắn sẽ bị hỏi trúng một trong các mục ở đây.

---

## Vài từ hay bị hỏi mà không phải ai cũng nhớ nghĩa

- **FPS (khung hình mỗi giây)**: số càng cao thì hình ảnh càng mượt. Dưới khoảng 15 FPS mắt người bắt đầu thấy giật.
- **ROI (vùng quan tâm)**: thay vì quét cả tấm ảnh to để tìm mắt, chỉ quét một ô nhỏ quanh chỗ mắt vừa thấy lần trước, đỡ tốn công.
- **CLAHE**: kỹ thuật làm sáng ảnh khi thiếu sáng, nhưng làm sáng theo từng vùng nhỏ thay vì làm sáng đều cả ảnh, nên trông tự nhiên hơn.
- **TF-IDF**: cách biến câu chữ thành một dãy số để máy tính "hiểu" được, dựa trên từ nào hiếm và đặc trưng thì được coi là quan trọng hơn.
- **macro-F1**: một cách chấm điểm mô hình phân loại công bằng cho cả nhóm ít dữ liệu, khác với accuracy (độ chính xác) vốn dễ bị nhóm đông áp đảo.
- **Transaction, atomic**: một khối lệnh trong đó hoặc là mọi thứ đều được lưu thành công, hoặc nếu có lỗi giữa chừng thì không có gì được lưu cả. Dùng để đảm bảo tồn kho và đơn hàng luôn khớp nhau.

---

*File này chỉ là tài liệu hỗ trợ đọc hiểu, không nộp kèm báo cáo chính thức.*
