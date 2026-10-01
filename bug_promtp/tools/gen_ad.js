// Sinh cac trang Activity Diagram (AD-00, AD-02, AD-03) cung style voi trang AD-01
const fs = require("fs");

const ST = {
  lane: "swimlane;startSize=30;html=1;collapsible=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;fontSize=11;fontFamily=Helvetica;",
  act: "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;fontSize=9;fontFamily=Helvetica;",
  db: "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;fontSize=9;fontFamily=Helvetica;",
  dec: "rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;fontSize=9;fontFamily=Helvetica;",
  merge: "rhombus;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;",
  start: "ellipse;fillColor=#000000;strokeColor=#000000;",
  end: "ellipse;html=1;shape=endState;fillColor=#000000;strokeColor=#000000;verticalLabelPosition=bottom;verticalAlign=top;labelPosition=center;align=center;fontSize=8;fontFamily=Helvetica;",
  bar: "rounded=0;html=1;fillColor=#000000;strokeColor=#000000;",
  note: "shape=note;whiteSpace=wrap;html=1;size=14;align=left;verticalAlign=top;spacing=6;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;fontSize=9;fontFamily=Helvetica;",
  edge: "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#000000;strokeWidth=1.5;endArrow=classic;fontSize=9;labelBackgroundColor=#FFFFFF;",
};
const SIZE = {
  act: [170, 45], db: [170, 45], dec: [140, 64], merge: [30, 30], start: [30, 30], end: [30, 30],
};
const SIDE = { l: [0, 0.5], r: [1, 0.5], t: [0.5, 0], b: [0.5, 1] };

const esc = (t) => String(t)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;")
  .replace(/\n/g, "&lt;br&gt;");

function page(spec) {
  const { id, name, lanes, rowH = 72, top = 95 } = spec;
  const out = [];
  let x = 40;
  const laneGeo = lanes.map((l) => { const g = { x, w: l.w, cx: x + l.w / 2 }; x += l.w; return g; });
  const rows = Math.max(...spec.nodes.map((n) => n.row)) + 1;
  const laneH = top + rows * rowH;
  lanes.forEach((l, i) => out.push(
    `<mxCell id="${id}_lane${i}" value="${esc("<b>" + l.name + "</b>")}" style="${ST.lane}" vertex="1" parent="1"><mxGeometry x="${laneGeo[i].x}" y="40" width="${l.w}" height="${laneH}" as="geometry" /></mxCell>`));
  const pos = {};
  for (const n of spec.nodes) {
    const g = laneGeo[n.lane];
    let [w, h] = n.size || SIZE[n.t] || [0, 0];
    if (n.t === "bar") { w = n.w || g.w - 40; h = 6; }
    const cx = g.cx + (n.dx || 0);
    const cy = top + 20 + n.row * rowH + rowH / 2 - 20;
    const nx = Math.round(cx - w / 2), ny = Math.round(cy - h / 2);
    pos[n.id] = { cx, cy, w, h, x: nx, y: ny };
    out.push(`<mxCell id="${id}_${n.id}" value="${esc(n.v || "")}" style="${ST[n.t]}" vertex="1" parent="1"><mxGeometry x="${nx}" y="${ny}" width="${w}" height="${h}" as="geometry" /></mxCell>`);
  }
  spec.edges.forEach((e, i) => {
    const [s, t, o = {}] = e;
    if (!pos[s] || !pos[t]) throw new Error(`${id}: canh ${s}->${t} tro toi node khong ton tai`);
    let st = ST.edge;
    if (o.ex) st += `exitX=${SIDE[o.ex][0]};exitY=${SIDE[o.ex][1]};exitDx=0;exitDy=0;`;
    if (o.en) st += `entryX=${SIDE[o.en][0]};entryY=${SIDE[o.en][1]};entryDx=0;entryDy=0;`;
    // pts: danh sach [x, y]; x/y co the la chuoi "cx:<node>+dx" de tinh theo node
    const res = (v) => {
      if (typeof v === "number") return v;
      const m = /^(cx|cy|lx|rx|ty|by):(\w+)([+-]\d+)?$/.exec(v);
      const p = pos[m[2]]; const d = Number(m[3] || 0);
      return { cx: p.cx, cy: p.cy, lx: p.x, rx: p.x + p.w, ty: p.y, by: p.y + p.h }[m[1]] + d;
    };
    const pts = (o.pts || []).map(([px, py]) => `<mxPoint x="${res(px)}" y="${res(py)}" />`).join("");
    out.push(`<mxCell id="${id}_e${i}" value="${esc(o.label || "")}" style="${st}" edge="1" parent="1" source="${id}_${s}" target="${id}_${t}"><mxGeometry relative="1" as="geometry">${pts ? `<Array as="points">${pts}</Array>` : ""}</mxGeometry></mxCell>`);
  });
  const pw = x + 40, ph = 40 + laneH + 60;
  return `  <diagram id="${id}" name="${name}">
    <mxGraphModel dx="1200" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="${pw}" pageHeight="${ph}" background="#FFFFFF" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        ${out.join("\n        ")}
      </root>
    </mxGraphModel>
  </diagram>`;
}

// ============================ AD-00 TONG QUAN ============================
const ad00 = {
  id: "ad-00-tongquan", name: "AD-00 Tong quan - Thu kinh, Mua hang, Danh gia",
  lanes: [{ name: "Khách hàng", w: 420 }, { name: "Hệ thống", w: 380 }],
  nodes: [
    { id: "s", t: "start", lane: 0, row: 0 },
    { id: "a1", t: "act", lane: 0, row: 1, v: "Xem / tìm kiếm sản phẩm kính\n(trang chủ, tìm kiếm, yêu thích, chi tiết)", size: [200, 45] },
    { id: "d1", t: "dec", lane: 0, row: 2, v: "Có ảnh AR và\nmuốn thử kính?" },
    { id: "a2", t: "act", lane: 0, row: 3, v: "Bấm \"TRY ON\"" },
    { id: "a3", t: "act", lane: 1, row: 4, v: "Thử kính ảo thời gian thực:\nmở camera, ghép kính lên mặt\n(chi tiết AD-03)", size: [190, 52] },
    { id: "a4", t: "act", lane: 0, row: 5, v: "Đổi mẫu kính để so sánh,\nđóng cửa sổ thử kính" },
    { id: "d2", t: "dec", lane: 0, row: 6, v: "Ưng mẫu kính?" },
    { id: "x1", t: "end", lane: 0, row: 6, dx: 150, v: "Rời đi" },
    { id: "m1", t: "merge", lane: 0, row: 7 },
    { id: "a5", t: "act", lane: 0, row: 8, v: "Thêm vào giỏ hàng,\nthanh toán (chi tiết AD-01)" },
    { id: "a6", t: "act", lane: 1, row: 9, v: "Tạo đơn hàng\n(status = DELIVERED)", size: [190, 45] },
    { id: "a7", t: "act", lane: 0, row: 10, v: "Xem \"Đơn hàng của tôi\"\n(có thể hủy đơn - AD-05)" },
    { id: "d3", t: "dec", lane: 0, row: 11, v: "Đơn đã bị hủy?" },
    { id: "x2", t: "end", lane: 0, row: 11, dx: 150, v: "Không được\nđánh giá" },
    { id: "d4", t: "dec", lane: 0, row: 12, v: "Muốn bình luận,\nđánh giá?" },
    { id: "x3", t: "end", lane: 0, row: 12, dx: 150, v: "Kết thúc" },
    { id: "a8", t: "act", lane: 0, row: 13, v: "Bấm \"Đánh giá\" ở dòng\nsản phẩm trong đơn" },
    { id: "a9", t: "act", lane: 0, row: 14, v: "Chấm sao, viết bình luận,\nđính kèm ảnh/video, bấm Gửi" },
    { id: "a10", t: "act", lane: 1, row: 15, v: "Kiểm tra điều kiện, AI gán nhãn\ncảm xúc, lưu Review (AD-02)", size: [190, 45] },
    { id: "a11", t: "act", lane: 1, row: 16, v: "Hiển thị bình luận + thống kê\nsao / cảm xúc", size: [190, 45] },
    { id: "e", t: "end", lane: 1, row: 17, v: "Bình luận hiển thị" },
  ],
  edges: [
    ["s", "a1"], ["a1", "d1"],
    ["d1", "a2", { label: "[Có]" }],
    ["d1", "m1", { label: "[Không]", ex: "l", en: "l", pts: [["lx:a1-20", "cy:d1"], ["lx:a1-20", "cy:m1"]] }],
    ["a2", "a3", { ex: "r", en: "t" }], ["a3", "a4", { ex: "b", en: "r" }], ["a4", "d2"],
    ["d2", "m1", { label: "[Ưng]" }],
    ["d2", "x1", { label: "[Không]", ex: "r", en: "l" }],
    ["m1", "a5"], ["a5", "a6", { ex: "r", en: "t" }], ["a6", "a7", { ex: "b", en: "r" }], ["a7", "d3"],
    ["d3", "x2", { label: "[CANCELLED]", ex: "r", en: "l" }],
    ["d3", "d4", { label: "[DELIVERED]" }],
    ["d4", "x3", { label: "[Không]", ex: "r", en: "l" }],
    ["d4", "a8", { label: "[Có]" }], ["a8", "a9"],
    ["a9", "a10", { ex: "r", en: "t" }], ["a10", "a11"], ["a11", "e"],
  ],
};

// ============================ AD-02 DANH GIA ============================
const ad02 = {
  id: "ad-02-danhgia", name: "AD-02 Binh luan - Danh gia san pham", rowH: 86,
  lanes: [{ name: "Khách hàng", w: 290 }, { name: "Hệ thống Web", w: 330 },
          { name: "Mô hình AI (phân loại cảm xúc)", w: 260 }, { name: "CSDL / Lưu trữ file", w: 290 }],
  nodes: [
    { id: "s", t: "start", lane: 0, row: 0 },
    { id: "b1", t: "act", lane: 0, row: 1, v: "Bấm \"Đánh giá\" ở Đơn hàng của tôi\nhoặc mở trang chi tiết sản phẩm", size: [200, 45] },
    { id: "d1", t: "dec", lane: 1, row: 2, v: "Đã đăng nhập?" },
    { id: "x0", t: "end", lane: 1, row: 2, dx: 125, v: "Chỉ xem\nbình luận" },
    { id: "b3", t: "db", lane: 3, row: 3, v: "Lấy dòng đơn (OrderItem) cùng\nsản phẩm, đơn DELIVERED,\nchưa có đánh giá", size: [190, 52] },
    { id: "b4", t: "act", lane: 1, row: 4, v: "Chọn dòng đơn theo ?item=\nhoặc dòng mới nhất" },
    { id: "d2", t: "dec", lane: 1, row: 5, v: "Có dòng đơn\nđủ điều kiện?" },
    { id: "x1", t: "end", lane: 1, row: 5, dx: 125, v: "Không hiện\nform" },
    { id: "b5", t: "act", lane: 1, row: 6, v: "Hiển thị form bình luận\n+ danh sách bình luận cũ" },
    { id: "b6", t: "act", lane: 0, row: 7, v: "Chọn 1-5 sao, viết nội dung,\ntùy chọn ẩn danh, đính kèm\n≤ 5 ảnh/video, bấm Gửi", size: [190, 55] },
    { id: "d3", t: "dec", lane: 1, row: 8, v: "Dòng đơn thuộc\nngười dùng?" },
    { id: "x2", t: "end", lane: 1, row: 8, dx: 125, v: "404" },
    { id: "d4", t: "dec", lane: 1, row: 9, v: "Đơn còn\nDELIVERED?" },
    { id: "x3", t: "end", lane: 1, row: 9, dx: 125, v: "Lỗi: đơn đã hủy" },
    { id: "d5", t: "dec", lane: 1, row: 10, v: "Dòng đơn đã\nđược đánh giá?" },
    { id: "x4", t: "end", lane: 1, row: 10, dx: 125, v: "Lỗi: đã đánh giá" },
    { id: "d6", t: "dec", lane: 1, row: 11, v: "Form hợp lệ?\n(1-5 sao, có nội dung)", size: [150, 70] },
    { id: "ai1", t: "act", lane: 2, row: 12, v: "Làm sạch văn bản,\ntách từ tiếng Việt" },
    { id: "ai2", t: "act", lane: 2, row: 13, v: "TF-IDF + Logistic Regression\n→ nhãn POS/NEU/NEG\n+ độ tin cậy", size: [180, 55] },
    { id: "sv1", t: "db", lane: 3, row: 14, v: "Lưu Review\n(kèm nhãn cảm xúc)" },
    { id: "d7", t: "dec", lane: 1, row: 15, v: "Có file\nđính kèm?" },
    { id: "sv2", t: "db", lane: 3, row: 16, v: "Lưu file +\nbản ghi ReviewMedia" },
    { id: "d8", t: "dec", lane: 3, row: 17, v: "Còn file và\nchưa đủ 5?" },
    { id: "m1", t: "merge", lane: 1, row: 18 },
    { id: "b13", t: "act", lane: 1, row: 19, v: "Báo \"Cảm ơn bạn đã đánh giá\",\nquay lại mục #danh-gia", size: [190, 45] },
    { id: "b14", t: "act", lane: 1, row: 20, v: "Tính lại điểm trung bình, phân bố\nsao, tỉ lệ cảm xúc; hiển thị bình luận", size: [210, 45] },
    { id: "e", t: "end", lane: 1, row: 21, v: "Bình luận hiển thị" },
    { id: "n1", t: "note", lane: 0, row: 17, size: [250, 150], v: "Ghi chú:\n- Mỗi dòng sản phẩm của mỗi đơn (OrderItem) chỉ đánh giá 1 lần. Mua lại ở đơn khác được đánh giá thêm.\n- Nhãn cảm xúc do mô hình AI gán, người dùng không tự chọn.\n- File thứ 6 trở đi bị bỏ qua." },
  ],
  edges: [
    ["s", "b1"], ["b1", "d1", { ex: "r", en: "t" }],
    ["d1", "x0", { label: "[Chưa]", ex: "r", en: "l" }],
    ["d1", "b3", { label: "[Rồi]", ex: "b", en: "t", pts: [["cx:d1", "ty:b3-15"], ["cx:b3", "ty:b3-15"]] }],
    ["b3", "b4", { ex: "b", en: "t", pts: [["cx:b3", "ty:b4-15"], ["cx:b4", "ty:b4-15"]] }],
    ["b4", "d2"],
    ["d2", "x1", { label: "[Không]", ex: "r", en: "l" }],
    ["d2", "b5", { label: "[Có]" }],
    ["b5", "b6", { ex: "b", en: "r", pts: [["cx:b5", "cy:b6"]] }],
    ["b6", "d3", { ex: "b", en: "l", pts: [["cx:b6", "cy:d3"]] }],
    ["d3", "x2", { label: "[Không]", ex: "r", en: "l" }],
    ["d3", "d4", { label: "[Có]" }],
    ["d4", "x3", { label: "[CANCELLED]", ex: "r", en: "l" }],
    ["d4", "d5", { label: "[Có]" }],
    ["d5", "x4", { label: "[Rồi]", ex: "r", en: "l" }],
    ["d5", "d6", { label: "[Chưa]" }],
    ["d6", "b6", { label: "[Không hợp lệ]", ex: "l", en: "l", pts: [["lx:b6-20", "cy:d6"], ["lx:b6-20", "cy:b6"]] }],
    ["d6", "ai1", { label: "[Hợp lệ]", ex: "r", en: "t", pts: [["cx:ai1", "cy:d6"]] }],
    ["ai1", "ai2"],
    ["ai2", "sv1", { ex: "b", en: "t", pts: [["cx:ai2", "ty:sv1-15"], ["cx:sv1", "ty:sv1-15"]] }],
    ["sv1", "d7", { ex: "b", en: "r", pts: [["cx:sv1", "cy:d7"]] }],
    ["d7", "sv2", { label: "[Có]", ex: "b", en: "l", pts: [["cx:d7", "cy:sv2"]] }],
    ["d7", "m1", { label: "[Không]", ex: "l", en: "l", pts: [["lx:d7-25", "cy:d7"], ["lx:d7-25", "cy:m1"]] }],
    ["sv2", "d8"],
    ["d8", "sv2", { label: "[Còn]", ex: "r", en: "r", pts: [["rx:d8+20", "cy:d8"], ["rx:d8+20", "cy:sv2"]] }],
    ["d8", "m1", { label: "[Hết]", ex: "b", en: "r", pts: [["cx:d8", "cy:m1"]] }],
    ["m1", "b13"], ["b13", "b14"], ["b14", "e"],
  ],
};

// ============================ AD-03 THU KINH ============================
const ad03 = {
  id: "ad-03-thukinh", name: "AD-03 Thu kinh ao", rowH: 70,
  lanes: [{ name: "Khách hàng", w: 290 }, { name: "Trình duyệt (tryon.js)", w: 340 },
          { name: "Server (TryOnConsumer)", w: 310 }, { name: "Xử lý ảnh (OpenCV + MediaPipe)", w: 290 }],
  nodes: [
    { id: "s", t: "start", lane: 0, row: 0 },
    { id: "c1", t: "act", lane: 0, row: 1, v: "Bấm \"TRY ON\" trên thẻ sản phẩm\nhoặc trang chi tiết", size: [200, 45] },
    { id: "c2", t: "act", lane: 1, row: 2, v: "Mở cửa sổ thử kính, đánh dấu\nmẫu kính trong danh sách", size: [190, 45] },
    { id: "d1", t: "dec", lane: 1, row: 3, v: "Được cấp\nquyền camera?" },
    { id: "x1", t: "end", lane: 1, row: 3, dx: -130, v: "Báo lỗi\ncamera" },
    { id: "c4", t: "act", lane: 1, row: 4, v: "Mở kết nối WebSocket\n/ws/tryon/" },
    { id: "c5", t: "act", lane: 2, row: 5, v: "Khởi tạo bộ nhận diện khuôn\nmặt, chuẩn hóa sáng, làm mượt", size: [190, 45] },
    { id: "d2", t: "dec", lane: 2, row: 6, v: "Có file\nmô hình?" },
    { id: "x2", t: "end", lane: 2, row: 6, dx: 120, v: "Báo lỗi,\nđóng kết nối" },
    { id: "c6", t: "act", lane: 1, row: 7, v: "Gửi lệnh chọn mẫu kính\n(select_glasses)" },
    { id: "c7", t: "act", lane: 2, row: 8, v: "Lấy mẫu kính từ CSDL, đọc ảnh\nPNG, tìm tâm 2 tròng (cache)", size: [190, 45] },
    { id: "d3", t: "dec", lane: 2, row: 9, v: "Tìm thấy\nmẫu kính?" },
    { id: "c7e", t: "act", lane: 1, row: 9, dx: 50, v: "Hiện thông báo\n\"Không tìm thấy mẫu kính\"", size: [160, 45] },
    { id: "m0", t: "merge", lane: 1, row: 10 },
    { id: "d4", t: "dec", lane: 1, row: 11, v: "Đang chờ phản\nhồi khung trước?", size: [150, 64] },
    { id: "c9", t: "act", lane: 1, row: 12, v: "Chụp khung hình, nén JPEG,\ngửi lên server (~40 ms/lần)" },
    { id: "c10", t: "act", lane: 3, row: 13, v: "Giải mã ảnh,\nlật ảnh soi gương" },
    { id: "d5", t: "dec", lane: 3, row: 14, v: "Thiếu sáng?" },
    { id: "c12", t: "act", lane: 3, row: 15, v: "Chuẩn hóa độ sáng\n(CLAHE)" },
    { id: "m1", t: "merge", lane: 3, row: 16 },
    { id: "d6", t: "dec", lane: 3, row: 17, v: "Đến lượt\nnhận diện?" },
    { id: "c14", t: "act", lane: 3, row: 18, v: "Chọn vùng quanh mặt (ROI),\nMediaPipe tìm điểm mắt", size: [180, 45] },
    { id: "m2", t: "merge", lane: 3, row: 19 },
    { id: "c15", t: "act", lane: 2, row: 20, v: "Cập nhật số lần\nmất mặt liên tiếp" },
    { id: "d7", t: "dec", lane: 2, row: 21, v: "Có mặt hoặc\nmất < 3 lần?" },
    { id: "c16", t: "act", lane: 3, row: 22, v: "Làm mượt điểm neo\n(One-Euro)" },
    { id: "c19", t: "act", lane: 2, row: 22, v: "Reset bộ làm mượt,\ngiữ khung gốc (cờ 0)" },
    { id: "c17", t: "act", lane: 3, row: 23, v: "Biến đổi affine + alpha\nblend dán kính (cờ 1)" },
    { id: "m3", t: "merge", lane: 2, row: 24 },
    { id: "c18", t: "act", lane: 2, row: 25, v: "Nén JPEG, gắn byte cờ,\ngửi về trình duyệt" },
    { id: "dc", t: "dec", lane: 1, row: 26, v: "Kết nối\nWebSocket còn?" },
    { id: "xc", t: "end", lane: 1, row: 26, dx: 125, v: "Báo mất kết nối" },
    { id: "c20", t: "act", lane: 1, row: 27, v: "Hiển thị khung hình; hiện/ẩn\ncảnh báo \"Không thấy khuôn mặt\"", size: [200, 45] },
    { id: "d8", t: "dec", lane: 0, row: 28, v: "Khách\nlàm gì?" },
    { id: "c21", t: "act", lane: 0, row: 29, v: "Đóng cửa sổ thử kính" },
    { id: "f1", t: "bar", lane: 1, row: 30 },
    { id: "t1", t: "act", lane: 1, row: 31, dx: -105, size: [92, 40], v: "Dừng timer" },
    { id: "t2", t: "act", lane: 1, row: 31, size: [92, 40], v: "Đóng\nWebSocket" },
    { id: "t3", t: "act", lane: 1, row: 31, dx: 105, size: [92, 40], v: "Tắt camera" },
    { id: "j1", t: "bar", lane: 1, row: 32 },
    { id: "c23", t: "act", lane: 2, row: 33, v: "Giải phóng bộ nhận diện\n(disconnect)" },
    { id: "e", t: "end", lane: 2, row: 34, v: "Kết thúc phiên thử kính" },
  ],
  edges: [
    ["s", "c1"], ["c1", "c2", { ex: "b", en: "l", pts: [["cx:c1", "cy:c2"]] }], ["c2", "d1"],
    ["d1", "x1", { label: "[Không]", ex: "l", en: "r" }],
    ["d1", "c4", { label: "[Có]" }],
    ["c4", "c5", { ex: "b", en: "l", pts: [["cx:c4", "cy:c5"]] }], ["c5", "d2"],
    ["d2", "x2", { label: "[Không]", ex: "r", en: "l" }],
    ["d2", "c6", { label: "[Có]", ex: "b", en: "r", pts: [["cx:d2", "cy:c6"]] }],
    ["c6", "c7", { ex: "b", en: "l", pts: [["cx:c6", "cy:c7"]] }], ["c7", "d3"],
    ["d3", "c7e", { label: "[Không]", ex: "l", en: "r" }],
    ["d3", "m0", { label: "[Có]", ex: "b", en: "r", pts: [["cx:d3", "cy:m0"]] }],
    ["c7e", "m0", { ex: "b", en: "t", pts: [["cx:c7e", "ty:m0-12"], ["cx:m0", "ty:m0-12"]] }],
    ["m0", "d4"],
    ["d4", "m0", { label: "[Có] bỏ lượt", ex: "r", en: "r", pts: [["rx:d4+30", "cy:d4"], ["rx:d4+30", "cy:m0"]] }],
    ["d4", "c9", { label: "[Không]" }],
    ["c9", "c10", { ex: "b", en: "l", pts: [["cx:c9", "cy:c10"]] }], ["c10", "d5"],
    ["d5", "c12", { label: "[Có]" }], ["c12", "m1"],
    ["d5", "m1", { label: "[Không]", ex: "r", en: "r", pts: [["rx:d5+25", "cy:d5"], ["rx:d5+25", "cy:m1"]] }],
    ["m1", "d6"], ["d6", "c14", { label: "[Có]" }], ["c14", "m2"],
    ["d6", "m2", { label: "[Chưa]", ex: "r", en: "r", pts: [["rx:d6+25", "cy:d6"], ["rx:d6+25", "cy:m2"]] }],
    ["m2", "c15", { ex: "b", en: "r", pts: [["cx:m2", "cy:c15"]] }], ["c15", "d7"],
    ["d7", "c16", { label: "[Có]", ex: "r", en: "t", pts: [["cx:c16", "cy:d7"]] }],
    ["d7", "c19", { label: "[Mất ≥ 3 lần]" }],
    ["c16", "c17"],
    ["c17", "m3", { ex: "b", en: "r", pts: [["cx:c17", "cy:m3"]] }],
    ["c19", "m3"], ["m3", "c18"],
    ["c18", "dc", { ex: "b", en: "t", pts: [["cx:c18", "ty:dc-15"], ["cx:dc", "ty:dc-15"]] }],
    ["dc", "xc", { label: "[Mất]", ex: "r", en: "l" }],
    ["dc", "c20", { label: "[Còn]" }],
    ["c20", "d8", { ex: "b", en: "r", pts: [["cx:c20", "cy:d8"]] }],
    ["d8", "c6", { label: "[Đổi mẫu kính]", ex: "l", en: "l", pts: [["lx:c1-15", "cy:d8"], ["lx:c1-15", "cy:c6"]] }],
    ["d8", "m0", { label: "[Tiếp tục]", ex: "t", en: "l", pts: [["cx:d8", "cy:m0"]] }],
    ["d8", "c21", { label: "[Đóng]" }],
    ["c21", "f1", { ex: "r", en: "t", pts: [["cx:f1", "cy:c21"]] }],
    ["f1", "t1", { ex: "b", en: "t" }], ["f1", "t2", { ex: "b", en: "t" }], ["f1", "t3", { ex: "b", en: "t" }],
    ["t1", "j1", { ex: "b", en: "t" }], ["t2", "j1", { ex: "b", en: "t" }], ["t3", "j1", { ex: "b", en: "t" }],
    ["j1", "c23", { ex: "b", en: "l", pts: [["cx:j1", "cy:c23"]] }], ["c23", "e"],
  ],
};

module.exports = { pages: [ad00, ad02, ad03].map(page) };
if (require.main === module) {
  const file = process.argv[2];
  let xml = fs.readFileSync(file, "utf8");
  // Xoa cac trang cu cung id (chay lai script khong bi nhan doi)
  for (const id of ["ad-00-tongquan", "ad-02-danhgia", "ad-03-thukinh"]) {
    xml = xml.replace(new RegExp(`\\s*<diagram id="${id}"[\\s\\S]*?</diagram>`), "");
  }
  const pages = module.exports.pages;
  // AD-00 dat truoc AD-01, AD-02/AD-03 dat sau
  xml = xml.replace(/(<mxfile[^>]*>)/, `$1\n${pages[0]}`);
  xml = xml.replace(/<\/mxfile>\s*$/, `${pages[1]}\n${pages[2]}\n</mxfile>\n`);
  fs.writeFileSync(file, xml);
  console.log("OK", file);
}
