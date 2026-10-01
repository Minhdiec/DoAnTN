// Ve lai seq_6 (Thu kinh ao) va seq_11 (Danh gia) co day du khung alt/opt/loop
const fs = require("fs");

const ST = {
  life: "shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;dropTarget=0;collapsible=0;recursiveResize=0;outlineConnect=0;strokeColor=#000000;fillColor=#FFFFFF;fontColor=#000000;strokeWidth=1.2;size=60;fontFamily=Times New Roman;fontSize=13;",
  call: "html=1;verticalAlign=bottom;labelBackgroundColor=#FFFFFF;endArrow=block;endFill=1;rounded=0;strokeColor=#000000;fontColor=#000000;fontFamily=Times New Roman;fontSize=12;",
  ret: "html=1;verticalAlign=bottom;labelBackgroundColor=#FFFFFF;endArrow=open;endFill=0;endSize=8;dashed=1;rounded=0;strokeColor=#000000;fontColor=#000000;fontFamily=Times New Roman;fontSize=12;",
  self: "html=1;align=left;verticalAlign=middle;spacingLeft=6;endArrow=block;endFill=1;rounded=0;strokeColor=#000000;fontColor=#000000;labelBackgroundColor=#FFFFFF;fontFamily=Times New Roman;fontSize=12;",
  frame: "shape=umlFrame;whiteSpace=wrap;html=1;width=56;height=22;boundedLbl=1;verticalAlign=middle;align=center;fillColor=none;strokeColor=#000000;strokeWidth=1;fontFamily=Times New Roman;fontSize=12;fontStyle=1;",
  guard: "text;html=1;align=left;verticalAlign=middle;fontFamily=Times New Roman;fontSize=11;fontStyle=2;fontColor=#000000;",
  sep: "endArrow=none;html=1;dashed=1;strokeColor=#000000;strokeWidth=1;",
};
const esc = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/\n/g, "&lt;br&gt;");
const GAP = 220, X0 = 25, W = 150, TOP = 40;
const cx = (i) => X0 + i * GAP + W / 2;

function build(spec) {
  const { id, name, lifelines, steps } = spec;
  const P = id.replace("seq_", "p") + "_";
  let y = TOP + 90, n = 0, k = 0;
  const frames = [], msgs = [], stack = [];
  const cell = (s) => msgs.push(s);
  for (const st of steps) {
    if (st.frame) {
      const depth = stack.length;
      const [a, b] = st.span;
      const par = stack[stack.length - 1];
      let fx = cx(a) - 60 + depth * 12, fx2 = cx(b) + 70 - depth * 12;
      if (par) { fx = Math.max(fx, par.x + 12); fx2 = Math.min(fx2, par.x2 - 12); }
      const f = { kind: st.frame, x: fx, x2: fx2, y, seps: [], guards: [[y + 24, st.guard]] };
      stack.push(f); y += 44; continue;
    }
    if (st.else !== undefined) {
      const f = stack[stack.length - 1];
      y += 4; f.seps.push(y); f.guards.push([y + 14, st.else]); y += 34; continue;
    }
    if (st.end) {
      const f = stack.pop(); f.y2 = y + 6; frames.push(f); y += 22; continue;
    }
    n++;
    const lines = String(st.t).split("\n").length;
    const label = `${n}. ${st.t}`;
    if (st.self !== undefined) {
      const x = cx(st.self); y += 14 * lines;
      cell(`<mxCell id="${P}m${++k}" value="${esc(label)}" style="${ST.self}" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="${x}" y="${y}" as="sourcePoint"/><mxPoint x="${x}" y="${y + 26}" as="targetPoint"/><Array as="points"><mxPoint x="${x + 40}" y="${y}"/><mxPoint x="${x + 40}" y="${y + 26}"/></Array></mxGeometry></mxCell>`);
      y += 46;
    } else {
      const [a, b] = st.m; y += 16 * lines;
      cell(`<mxCell id="${P}m${++k}" value="${esc(label)}" style="${st.r ? ST.ret : ST.call}" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="${cx(a)}" y="${y}" as="sourcePoint"/><mxPoint x="${cx(b)}" y="${y}" as="targetPoint"/></mxGeometry></mxCell>`);
      y += 26;
    }
  }
  if (stack.length) throw new Error(id + ": khung chua dong");
  const H = y + 30 - TOP;
  const out = [`<mxCell id="0"/>`, `<mxCell id="1" parent="0"/>`];
  lifelines.forEach(([title, stereo], i) => out.push(
    `<mxCell id="${P}${i + 1}" value="${esc(`<b>${title}</b>\n«${stereo}»`)}" style="${ST.life}" vertex="1" parent="1"><mxGeometry x="${X0 + i * GAP}" y="${TOP}" width="${W}" height="${H}" as="geometry"/></mxCell>`));
  frames.forEach((f, i) => {
    out.push(`<mxCell id="${P}f${i}" value="${f.kind}" style="${ST.frame}" vertex="1" parent="1"><mxGeometry x="${f.x}" y="${f.y}" width="${f.x2 - f.x}" height="${f.y2 - f.y}" as="geometry"/></mxCell>`);
    f.seps.forEach((sy, j) => out.push(`<mxCell id="${P}f${i}s${j}" style="${ST.sep}" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="${f.x}" y="${sy}" as="sourcePoint"/><mxPoint x="${f.x2}" y="${sy}" as="targetPoint"/></mxGeometry></mxCell>`));
    f.guards.forEach(([gy, g], j) => out.push(`<mxCell id="${P}f${i}g${j}" value="${esc("[" + g + "]")}" style="${ST.guard}" vertex="1" parent="1"><mxGeometry x="${f.x + (j === 0 ? 60 : 6)}" y="${gy - 10}" width="${Math.min(360, f.x2 - f.x - 70)}" height="20" as="geometry"/></mxCell>`));
  });
  out.push(...msgs);
  const pw = X0 + lifelines.length * GAP + 40;
  return `<diagram id="${id}" name="${name}"><mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="${pw}" pageHeight="${y + 60}" background="#FFFFFF" math="0" shadow="0"><root>${out.join("")}</root></mxGraphModel></diagram>`;
}

// ============================ seq_11 DANH GIA ============================
const KH = 0, UI = 1, PC = 2, RC = 3, AI = 4, DB = 5;
const seq11 = {
  id: "seq_11", name: "Hình 3.13 - Đánh giá sản phẩm và phân loại cảm xúc",
  lifelines: [["Khách hàng", "Actor"], ["Giao diện chi tiết sản phẩm", "Boundary"], ["Bộ điều khiển sản phẩm", "Control"],
              ["Bộ điều khiển đánh giá", "Control"], ["Mô hình phân loại cảm xúc", "Service"], ["Cơ sở dữ liệu", "Entity / MySQL"]],
  steps: [
    { m: [KH, UI], t: "Bấm \"Đánh giá\" ở Đơn hàng\ncủa tôi (?item=id)" },
    { m: [UI, PC], t: "Yêu cầu trang sản phẩm" },
    { m: [PC, DB], t: "Lấy dòng đơn đã giao,\nchưa được đánh giá" },
    { r: 1, m: [DB, PC], t: "Danh sách dòng đơn" },
    { self: PC, t: "Chọn dòng theo ?item\nhoặc dòng mới nhất" },
    { r: 1, m: [PC, UI], t: "Trang sản phẩm, bình luận, thống kê" },
    { frame: "opt", span: [KH, UI], guard: "có dòng đơn đủ điều kiện" },
    { r: 1, m: [UI, KH], t: "Hiện form bình luận" },
    { end: 1 },
    { m: [KH, UI], t: "Chọn số sao, nhập nội dung,\nđính kèm ảnh/video, bấm Gửi" },
    { m: [UI, RC], t: "Gửi đánh giá (POST)" },
    { m: [RC, DB], t: "Lấy dòng đơn theo id\nvà người dùng" },
    { r: 1, m: [DB, RC], t: "Dòng đơn, trạng thái đơn" },
    { m: [RC, DB], t: "Kiểm tra dòng đơn đã có đánh giá" },
    { r: 1, m: [DB, RC], t: "Kết quả kiểm tra" },
    { self: RC, t: "Kiểm tra số sao\n(1-5) và nội dung" },
    { frame: "alt", span: [UI, DB], guard: "dòng đơn không thuộc người dùng" },
    { r: 1, m: [RC, UI], t: "Lỗi 404" },
    { else: "đơn đã bị hủy" },
    { r: 1, m: [RC, UI], t: "\"Chỉ đánh giá được đơn đã giao\",\nvề Đơn hàng của tôi" },
    { else: "dòng đơn đã được đánh giá" },
    { r: 1, m: [RC, UI], t: "\"Bạn đã đánh giá ... trong đơn #... rồi\"" },
    { else: "form không hợp lệ" },
    { r: 1, m: [RC, UI], t: "\"Vui lòng chọn số sao và nhập nội dung\"" },
    { else: "hợp lệ" },
    { m: [RC, AI], t: "Gửi nội dung bình luận" },
    { self: AI, t: "Làm sạch, tách từ,\nTF-IDF, Logistic Regression" },
    { r: 1, m: [AI, RC], t: "Nhãn cảm xúc + độ tin cậy" },
    { m: [RC, DB], t: "Lưu đánh giá kèm nhãn cảm xúc" },
    { frame: "loop", span: [RC, DB], guard: "mỗi file đính kèm, tối đa 5" },
    { m: [RC, DB], t: "Lưu file + bản ghi ReviewMedia" },
    { end: 1 },
    { r: 1, m: [RC, UI], t: "Quay về mục #danh-gia,\n\"Cảm ơn bạn đã đánh giá\"" },
    { r: 1, m: [UI, KH], t: "Hiển thị bình luận kèm\nnhãn cảm xúc, thống kê" },
    { end: 1 },
  ],
};

// ============================ seq_6 THU KINH ============================
const K = 0, B = 1, S = 2, I = 3, D = 4;
const seq6 = {
  id: "seq_6", name: "Hình 3.8 - Thử kính ảo",
  lifelines: [["Khách hàng", "Actor"], ["Cửa sổ thử kính", "Boundary"], ["Máy chủ xử lý (WebSocket)", "Control"],
              ["Mô-đun xử lý ảnh (MediaPipe, OpenCV)", "Service"], ["Cơ sở dữ liệu", "Entity / MySQL"]],
  steps: [
    { m: [K, B], t: "Bấm \"TRY ON\" (thẻ sản\nphẩm / trang chi tiết)" },
    { self: B, t: "Mở cửa sổ, đánh dấu mẫu\nkính, xin quyền mở webcam" },
    { frame: "alt", span: [K, D], guard: "từ chối quyền / trình duyệt không hỗ trợ camera" },
    { r: 1, m: [B, K], t: "Báo lỗi không mở được camera" },
    { else: "được cấp quyền camera" },
    { m: [B, S], t: "Mở kết nối WebSocket" },
    { m: [S, I], t: "Khởi tạo bộ nhận diện khuôn mặt" },
    { frame: "alt", span: [K, D], guard: "không có file mô hình" },
    { r: 1, m: [S, B], t: "Gửi lỗi, đóng kết nối" },
    { else: "khởi tạo thành công" },
    { m: [B, S], t: "Gửi mẫu kính đã chọn" },
    { m: [S, D], t: "Lấy thông tin mẫu kính" },
    { r: 1, m: [D, S], t: "Đường dẫn ảnh PNG, tỉ lệ, độ lệch" },
    { frame: "alt", span: [B, D], guard: "không tìm thấy mẫu kính" },
    { r: 1, m: [S, B], t: "Báo \"Không tìm thấy mẫu kính\"" },
    { else: "tìm thấy" },
    { m: [S, I], t: "Đọc ảnh PNG, xác định\ntâm tròng kính (cache)" },
    { end: 1 },
    { frame: "loop", span: [K, D], guard: "mỗi ~40 ms khi cửa sổ còn mở và không chờ phản hồi" },
    { m: [B, S], t: "Gửi khung hình JPEG" },
    { m: [S, I], t: "Giải mã, lật ảnh soi gương" },
    { frame: "opt", span: [S, I], guard: "thiếu sáng" },
    { self: I, t: "Chuẩn hóa sáng (CLAHE)" },
    { end: 1 },
    { frame: "opt", span: [S, I], guard: "đến lượt nhận diện" },
    { self: I, t: "MediaPipe tìm điểm mắt\ntrong vùng quanh mặt" },
    { end: 1 },
    { frame: "alt", span: [K, I], guard: "có mặt hoặc mất mặt < 3 lần liên tiếp" },
    { self: I, t: "Làm mượt, biến đổi affine,\nalpha blend dán kính" },
    { r: 1, m: [I, S], t: "Khung hình đã ghép kính" },
    { r: 1, m: [S, B], t: "Cờ 1 + ảnh JPEG" },
    { r: 1, m: [B, K], t: "Hiển thị hình đeo kính" },
    { else: "mất mặt ≥ 3 lần liên tiếp" },
    { self: S, t: "Reset bộ làm mượt" },
    { r: 1, m: [S, B], t: "Cờ 0 + khung gốc" },
    { r: 1, m: [B, K], t: "Cảnh báo \"Không phát hiện khuôn mặt\"" },
    { end: 1 },
    { frame: "opt", span: [K, D], guard: "khách chọn mẫu kính khác" },
    { m: [K, B], t: "Chọn mẫu kính khác" },
    { m: [B, S], t: "Gửi mẫu kính mới" },
    { m: [S, D], t: "Lấy thông tin mẫu kính" },
    { r: 1, m: [D, S], t: "Thông tin mẫu kính" },
    { end: 1 },
    { end: 1 },
    { m: [K, B], t: "Đóng cửa sổ thử kính" },
    { self: B, t: "Dừng timer, tắt camera" },
    { m: [B, S], t: "Đóng kết nối WebSocket" },
    { m: [S, I], t: "Giải phóng bộ nhận diện" },
    { end: 1 },
    { end: 1 },
  ],
};

const file = process.argv[2];
let xml = fs.readFileSync(file, "utf8");
for (const spec of [seq6, seq11]) {
  const re = new RegExp(`<diagram id="${spec.id}"[\\s\\S]*?</diagram>`);
  if (!re.test(xml)) throw new Error("khong thay trang " + spec.id);
  const built = build(spec);
  xml = xml.replace(re, () => built);
}
fs.writeFileSync(file, xml);
console.log("OK");
