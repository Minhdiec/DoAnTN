---
name: humanizer
description: Viết lại (humanize) văn bản để loại bỏ các dấu hiệu văn phong AI theo danh mục của Wikipedia "Signs of AI writing" — sáo ngữ đề cao ý nghĩa, ngôn ngữ quảng cáo, quy gán mơ hồ, cấu trúc "không chỉ X mà còn Y", lạm dụng in đậm/em dash/emoji, mục "Thách thức và Triển vọng", rác markdown và citation — trong khi giữ nguyên tuyệt đối ý nghĩa và sự thật. Dùng skill này bất cứ khi nào người dùng nói "humanize", "làm cho giống người viết", "bớt giọng AI", "nghe như ChatGPT quá", "sửa cho tự nhiên hơn", "remove AI tells", hoặc đưa một đoạn văn và nhờ viết lại cho tự nhiên — kể cả khi họ không nhắc tới từ "AI".
---

# Humanizer

Viết lại văn bản để nó đọc như do người viết, bằng cách gỡ bỏ các khuôn mẫu đặc trưng của LLM, mà **không** đổi ý nghĩa và **không** thêm thông tin.

## Ba ràng buộc không được vi phạm

1. **Giữ nguyên ý nghĩa.** Mỗi mệnh đề trong bản gốc phải còn nguyên trong bản viết lại.
2. **Giữ nguyên sự thật.** Không đổi số liệu, tên riêng, ngày tháng, đơn vị, trích dẫn, quan hệ nhân quả, mức độ chắc chắn ("có thể" không được thành "chắc chắn").
3. **Không thêm gì mới.** Không thêm ví dụ, số liệu, nhận định, chuyển ý mang nội dung mới, hay "cho đầy đặn hơn". Nếu một câu gốc rỗng tuếch (chỉ là sáo ngữ đề cao), **xóa nó**, đừng thay bằng một câu rỗng khác.

Ngoài ra: giữ nguyên ngôn ngữ của bản gốc (tiếng Việt viết lại bằng tiếng Việt, tiếng Anh bằng tiếng Anh) và giữ thuật ngữ chuyên ngành như gốc.

Ràng buộc 3 là điểm hay bị vi phạm nhất. Khi gỡ một cụm sáo rỗng, phản xạ tự nhiên là viết một câu khác cho "đủ ý" — nhưng câu đó là thông tin bạn tự nghĩ ra. Để trống là đúng.

## Quy trình

1. **Đọc hết văn bản trước khi sửa.** Ghi nhận thể loại (bài luận, mô tả sản phẩm, báo cáo, email, bài viết wiki) vì chuẩn "tự nhiên" khác nhau theo thể loại.
2. **Quét theo checklist bên dưới**, đánh dấu từng chỗ.
3. **Viết lại theo từng câu**, không viết lại từ đầu theo trí nhớ — viết lại từ trí nhớ là cách nhanh nhất để đánh mất chi tiết.
4. **Đối chiếu sự thật**: duyệt lại bản gốc, liệt kê nhẩm mọi con số/tên/ngày/khẳng định và xác nhận chúng còn nguyên, không dư.
5. **Đọc lại thành tiếng trong đầu.** Nếu một câu nghe như lời giới thiệu sản phẩm hoặc lời tổng kết bài giảng, nó chưa xong.

Nếu văn bản quá dài để xử lý một lượt, chia theo đoạn và giữ nguyên thứ tự đoạn.

## Checklist dấu hiệu AI cần gỡ

### A. Nội dung và giọng điệu

**1. Đề cao ý nghĩa, di sản, xu hướng lớn.** Đây là dấu hiệu mạnh nhất. Xóa hẳn những câu kiểu "đóng vai trò quan trọng trong...", "là minh chứng cho...", "đánh dấu bước ngoặt", "góp phần vào bức tranh chung của...", "khẳng định vị thế", "để lại dấu ấn sâu đậm"; tiếng Anh: *stands as a testament, plays a crucial/pivotal role, underscores the importance of, reflects broader, marking a shift, evolving landscape, indelible mark*. Nếu câu chỉ nói "cái này quan trọng" mà không nói thêm sự kiện nào, xóa. Nếu có kèm sự kiện, giữ sự kiện, bỏ phần tán dương.

**2. Phân tích hời hợt gắn đuôi.** Mệnh đề phân từ treo ở cuối câu: "..., góp phần nâng cao trải nghiệm người dùng", "..., thể hiện cam kết với chất lượng"; tiếng Anh *..., highlighting/ensuring/reflecting/fostering/contributing to...*. Gần như luôn là suy diễn thêm của LLM chứ không phải dữ kiện. Cắt.

**3. Ngôn ngữ quảng cáo.** *sôi động, phong phú, đa dạng, nổi tiếng, tọa lạc giữa lòng, mang đậm, đẳng cấp, tối ưu, đột phá*; tiếng Anh *boasts, vibrant, rich, renowned, nestled, in the heart of, groundbreaking, diverse array, commitment to, seamless*. Thay bằng mô tả trung tính hoặc bỏ tính từ.

**4. Quy gán mơ hồ và thổi phồng số nguồn.** "Nhiều chuyên gia cho rằng", "Các báo cáo ngành chỉ ra", "Giới quan sát nhận định", *Experts argue, Observers have noted, several sources*. Nếu bản gốc có nguồn cụ thể, nêu đích danh nguồn đó. Nếu không có nguồn nào, hạ về khẳng định trần hoặc bỏ nếu nó chỉ là ý kiến LLM tự thêm.

**5. Công thức "Thách thức" / "Triển vọng tương lai".** Mẫu "Dù có nhiều [ưu điểm], X vẫn đối mặt với không ít thách thức..." kết bằng một câu lạc quan mơ hồ. Giữ các thách thức *cụ thể* nếu bản gốc nêu; bỏ khung công thức và câu kết an ủi.

**6. Đoạn kết tổng kết.** "Tóm lại", "Nhìn chung", "Có thể thấy rằng", mục "Kết luận" chỉ nhắc lại nội dung đã nói. Bỏ, trừ khi bản gốc thực sự có kết luận mang thông tin mới.

**7. Rào đón kiểu giáo huấn.** "Điều quan trọng cần lưu ý là", "Cần nhấn mạnh rằng", *it's important to note, worth noting*. Bỏ cụm rào đón, giữ nội dung phía sau.

**8. Rào đón về nguồn tin / knowledge cutoff.** "Thông tin chi tiết hiện chưa được công bố rộng rãi", "dựa trên các nguồn hiện có", "nhân vật này giữ kín đời tư". Xóa — đây là suy đoán, không phải sự thật.

**9. Lời nói với người dùng.** "Hy vọng bài viết hữu ích", "Chắc chắn rồi!", "Bạn có muốn tôi...", "Dưới đây là...", chỗ trống chưa điền như `[Tên công ty]`, `(Thêm link tại đây)`. Xóa hẳn. Nếu có chỗ trống chưa điền, **không tự bịa nội dung** — giữ nguyên chỗ trống và báo cho người dùng.

### B. Câu chữ

**10. Né động từ "là/có".** LLM thay *là* bằng *đóng vai trò là, được xem là, thể hiện, mang trong mình*; tiếng Anh *serves as, stands as, represents, functions as, features, boasts, refers to*. Trả về dạng đơn giản: "X là Y", "X có Y".
> *Gallery 825 serves as LAAA's exhibition space. The gallery features four separate spaces.* → *Gallery 825 is LAAA's exhibition space. It has four spaces.*

**11. Quan hệ mơ hồ.** "gắn liền với", "có liên hệ với", *associated with, connected to*. Nếu bản gốc cho biết quan hệ thật (ai làm gì, chức vụ nào), nói thẳng. Nếu không biết, giữ nguyên mức mơ hồ chứ đừng đoán ra quan hệ cụ thể — đó là thêm thông tin.

**12. Đối lập phủ định.** "không chỉ X mà còn Y", "đây không phải là X, mà là Y", *not just… but…, it's not… it's…, rather than*. Viết thành câu khẳng định thẳng: nếu cả X và Y đều đúng, nêu cả hai bằng câu thường.

**13. Quy tắc ba.** Chuỗi ba tính từ / ba cụm song song đều đặn. Rút còn những mục thực sự có trong bản gốc; đừng giữ nhịp ba chỉ vì nghe kêu. Không được cắt mất một mục nếu đó là dữ kiện thật — khi đó hãy phá nhịp bằng cách đổi cấu trúc câu.

**14. Từ vựng AI dày đặc.** Giảm mật độ: *delve, crucial, pivotal, testament, underscore, foster, robust, leverage, intricate, tapestry, landscape, meticulous, garner, align with, showcase, enhance, bolster, Additionally (mở đầu câu)*; tiếng Việt: *then chốt, cốt lõi, chủ chốt, thúc đẩy, tối ưu hóa, đa chiều, toàn diện, sâu sắc, nổi bật, bên cạnh đó (lặp đi lặp lại)*. Thay bằng từ thường ngày.

**15. Từ trang trọng không cần thiết.** *authored → wrote*, *utilized → used*, *relocated → moved*, *attempted → tried*, *prior to → before*, *in order to → to*; tiếng Việt: *tiến hành thực hiện → làm*, *sở hữu → có*, *nhằm mục đích → để*.

**16. Biến tấu từ ngữ (elegant variation).** LLM tránh lặp từ bằng cách đổi sang từ đồng nghĩa lòng vòng ("công ty" → "doanh nghiệp này" → "đơn vị" → "tổ chức nói trên"). Người viết thật lặp lại danh từ hoặc dùng đại từ. Trả về cách gọi nhất quán.

**17. Nhịp câu đều tăm tắp.** Nếu mọi câu dài 20–25 từ với cùng cấu trúc, trộn lại: chèn câu ngắn, ghép hai câu, đảo mệnh đề. Đây là điều chỉnh về nhịp, không phải về nội dung.

### C. Hình thức

**18. In đậm quá tay.** Bỏ in đậm rải rác giữa câu để "nhấn mạnh". Chỉ giữ in đậm nếu bản gốc có ý nghĩa chức năng (tên mục trong bảng thuật ngữ).

**19. Danh sách kiểu "**Tiêu đề**: mô tả".** Gạch đầu dòng + tiêu đề in đậm + dấu hai chấm. Nếu các mục là một dòng suy nghĩ liền mạch, chuyển thành văn xuôi. Nếu bản chất là danh sách (danh mục vật phẩm, các bước), giữ danh sách nhưng bỏ in đậm.

**20. Em dash.** Em dash có khoảng trắng hai bên ( — ) dùng thay dấu phẩy/ngoặc đơn/hai chấm. Thay bằng dấu phẩy, ngoặc đơn, hoặc tách câu. Không cần diệt sạch mọi dấu gạch ngang, chỉ bỏ kiểu dùng "nhấn nhá" lặp lại.

**21. Tiêu đề Viết Hoa Kiểu Tên Riêng.** "Tác Động Của Công Nghệ" → "Tác động của công nghệ". Bỏ tiêu đề lặp lại tên bài ở đầu văn bản; bỏ tiêu đề rỗng chỉ chứa tiêu đề con.

**22. Emoji trang trí, đường kẻ ngang `---` giữa các mục, dấu nháy cong (“ ” ’).** Bỏ emoji, bỏ đường kẻ, đổi nháy cong thành nháy thẳng (" ').

**23. Rác kỹ thuật.** Xóa `:contentReference[oaicite:0]{index=0}`, `turn0search0`, `[cite: 1]`, `(start_span)`, `【85†L261-269】`, `[attached_file:1]`, `?utm_source=chatgpt.com` trong URL, `↩`. Giữ nguyên phần URL còn lại.

## Không sửa quá tay

Skill này dễ gây hại theo hướng ngược lại. Tránh:

- Biến văn bản thành giọng suồng sã nếu bản gốc là văn trang trọng. Mục tiêu là *người viết*, không phải *người viết blog*.
- Chèn lỗi chính tả, câu cụt, hay tiếng lóng để "trông giống người". Ngữ pháp chuẩn không phải dấu hiệu AI.
- Xóa thông tin chỉ vì câu chứa nó có từ trong danh sách. Từ ngữ mới là thứ bị thay, dữ kiện thì ở lại.
- Cắt độ dài mạnh tay. Bản viết lại thường ngắn hơn bản gốc khoảng 10–25% do gỡ sáo ngữ; ngắn hơn nhiều là dấu hiệu đã mất nội dung.
- Sửa cả những chỗ vốn đã ổn. Câu nào không dính dấu hiệu nào thì để nguyên.

## Định dạng đầu ra

Mặc định trả về **bản viết lại hoàn chỉnh** trước, không có lời dẫn. Sau đó thêm một danh sách ngắn (3–6 gạch đầu dòng) nêu những nhóm dấu hiệu đã xử lý và bất cứ chỗ nào cần người dùng tự quyết — ví dụ thông tin mơ hồ mà việc làm rõ sẽ đòi hỏi thêm dữ kiện, hoặc chỗ trống chưa điền trong bản gốc.

Nếu người dùng chỉ muốn văn bản, bỏ phần danh sách. Nếu người dùng muốn thấy rõ thay đổi, trình bày đối chiếu trước/sau theo từng câu đã sửa.

Khi một đoạn gần như toàn sáo ngữ và việc gỡ sẽ làm mất gần hết đoạn đó, đừng tự viết bù. Báo cho người dùng biết đoạn đó gần như không mang thông tin và hỏi họ muốn bổ sung dữ kiện gì.

## Ví dụ

**Gốc:**
> Ra đời năm 2015, VietPay không chỉ là một ứng dụng thanh toán mà còn là minh chứng cho sự chuyển mình mạnh mẽ của hệ sinh thái fintech Việt Nam. Với hơn 2 triệu người dùng, nền tảng này đóng vai trò then chốt trong việc thúc đẩy thanh toán không tiền mặt, góp phần định hình lại thói quen tiêu dùng của người Việt. Các chuyên gia nhận định rằng đây là bước ngoặt quan trọng.

**Viết lại:**
> VietPay ra đời năm 2015 và hiện có hơn 2 triệu người dùng. Đây là một ứng dụng thanh toán không tiền mặt.

Đã gỡ: "không chỉ… mà còn", "minh chứng cho", "đóng vai trò then chốt", "góp phần định hình lại", "các chuyên gia nhận định" (không có nguồn). Hai dữ kiện duy nhất trong bản gốc — năm thành lập và số người dùng — được giữ nguyên.

**Gốc:**
> The museum **stands as a testament** to the region's vibrant cultural heritage — housing over 3,000 artifacts, showcasing the intricate craftsmanship of local artisans, and serving as a vital hub for community engagement.

**Viết lại:**
> The museum has over 3,000 artifacts made by local artisans. It also hosts community events.

Đã gỡ: in đậm, "stands as a testament", "vibrant", em dash, nhịp ba, "showcasing/intricate", "serving as a vital hub". "Community engagement" là dữ kiện mơ hồ trong gốc nên được giữ ở mức mơ hồ tương đương, không cụ thể hóa thành sự kiện nào.
