-- =============================================================
-- Seed du lieu san pham kinh mat (nguon: intl.lespecs.com + carfia.com)
-- Danh muc duoc gan theo dang gong kinh (Frame Shape), moi san
-- pham co them gioi tinh (gender: nu/nam/unisex) de loc tren
-- trang chu. Anh san pham da duoc tai ve media/products/.
--
-- LUU Y: file nay CHI liet ke dung nhung san pham THAT SU dang
-- co trong CSDL (co anh that trong media/products/). Ban dau file
-- nay co ~45 dong INSERT cho ca 10 danh muc, nhung phan lon chi la
-- du lieu crawl thu (dat hang) roi khong dung toi - anh chua bao
-- gio duoc tai ve nen chua tung duoc chen vao CSDL thuc te. Da don
-- lai (xem CLAUDE_PROGRESS.md) chi giu phan da thuc su len web.
-- =============================================================

SET NAMES utf8mb4;

-- ---------- Danh muc theo dang gong kinh (chi 2 danh muc dang co san pham) ----------
INSERT INTO products_category (name, slug, created_at) SELECT 'Vuông (Square)', 'vuong-square', NOW() WHERE NOT EXISTS (SELECT 1 FROM products_category WHERE slug = 'vuong-square');
INSERT INTO products_category (name, slug, created_at) SELECT 'Oval', 'oval', NOW() WHERE NOT EXISTS (SELECT 1 FROM products_category WHERE slug = 'oval');

-- ---------- San pham ----------
INSERT INTO products_product (name, slug, description, price, stock_quantity, image, is_active, created_at, updated_at, category_id, created_by_id, gender) SELECT 'Incantation', 'incantation-black', 'Designed with a nod to the effortless glamour of the 70s, INCANTATION is a statement-making silhouette that feels both feminine and flattering. Featuring an oversized frame and refined detailing, this style brings a touch of vintage allure while remaining modern and wearable.
- Finished in a black frame with smoke mono lenses.
- Made using BPA free polymer plastic which is lightweight, durable and impact resistant.
- Fitted with shatterproof and scratch resistant polycarbonate lenses.', 1651000, 19, 'products/incantation-black.jpg', 1, NOW(), NOW(), (SELECT id FROM products_category WHERE slug = 'vuong-square'), NULL, 'nu' WHERE NOT EXISTS (SELECT 1 FROM products_product WHERE slug = 'incantation-black');
INSERT INTO products_product (name, slug, description, price, stock_quantity, image, is_active, created_at, updated_at, category_id, created_by_id, gender) SELECT 'Mythic', 'mythic-gold-blue-light-lens', 'Defined by its geometric silhouette and slimline metal construction, MYTHIC octagonal sunglasses are a modern classic with sharp appeal. The unique lens shape offers a clean, angular finish, while the tapered temples and adjustable nose pads ensure a tailored fit. This frame is finished with our signature flag stripe mono block end piece and sleek slimline metal temples.
- Finished in a gold frame.
- Sturdy metal frame fitted with allergy-free cushioned PVC nose pads.
- Fitted with anti-blue...', 2159000, 18, 'products/mythic-gold-blue-light-lens.jpg', 1, NOW(), NOW(), (SELECT id FROM products_category WHERE slug = 'vuong-square'), NULL, 'unisex' WHERE NOT EXISTS (SELECT 1 FROM products_product WHERE slug = 'mythic-gold-blue-light-lens');
INSERT INTO products_product (name, slug, description, price, stock_quantity, image, is_active, created_at, updated_at, category_id, created_by_id, gender) SELECT 'Impossible', 'impossible-tokyo-tort', 'Designed with a rounded profile and wide proportions for allface sizes, our IMPOSSIBLE rectangular frame sunglasses area wardrobe staple for both guys and girls. Offering a classic nineties inspired look, this unisex sunglass features discreet LeSpecs metal stud detailing on both temples.
- Finished in a tokyo tort frame with smoke mono lenses.
- A lightweight, durable and impact resistant polycarbonate frame.
- Fitted with shatterproof and scratch resistant polycarbonate lenses.', 1778000, 48, 'products/impossible-tokyo-tort.jpg', 1, NOW(), NOW(), (SELECT id FROM products_category WHERE slug = 'vuong-square'), NULL, 'unisex' WHERE NOT EXISTS (SELECT 1 FROM products_product WHERE slug = 'impossible-tokyo-tort');
INSERT INTO products_product (name, slug, description, price, stock_quantity, image, is_active, created_at, updated_at, category_id, created_by_id, gender, sku, specs, care_instructions) SELECT 'Dublin', 'dublin', 'Dublin là mẫu kính gọng tròn (oval) tối giản, được chế tác từ chất liệu acetate cao cấp với tông màu trong suốt tinh tế - lựa chọn hoàn hảo cho phong cách vừa hiện đại vừa cổ điển, phù hợp cả nam và nữ.
- Gọng acetate trong suốt, nhẹ và bền, ôm sát khuôn mặt thoải mái cả ngày dài.
- Thiết kế tròn (oval) full-rim cổ điển, tôn lên nét thanh lịch, tinh tế.
- Càng kính bọc chi tiết ánh vàng tạo điểm nhấn sang trọng.
- Form dáng unisex linh hoạt, lắp được tròng cận/viễn theo toa hoặc tròng thường.', 1890000, 20, 'products/dublin-oval-front.webp', 1, NOW(), NOW(), (SELECT id FROM products_category WHERE slug = 'oval'), NULL, 'unisex', 'CA5506-FC10', '{"Màu gọng": "Trong suốt (Clear)", "Dáng gọng": "Oval", "Cỡ gọng": "M", "Chất liệu gọng": "Acetate", "Chiều rộng gọng": "142 mm", "Cầu mũi": "21 mm", "Chiều rộng tròng kính": "50 mm", "Chiều cao gọng": "43 mm", "Chiều dài càng kính": "145 mm"}', '- Bảo quản kính trong túi/hộp đi kèm khi không sử dụng.
- Lau tròng kính bằng khăn microfiber đi kèm, tránh dùng khăn giấy hoặc vải thô dễ gây trầy xước.
- Không đặt kính úp mặt tròng kính xuống các bề mặt cứng.
- Tránh để kính ở nơi có nhiệt độ cao (trong xe hơi đóng kín, gần nguồn nhiệt).' WHERE NOT EXISTS (SELECT 1 FROM products_product WHERE slug = 'dublin');
