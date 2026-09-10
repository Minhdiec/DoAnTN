r"""
Prototype thu kinh ao qua webcam - GIAI DOAN 2 + BUOC 1 (ghep PNG that) +
BUOC A (tu dong can kinh 2 diem neo) + BANG CHON KINH cot doc (muc 20/22
CLAUDE_PROGRESS.md) cua PROMPT_VirtualTryOn_ClaudeCode.md.
Xem CLAUDE_PROGRESS.md muc 11 (Buoc 1), muc 13 (Buoc A), muc 20+22 (bang chon).

Bang chon kinh (muc 20, doi bo cuc o muc 22): quet thu muc
media/tryon/glasses/, gom cac file "_f.png" thanh danh sach mau kinh (SO
LUONG TU DONG theo so anh co san, khong hard-code), ve thanh 1 COT DOC sat
canh PHAI khung hinh webcam - xem class GlassesPicker. Chon mau bang phim so
1-9, click chuot vao o thumbnail, hoac di chuyen o dang chon bang phim
len/xuong (hay w/s) - cuon toan cot bang lan chuot. Ap dung NGAY khung hinh
ke tiep, khong can khoi dong lai chuong trinh. Neu thu muc rong, hien thong
bao "Chua co mau kinh", khong crash.

Muc tieu Giai doan 2: CHUNG MINH thuat toan chay dung va muot TRUOC KHI tich
hop vao Django. Buoc 1: ghep anh kinh PNG THAT (nen trong suot) thay vi kinh
ve tay. Buoc A (muc 13): THAY the chinh tay width_ratio/vertical_offset bang
CO CHE TU DONG - tu tim tam 2 trong kinh trong anh PNG, anh xa sang tam 2
mat tren khuon mat bang phep bien doi similarity (xoay + ty le + tinh tien),
khong can chinh tay nua. Code chinh tay CU van GIU LAI lam phuong an du
phong (xem GlassesOverlay.render_on_frame) cho truong hop khong tu tim duoc
2 tam trong dang tin cay. Chua toi uu do tre (do la Giai doan 3), chua xu ly
nghieng mat/che khuat/doi anh 3-4 (do la Giai doan 4 / Buoc B muc 13).

Pipeline 5 buoc theo dung yeu cau:
  1. OpenCV thu khung hinh tu webcam            -> cv2.VideoCapture
  2. OpenCV chuan hoa anh sang (CLAHE)          -> class LightNormalizer
  3. MediaPipe Face Mesh nhan dien landmark     -> class FaceMeshDetector
     + uoc luong "head pose" don gian (vi tri, kich thuoc, goc nghieng)
       tu 2 diem khoe mat ngoai (chua tinh yaw/pitch day du - de danh cho
       Giai doan 4 khi xu ly nghieng mat 3/4)
  4. OpenCV bien doi + alpha-blend anh kinh PNG -> class GlassesOverlay,
     chon mau kinh dang dung -> class GlassesPicker
  5. Hien thi ket qua                           -> cv2.imshow (cua so OpenCV)

Chay thu (PowerShell, tu thu muc goc project):
    .\.venv\Scripts\python.exe prototype\tryon_demo.py
    .\.venv\Scripts\python.exe prototype\tryon_demo.py --max-seconds 15   (tu thoat sau 15s, de do FPS qua console)
    .\.venv\Scripts\python.exe prototype\tryon_demo.py --glasses-png "media\tryon\glasses\Vanta 02_f.png"   (kieu cu: 1 anh don, bo qua bang chon)

Phim tat trong cua so video:
    q            thoat
    1..9         chon nhanh mau kinh o vi tri tuong ung dang hien trong cot
    len / xuong  (hoac w / s) doi o dang chon len/xuong, tu cuon theo neu can
    lan chuot    cuon ca cot len/xuong (khong doi mau dang chon)
    (hoac click chuot truc tiep vao o thumbnail muon chon)
    + / -        tang / giam width_ratio (CHI dung khi o CHE DO DU PHONG - xem HUD)
    ] / [        tang / giam vertical_offset (CHI dung khi o CHE DO DU PHONG)
    p            in gia tri width_ratio/vertical_offset hien tai ra console
"""

import argparse
import glob
import math
import os
import sys
import time
from collections import deque

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision


class LightNormalizer:
    """Chuan hoa anh sang bang CLAHE (Contrast Limited Adaptive Histogram
    Equalization) tren kenh L cua khong gian mau LAB.

    Vi sao dung CLAHE thay vi can bang histogram thong thuong (cv2.equalizeHist):
    CLAHE chia anh thanh cac o nho va can bang rieng tung o, kem gioi han do
    tuong phan (clip limit) de khong lam "chay" nhieu qua muc. Nho vay no tang
    do tuong phan cuc bo (giup lo ro net mat khi thieu sang) nhung khong lam
    hong nhung vung da du sang san - phu hop lam buoc tien xu ly truoc khi
    dua vao MediaPipe.
    """

    def __init__(self, clip_limit: float = 2.0, tile_grid_size=(8, 8), dark_threshold: float = 90.0):
        self._clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        # nguong do sang trung binh (thang 0-255) de coi la "thieu sang" - dung
        # o Giai doan 4 khi can quyet dinh co canh bao nguoi dung hay khong
        self.dark_threshold = dark_threshold

    def mean_brightness(self, frame_bgr: np.ndarray) -> float:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        return float(gray.mean())

    def is_low_light(self, frame_bgr: np.ndarray) -> bool:
        return self.mean_brightness(frame_bgr) < self.dark_threshold

    def normalize(self, frame_bgr: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        l_eq = self._clahe.apply(l_channel)
        lab_eq = cv2.merge((l_eq, a_channel, b_channel))
        return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)


class FaceMeshDetector:
    """Boc lai mediapipe.tasks.python.vision.FaceLandmarker (Tasks API moi -
    xem CLAUDE_PROGRESS.md muc 2 quyet dinh #6: KHONG dung mp.solutions.face_mesh
    vi ban mediapipe moi da xoa hoan toan API cu do).

    Dung che do RunningMode.VIDEO (khong phai IMAGE) de MediaPipe tu bam vet
    (tracking) giua cac khung hinh thay vi detect lai tu dau moi frame - day
    la mot trong nhung ky thuat toi uu do tre quan trong ma de bai yeu cau
    (Giai doan 3), nhung bat no ngay tu dau vi no khong ton them cong sua code
    sau nay.
    """

    # Chi so landmark trong luoi 478 diem cua MediaPipe Face Landmarker.
    # Dung 2 khoe mat NGOAI (outer corner) de tinh vi tri/kich thuoc/goc nghieng -
    # day la ky thuat pho bien trong cac du an AR glasses try-on tren GitHub vi
    # 2 diem nay on dinh, it bi bien dang khi nhay bieu cam so voi vi du diem
    # duoi mi mat.
    RIGHT_EYE_OUTER = 33   # mat phai cua NGUOI (anatomical), khong phai cua man hinh
    LEFT_EYE_OUTER = 263   # mat trai cua NGUOI (anatomical)

    def __init__(self, model_path: str, num_faces: int = 1):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Khong tim thay file model MediaPipe tai: {model_path}\n"
                "Kiem tra file prototype/models/face_landmarker.task co ton tai khong."
            )
        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_faces=num_faces,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = mp_vision.FaceLandmarker.create_from_options(options)
        self._last_timestamp_ms = -1

    def detect(self, frame_bgr: np.ndarray, timestamp_ms: int):
        # Che do VIDEO bat buoc timestamp tang dan nghiem ngat, neu khong se
        # nem ra loi. Ep tang toi thieu 1ms de phong truong hop 2 frame lien
        # tiep co cung gia tri timestamp lam tron (video qua nhanh).
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        return self._landmarker.detect_for_video(mp_image, timestamp_ms)

    @classmethod
    def get_eye_anchor_points(cls, result, frame_width: int, frame_height: int):
        """Tra ve (diem_mat_a, diem_mat_b) toa do pixel, hoac None neu khong
        phat hien duoc mat nao. Giai doan nay coi "co landmark tra ve" = "co
        mat" (bai toan do tin cay chi tiet hon danh cho Giai doan 4)."""
        if not result.face_landmarks:
            return None
        landmarks = result.face_landmarks[0]
        lm_a = landmarks[cls.RIGHT_EYE_OUTER]
        lm_b = landmarks[cls.LEFT_EYE_OUTER]
        # landmark cua MediaPipe la toa do CHUAN HOA (0..1), phai nhan lai
        # voi kich thuoc anh de ra toa do pixel that
        pt_a = (lm_a.x * frame_width, lm_a.y * frame_height)
        pt_b = (lm_b.x * frame_width, lm_b.y * frame_height)
        return pt_a, pt_b

    def close(self):
        self._landmarker.close()


class GlassesOverlay:
    """Ghep anh kinh PNG (nen trong suot, RGBA) len khuon mat.

    CO CHE CHINH (Buoc A - muc 13 CLAUDE_PROGRESS.md): TU DONG can kinh bang
    2 DIEM NEO = TAM 2 TRONG KINH trong anh PNG, anh xa sang TAM 2 MAT tren
    khuon mat (method render_on_frame_auto). Tu 2 cap diem (trong-trai <->
    mat-X, trong-phai <-> mat-Y) suy ra DUY NHAT mot phep bien doi
    similarity (xoay deu + ty le deu + tinh tien, KHONG lat guong) bang cong
    thuc so phuc - xem _similarity_matrix_2pt. Khong con can chinh tay
    width_ratio/vertical_offset nua vi ty le va vi tri suy ra thang tu
    khoang cach/goc giua 2 tam trong so voi 2 tam mat.

    Tim tam trong tu dong (_find_lens_anchors) ho tro 2 kieu anh kinh khac
    nhau da kiem chung thuc te tren anh mau (xem CLAUDE_PROGRESS.md muc 13):
      (a) Gong kim loai/rimless mong: trong kinh la vung THAT SU TRONG SUOT
          (alpha=0) duoc gong bao kin -> phat hien bang contour hierarchy
          (lo = child contour cua duong vien ngoai silhouette).
      (b) Kinh gong day, trong nhuom mau: trong kinh la vung DUC (alpha=255)
          nhung SANG MAU HON gong -> phat hien bang Otsu threshold do sang
          BEN TRONG silhouette, phan biet lop "gong" (luon cham sat duong
          vien ngoai vi no CHINH LA duong vien) voi lop "trong" (bi gong
          bao boc, khong cham vien ngoai).

    CO CHE DU PHONG (Buoc 1 cu - GIU NGUYEN, method render_on_frame): neu
    KHONG tim duoc 2 tam trong dang tin cay (gong qua manh, render qua phuc
    tap, anh PNG khong phai kinh...) thi tu dong quay lai phuong phap CHINH
    TAY cu bang 1 diem neo (tam bbox alpha) + width_ratio/vertical_offset
    (co the chinh nhanh bang phim +/-/[/ ] nhu Buoc 1). Khong xoa code cu.

    2 tham so hieu chinh CHE DO DU PHONG, KHONG hard-code, truyen tu ben
    ngoai (CLI o main()):
      - width_ratio: be rong kinh hien thi = eye_distance * width_ratio, voi
        eye_distance la khoang cach 2 khoe mat ngoai (landmark 33/263) do
        duoc tren khuon mat that. Vi kinh (tinh ca gong) luon rong hon
        khoang cach 2 khoe mat ngoai nen ty le nay thuong > 1.0.
      - vertical_offset: do lech doc cua tam kinh so voi TRUNG DIEM 2 khoe
        mat, tinh theo TY LE cua eye_distance (khong phai pixel co dinh) de
        gia tri hieu chinh dung nguyen khi khuon mat lai/gan camera (anh to/
        nho khac nhau). Duong = xuong duoi.
      - Ca 2 so co the chinh nhanh bang phim khi dang chay (xem main()):
        '+'/'-' chinh width_ratio, ']'/'[' chinh vertical_offset, 's' in ra
        console gia tri hien tai de dan lai lam mac dinh moi.

    Tam neo (anchor) trong anh PNG = TAM BBOX cua vung KHONG trong suot
    (alpha > 0), tu dong tinh khi nap anh - khong gia dinh anh doi xung qua
    tam canvas nhu ban ve demo cu, nen dung duoc voi bat ky anh PNG that nao
    (co the co le/khong can chinh giua khi xuat file).

    Ky thuat PREMULTIPLIED ALPHA khi resize/xoay: neu resize/warpAffine truc
    tiep tren anh RGBA thong thuong, noi suy bilinear o cac diem sat vien se
    tron mau RGB cua vung TRONG SUOT (alpha=0, thuong con sot mau den/trang
    ray tu buoc tach nen) VAO mau RGB vung DUC ke ben, tao thanh VIEN MAU la
    (fringing/halo) quanh kinh sau khi blend - loi rat pho bien voi PNG tach
    nen that (anh demo ve tay cu khong bi vi mau nen luon la (0,0,0,0) dong
    bo voi RGB=0). Premultiply RGB voi alpha TRUOC khi resize/xoay giai
    quyet dut diem: vung trong suot luon co RGB=(0,0,0) dong bo voi alpha=0
    nen phep noi suy tuyen tinh tren ca 4 kenh van cho ra ket qua dung, khong
    can buoc "un-premultiply" nao them (cong thuc blend "over" chuan cho anh
    premultiplied: out = src_premult + dst*(1-alpha)).
    """

    def __init__(self, png_path: str = None, width_ratio: float = 1.6, vertical_offset: float = 0.0):
        self.width_ratio = width_ratio
        self.vertical_offset = vertical_offset
        self._image_premult = None  # BGRA, kenh BGR da premultiply voi alpha
        self._anchor_x = None
        self._anchor_y = None
        self._src_width = None
        self._lens_left = None   # tam trong trai (Buoc A) - None = dung che do du phong
        self._lens_right = None

        if png_path:
            if not os.path.exists(png_path):
                print(f"CANH BAO: khong tim thay anh kinh tai '{png_path}'. Dung kinh demo ve bang code thay the.")
                self._set_image(self._draw_demo_glasses(), detect_lens_anchors=False)
                return
            try:
                raw = cv2.imread(png_path, cv2.IMREAD_UNCHANGED)
                if raw is None:
                    raise ValueError("cv2.imread tra ve None (file hong hoac sai dinh dang anh)")
                if raw.ndim != 3 or raw.shape[2] != 4:
                    raise ValueError(f"Anh khong co kenh alpha (shape={raw.shape}) - can PNG RGBA nen trong suot")
                self._set_image(raw)
                print(f"Da nap anh kinh that: {png_path} ({raw.shape[1]}x{raw.shape[0]}px)")
            except Exception as e:
                print(f"CANH BAO: loi doc anh kinh '{png_path}' ({e}). Dung kinh demo ve bang code thay the.")
                self._set_image(self._draw_demo_glasses(), detect_lens_anchors=False)
        else:
            self._set_image(self._draw_demo_glasses(), detect_lens_anchors=False)

    def _draw_demo_glasses(self) -> np.ndarray:
        """Kinh demo ve bang code - CHI dung khi khong co/khong doc duoc PNG
        that (xem docstring class). Giu lai tu Giai doan 2 lam phuong an du
        phong, khong con la duong chinh."""
        canvas_w, canvas_h, lens_y = 400, 160, 80
        anchor_a_x, anchor_b_x = 100, 300
        img = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
        lens_color = (40, 40, 40, 160)
        frame_color = (10, 10, 10, 255)

        for cx in (anchor_a_x, anchor_b_x):
            cv2.ellipse(img, (cx, lens_y), (65, 50), 0, 0, 360, lens_color, -1)
            cv2.ellipse(img, (cx, lens_y), (65, 50), 0, 0, 360, frame_color, 6)
        cv2.line(img, (anchor_a_x + 65, lens_y - 10), (anchor_b_x - 65, lens_y - 10), frame_color, 6)
        cv2.line(img, (anchor_a_x - 65, lens_y), (0, lens_y - 5), frame_color, 6)
        cv2.line(img, (anchor_b_x + 65, lens_y), (canvas_w - 1, lens_y - 5), frame_color, 6)
        return img

    def _set_image(self, bgra: np.ndarray, detect_lens_anchors: bool = True) -> None:
        bgr = bgra[:, :, :3].astype(np.float32)
        alpha = bgra[:, :, 3:4].astype(np.float32) / 255.0
        premult_bgr = np.clip(bgr * alpha, 0, 255).astype(np.uint8)
        self._image_premult = np.dstack([premult_bgr, bgra[:, :, 3]])

        ys, xs = np.where(bgra[:, :, 3] > 0)
        if len(xs) == 0:
            raise ValueError("Kenh alpha rong toan bo - anh khong co noi dung nhin thay")
        self._anchor_x = (xs.min() + xs.max()) / 2.0
        self._anchor_y = (ys.min() + ys.max()) / 2.0
        self._src_width = max(1, xs.max() - xs.min())

        if not detect_lens_anchors:
            # Kinh demo ve bang code (_draw_demo_glasses) - khong phai anh
            # kinh that, khong can/khong nen chay dieu tra tam trong.
            self._lens_left = None
            self._lens_right = None
            return

        # Buoc A (muc 13): thu tu dong tim 2 tam trong kinh de can tu dong.
        # Neu khong tim duoc (None) thi render_on_frame_auto se tu quay lai
        # che do du phong 1-diem-neo + width_ratio o tren.
        lens_anchors = self._find_lens_anchors(bgra)
        if lens_anchors is None:
            self._lens_left = None
            self._lens_right = None
            print("CANH BAO: khong tu tim duoc 2 tam trong kinh dang tin cay trong anh nay "
                  "- dung che do du phong (chinh tay width_ratio/vertical_offset).")
        else:
            self._lens_left, self._lens_right = lens_anchors
            print(f"Da tu dong xac dinh 2 tam trong kinh: trai={self._lens_left}, phai={self._lens_right}")

    @staticmethod
    def _find_lens_anchors(bgra: np.ndarray):
        """Tu dong tim tam 2 trong kinh trong anh PNG (xem docstring class
        de biet 2 truong hop (a)/(b) duoc ho tro). Tra ve
        ((x_trai,y_trai), (x_phai,y_phai)) theo toa do TRAI/PHAI CUA ANH
        (x nho hon = trai), khong phai trai/phai giai phau nguoi doi - viec
        khop dung voi mat nao la trach nhiem cua render_on_frame_auto (tu
        chon chieu khop it xoay nhat, xem docstring o do). Tra ve None neu
        khong tim duoc 2 vung du tin cay.
        """
        alpha = bgra[:, :, 3]
        # nguong 10 (khong phai 0) de bo qua vien antialias mo cua PNG tach
        # nen (cac pixel alpha rat thap sat bien, khong phai noi dung that)
        silhouette = (alpha > 10).astype(np.uint8) * 255
        if silhouette.sum() == 0:
            return None

        contours, hierarchy = cv2.findContours(silhouette, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if hierarchy is None or len(contours) == 0:
            return None
        hierarchy = hierarchy[0]  # (N,4): next, prev, first_child, parent

        # Duong vien NGOAI lon nhat = silhouette tong the cua kinh (frame +
        # trong) - bo qua cac dom nhieu nho neu tach nen sot lai.
        outer_candidates = [i for i in range(len(contours)) if hierarchy[i][3] == -1]
        if not outer_candidates:
            return None
        outer_idx = max(outer_candidates, key=lambda i: cv2.contourArea(contours[i]))
        if cv2.contourArea(contours[outer_idx]) <= 0:
            return None
        _, _, w0, h0 = cv2.boundingRect(contours[outer_idx])
        # loc dom nhieu nho (dinh oc, logo, moi han gong...) nho hon 2% dien
        # tich bbox - khong phai trong kinh that
        min_area = (w0 * h0) * 0.02

        # ---- Truong hop (a): LO THAT (child contour cua duong vien ngoai) ----
        holes = [i for i in range(len(contours)) if hierarchy[i][3] == outer_idx]
        holes = [i for i in holes if cv2.contourArea(contours[i]) >= min_area]
        if len(holes) >= 2:
            holes.sort(key=lambda i: cv2.contourArea(contours[i]), reverse=True)
            centers = []
            for i in holes[:2]:
                m = cv2.moments(contours[i])
                if m["m00"] == 0:
                    x, y, w, h = cv2.boundingRect(contours[i])
                    centers.append((x + w / 2.0, y + h / 2.0))
                else:
                    centers.append((m["m10"] / m["m00"], m["m01"] / m["m00"]))
            centers.sort(key=lambda p: p[0])
            return centers[0], centers[1]

        # ---- Truong hop (b): trong la vung DUC sang mau hon gong (Otsu) ----
        outer_mask = np.zeros(silhouette.shape, dtype=np.uint8)
        cv2.drawContours(outer_mask, contours, outer_idx, 255, thickness=-1)
        for i in holes:  # tru cac lo that (neu co, du chua du 2 cai) khoi vung xet Otsu
            cv2.drawContours(outer_mask, contours, i, 0, thickness=-1)
        inside = outer_mask > 0
        if inside.sum() < min_area:
            return None

        gray = cv2.cvtColor(bgra[:, :, :3], cv2.COLOR_BGR2GRAY)
        vals = gray[inside]
        if vals.max() == vals.min():
            return None  # mau dong nhat toan bo vung trong - khong tach duoc gong/trong
        otsu_t, _ = cv2.threshold(vals.reshape(-1, 1).astype(np.uint8), 0, 255,
                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        class_low = inside & (gray <= otsu_t)
        class_high = inside & (gray > otsu_t)

        # Gong LUON cham sat duong vien ngoai (vi no CHINH LA duong vien) -
        # dung mot vanh mong ngay sat bien de xac dinh lop nao la gong, thay
        # vi doan "sang hon = trong" (co the sai neu la kinh mau toi/gong
        # sang mau, vi du gong bac + trong ram).
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        boundary_ring = (outer_mask > 0) & (cv2.erode(outer_mask, kernel) == 0)
        overlap_low = np.count_nonzero(class_low & boundary_ring)
        overlap_high = np.count_nonzero(class_high & boundary_ring)
        lens_mask = class_high if overlap_low >= overlap_high else class_low

        num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(
            (lens_mask.astype(np.uint8)) * 255, connectivity=8
        )
        candidates = [(i, stats[i, cv2.CC_STAT_AREA]) for i in range(1, num_labels)
                      if stats[i, cv2.CC_STAT_AREA] >= min_area]
        if len(candidates) < 2:
            return None
        candidates.sort(key=lambda t: t[1], reverse=True)
        centers = [(centroids[i][0], centroids[i][1]) for i, _ in candidates[:2]]
        centers.sort(key=lambda p: p[0])
        return centers[0], centers[1]

    @staticmethod
    def _similarity_matrix_2pt(src1, src2, dst1, dst2) -> np.ndarray:
        """Tinh ma tran affine 2x3 CHI gom xoay deu + ty le deu + tinh tien
        (KHONG lat guong/skew) sao cho src1->dst1 VA src2->dst2 dung tuyet
        doi - day la phep bien doi similarity DUY NHAT thoa 2 cap diem.

        Dung so phuc de suy cong thuc gon: coi moi diem (x,y) la so phuc
        x+iy. Voi p_dst = a*p_src + b (a,b la so phuc), thay 2 cap diem vao
        se ra he 2 phuong trinh 2 an (a,b), giai duoc:
            a = (dst2-dst1) / (src2-src1)
            b = dst1 - a*src1
        a = scale * e^{i*theta} nen |a| = ty le, arg(a) = goc xoay - dung
        chinh vector [Re(a), Im(a)] lam 2 hang dau ma tran xoay-ty le chuan
        cua OpenCV (dang [[c,-s],[s,c]] nhan them ty le).
        """
        src1c, src2c = complex(*src1), complex(*src2)
        dst1c, dst2c = complex(*dst1), complex(*dst2)
        a = (dst2c - dst1c) / (src2c - src1c)
        b = dst1c - a * src1c
        return np.array([
            [a.real, -a.imag, b.real],
            [a.imag, a.real, b.imag],
        ], dtype=np.float32)

    def render_on_frame_auto(self, frame_bgr: np.ndarray, eye_a, eye_b) -> np.ndarray:
        """Duong CHINH (Buoc A): can kinh TU DONG bang 2 diem neo tam trong,
        khong can width_ratio/vertical_offset. Neu anh kinh khong tu tim
        duoc 2 tam trong (self._lens_left/_right la None) thi tu dong goi
        lai render_on_frame (che do du phong 1-diem-neo cu) - giu dung tinh
        than "khong xoa duong cu" cua muc 13.

        Van de can xu ly: KHONG chac chan quy uoc trai/phai trong anh PNG
        (tam trong nao la "ben trai anh") co khop huong voi trai/phai cua 2
        diem neo mat tren khuon mat da bi lat guong (cv2.flip trong main())
        hay khong - phu thuoc quy uoc chup anh san pham va thu tu landmark.
        Thay vi gia dinh cung mot chieu co dinh (de sai neu gia dinh nguoc,
        kinh se bi xoay nguoc ~180 do), TU CHON cach ghep (trong-trai<->eye_a
        hay trong-trai<->eye_b) sao cho GOC XOAY KET QUA NHO NHAT - vi kinh
        deo dung luon gan nhu thang hang voi 2 mat (chi lech theo do nghieng
        dau thuc te, khong bao gio gan 180 do), nen cach ghep dung se luon
        cho goc xoay nho hon han cach ghep sai. Cach lam nay tu dung bat ke
        quy uoc anh nguon la gi, khong can gia dinh.
        """
        if self._lens_left is None or self._lens_right is None:
            return self.render_on_frame(frame_bgr, eye_a, eye_b)

        dx, dy = eye_b[0] - eye_a[0], eye_b[1] - eye_a[1]
        if math.hypot(dx, dy) < 1e-3:
            return frame_bgr  # 2 mat trung nhau - loi nhan dien hi hu, bo qua khung hinh

        m1 = self._similarity_matrix_2pt(self._lens_left, self._lens_right, eye_a, eye_b)
        m2 = self._similarity_matrix_2pt(self._lens_left, self._lens_right, eye_b, eye_a)
        angle1 = math.atan2(m1[1, 0], m1[0, 0])
        angle2 = math.atan2(m2[1, 0], m2[0, 0])
        matrix = m1 if abs(angle1) <= abs(angle2) else m2

        frame_h, frame_w = frame_bgr.shape[:2]
        warped = cv2.warpAffine(
            self._image_premult, matrix, (frame_w, frame_h),
            flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0),
        )
        return self._alpha_blend(frame_bgr, warped, 0, 0)

    def render_on_frame(self, frame_bgr: np.ndarray, pt_a, pt_b) -> np.ndarray:
        """Co gian + xoay anh kinh sao cho tam neo (xem docstring class)
        trung dung diem tinh tu pt_a, pt_b tren khung hinh, roi alpha-blend
        len frame_bgr. Sua truc tiep tren frame_bgr va tra ve cung tham
        chieu do."""
        dx = pt_b[0] - pt_a[0]
        dy = pt_b[1] - pt_a[1]
        eye_distance = math.hypot(dx, dy)
        if eye_distance < 1e-3:
            # 2 landmark trung nhau (mat qua nho / loi nhan dien hi hu) - bo
            # qua khung hinh nay thay vi chia cho 0
            return frame_bgr

        scale = (eye_distance * self.width_ratio) / self._src_width
        angle_deg = math.degrees(math.atan2(dy, dx))

        src_h, src_w = self._image_premult.shape[:2]
        new_w = max(1, int(src_w * scale))
        new_h = max(1, int(src_h * scale))
        resized = cv2.resize(self._image_premult, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Xoay quanh TAM NEO (khong phai tam hinh chu nhat resized nua, vi
        # tam neo co the lech tam voi PNG that). Dau "-angle_deg": suy ra tu
        # cong thuc ma tran xoay cua OpenCV de vector ngang trong anh kinh
        # khop dung huong voi vector A->B do duoc tren khuon mat (da kiem
        # chung bang tinh tay o Giai doan 2, van dung nguyen ly cu).
        anchor_x_scaled = self._anchor_x * scale
        anchor_y_scaled = self._anchor_y * scale
        rot_mat = cv2.getRotationMatrix2D((anchor_x_scaled, anchor_y_scaled), -angle_deg, 1.0)
        rotated = cv2.warpAffine(
            resized, rot_mat, (new_w, new_h),
            flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0),
        )

        mid_x = (pt_a[0] + pt_b[0]) / 2.0
        mid_y = (pt_a[1] + pt_b[1]) / 2.0 + self.vertical_offset * eye_distance
        top_left_x = int(round(mid_x - anchor_x_scaled))
        top_left_y = int(round(mid_y - anchor_y_scaled))

        return self._alpha_blend(frame_bgr, rotated, top_left_x, top_left_y)

    def draw_calibration_hint(self, frame: np.ndarray) -> None:
        """Ve trang thai che do hien tai (TU DONG hay DU PHONG) len goc
        duoi-trai. Che do DU PHONG (khong tu tim duoc tam trong) moi hien
        gia tri width_ratio/vertical_offset va phim tat chinh tay - che do
        TU DONG (Buoc A) khong can chinh gi ca. (Tu muc 22, bang chon kinh
        chuyen sang cot doc canh PHAI nen goc duoi-trai nay lai trong,
        khong can nhuong cho nua.)"""
        h = frame.shape[0]
        if self._lens_left is not None and self._lens_right is not None:
            text = "Che do: TU DONG can theo tam trong kinh (khong can chinh tay)"
            color = (0, 255, 0)
        else:
            text = (f"Che do DU PHONG - width_ratio: {self.width_ratio:.2f} (+/-)   "
                    f"vertical_offset: {self.vertical_offset:.2f} ([/])   [p]=in ra console")
            color = (0, 255, 255)
        cv2.putText(frame, text, (10, h - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)

    @staticmethod
    def _alpha_blend(frame_bgr: np.ndarray, overlay_premult_bgra: np.ndarray, x: int, y: int) -> np.ndarray:
        frame_h, frame_w = frame_bgr.shape[:2]
        ov_h, ov_w = overlay_premult_bgra.shape[:2]

        # Cat phan overlay nam ngoai khung hinh (kinh bi day sat mep anh khi
        # nguoi dung dung gan mep camera) - khong lam vay se bi loi index am.
        src_x0, src_y0 = max(0, -x), max(0, -y)
        dst_x0, dst_y0 = max(0, x), max(0, y)
        dst_x1 = min(frame_w, x + ov_w)
        dst_y1 = min(frame_h, y + ov_h)
        if dst_x1 <= dst_x0 or dst_y1 <= dst_y0:
            return frame_bgr  # kinh nam hoan toan ngoai khung hinh

        src_x1 = src_x0 + (dst_x1 - dst_x0)
        src_y1 = src_y0 + (dst_y1 - dst_y0)

        roi = frame_bgr[dst_y0:dst_y1, dst_x0:dst_x1]
        overlay_crop = overlay_premult_bgra[src_y0:src_y1, src_x0:src_x1]

        alpha = overlay_crop[:, :, 3:4].astype(np.float32) / 255.0
        premult_rgb = overlay_crop[:, :, :3].astype(np.float32)
        roi_f = roi.astype(np.float32)

        # Cong thuc "over" chuan cho anh da premultiplied: khong nhan lai
        # overlay voi alpha nua vi premult_rgb da nhan san tu _set_image.
        blended = premult_rgb + roi_f * (1.0 - alpha)
        frame_bgr[dst_y0:dst_y1, dst_x0:dst_x1] = np.clip(blended, 0, 255).astype(np.uint8)
        return frame_bgr


def discover_glasses_models(glasses_dir: str):
    """Quet thu muc glasses_dir, tim cac file anh chinh dien theo quy uoc
    dat ten "<ten_mau>_f.png" cua muc 13 CLAUDE_PROGRESS.md - moi file la 1
    mau kinh, ten mau = ten file bo hau to "_f". SO LUONG mau la TU DONG
    theo so file tim duoc, KHONG hard-code (muc 20). Them mau moi = tha 1
    file dung ten vao thu muc, khong sua code. Tra ve
    list[(ten_mau, duong_dan_anh)], sap theo ten."""
    front_files = {}
    for path in glob.glob(os.path.join(glasses_dir, "*_f.png")):
        name = os.path.splitext(os.path.basename(path))[0][:-len("_f")]
        front_files[name] = path
    return [(name, front_files[name]) for name in sorted(front_files)]


class GlassesPicker:
    """Bang chon kinh hien NGAY tren cua so webcam (muc 20/22
    CLAUDE_PROGRESS.md). Nap SAN tat ca mau kinh trong entries thanh
    GlassesOverlay + 1 anh thumbnail nho (tinh 1 LAN luc khoi tao, khong
    tinh lai moi khung hinh - giu FPS on dinh), roi ve thanh 1 COT DOC sat
    canh PHAI khung hinh (muc 22 - doi tu dai ngang o day khung hinh cua
    muc 20) de nguoi dung chon bang phim so, phim len/xuong, lan chuot,
    hoac click chuot. Doi mau chi la doi self.selected_index - khong nap
    lai anh, nen ap dung NGAY khung hinh ke tiep, khong can khoi dong lai
    chuong trinh. TOAN BO logic gom mau/chon/ap kinh (models, select,
    select_visible_slot, current_overlay...) GIU NGUYEN tu muc 20, chi doi
    phan VE (draw) va CACH CUON (scroll/move_selection) sang chieu doc.

    Neu entries rong (thu muc khong co anh nao) thi self.models rong -
    draw() se chi hien 1 dong canh bao thay vi cot thumbnail, va
    current_overlay tra ve None (main() phai tu kiem tra None truoc khi
    goi render, KHONG duoc gia dinh luon co it nhat 1 mau).
    """

    COLUMN_WIDTH = 140       # be rong cot doc (px), sat canh phai khung hinh
    THUMB_MAX_HEIGHT = 60    # chieu cao toi da thumbnail trong o (giu ty le anh goc)
    LABEL_HEIGHT = 16        # cho dong chu "so_thu_tu:ten_mau" duoi thumbnail
    PADDING = 6
    CELL_HEIGHT = THUMB_MAX_HEIGHT + LABEL_HEIGHT + PADDING * 2
    TOP_MARGIN = 40          # chua ve gi o day (tranh dinh sat canh tren khung hinh)

    def __init__(self, entries):
        """entries: list[(ten_mau, duong_dan_anh_chinh_dien)], vi du tra ve
        tu discover_glasses_models() hoac tu 1 file don le (--glasses-png)."""
        self.models = []        # list[(ten_mau, GlassesOverlay)]
        self._thumbnails = []   # anh thumbnail BGR CO KICH THUOC CO DINH, CUNG THU TU voi self.models
        self.selected_index = 0
        self.scroll_offset = 0  # vi tri mau DAU TIEN dang hien trong cot (cuon bang lan chuot/mui ten)
        # Toa do (x0,y0,x1,y1,chi_so_mau) cua tung o dang ve tren khung hinh
        # GAN NHAT - cap nhat lai moi lan goi draw(), dung de bat click chuot.
        self._cell_rects = []

        for name, front_path in entries:
            try:
                overlay = GlassesOverlay(front_path)
            except Exception as e:
                print(f"CANH BAO: bo qua mau kinh '{name}' do loi nap anh ({e}).")
                continue
            self.models.append((name, overlay))
            self._thumbnails.append(self._make_thumbnail(front_path))

    @classmethod
    def _make_thumbnail(cls, png_path: str) -> np.ndarray:
        """Doc lai file PNG (rieng voi ban GlassesOverlay da nap - can anh
        RGBA GOC, chua premultiply, de ghep len nen xam cho dung mau), thu
        nho GIU NGUYEN TY LE de vua trong khung (COLUMN_WIDTH - 2*PADDING)
        x THUMB_MAX_HEIGHT ("contain" fit - khong bi meo hinh), roi dat
        CHINH GIUA 1 canvas nen xam KICH THUOC CO DINH - nho vay draw() chi
        can copy thang canvas nay vao dung vi tri, khong phai tinh toan
        offset rieng cho tung anh moi khung hinh. Chi goi 1 LAN luc khoi
        tao GlassesPicker (khong phai moi khung hinh) nen doc lai file
        khong anh huong toc do. Neu anh loi/thieu kenh alpha, tra ve canvas
        mau xam thay the (khong crash bang chon vi 1 anh hong)."""
        canvas_w = cls.COLUMN_WIDTH - cls.PADDING * 2
        canvas_h = cls.THUMB_MAX_HEIGHT
        canvas = np.full((canvas_h, canvas_w, 3), (235, 235, 235), dtype=np.uint8)

        raw = cv2.imread(png_path, cv2.IMREAD_UNCHANGED)
        if raw is None or raw.ndim != 3 or raw.shape[2] != 4:
            return canvas

        src_h, src_w = raw.shape[:2]
        scale = min(canvas_w / src_w, canvas_h / src_h)
        new_w = max(1, int(round(src_w * scale)))
        new_h = max(1, int(round(src_h * scale)))
        resized = cv2.resize(raw, (new_w, new_h), interpolation=cv2.INTER_AREA)

        alpha = resized[:, :, 3:4].astype(np.float32) / 255.0
        rgb = resized[:, :, :3].astype(np.float32)
        bg_crop = canvas[:new_h, :new_w].astype(np.float32)
        composed = rgb * alpha + bg_crop * (1.0 - alpha)

        off_x = (canvas_w - new_w) // 2
        off_y = (canvas_h - new_h) // 2
        canvas[off_y:off_y + new_h, off_x:off_x + new_w] = np.clip(composed, 0, 255).astype(np.uint8)
        return canvas

    @property
    def current_overlay(self):
        """GlassesOverlay dang duoc chon, hoac None neu khong co mau nao."""
        if not self.models:
            return None
        return self.models[self.selected_index][1]

    @property
    def current_name(self) -> str:
        if not self.models:
            return "(khong co)"
        return self.models[self.selected_index][0]

    def visible_count(self, frame_h: int) -> int:
        """So o thumbnail toi da vua chieu cao khung hinh (tru phan
        TOP_MARGIN chua o tren)."""
        return max(1, (frame_h - self.TOP_MARGIN) // self.CELL_HEIGHT)

    def select(self, index: int) -> None:
        if 0 <= index < len(self.models):
            self.selected_index = index

    def select_visible_slot(self, slot: int) -> None:
        """slot: vi tri O DANG HIEN trong cot (0 = o tren cung, tinh tu
        phim so 1-9 da tru 1) - CHUYEN sang chi so thuc trong self.models
        bang cach cong them scroll_offset, roi moi chon."""
        self.select(self.scroll_offset + slot)

    def scroll(self, delta: int, frame_h: int) -> None:
        """Cuon KHUNG NHIN delta o (am = len tren, duong = xuong duoi) MA
        KHONG doi o dang chon - dung cho lan chuot. Gioi han khong cuon qua
        dau/cuoi danh sach; neu so mau <= so o vua hien thi khong can cuon
        gi (max_offset = 0 nen scroll_offset luon o 0)."""
        if not self.models:
            return
        max_offset = max(0, len(self.models) - self.visible_count(frame_h))
        self.scroll_offset = max(0, min(self.scroll_offset + delta, max_offset))

    def move_selection(self, delta: int, frame_h: int) -> None:
        """Di chuyen O DANG CHON len/xuong 1 vi tri (phim mui ten hoac w/s -
        muc 22) - KHAC voi scroll() o cho: doi chieu doi luon lua chon, va
        TU DONG cuon khung nhin theo neu o moi chon bi khuat, de o dang
        chon luon nam trong vung nhin thay duoc."""
        if not self.models:
            return
        self.select(max(0, min(self.selected_index + delta, len(self.models) - 1)))
        visible = self.visible_count(frame_h)
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + visible:
            self.scroll_offset = self.selected_index - visible + 1

    def handle_mouse_click(self, x: int, y: int) -> None:
        """Goi tu callback cv2.setMouseCallback khi nguoi dung click chuot
        trai - do (x,y) voi cac o da ve o lan draw() gan nhat, chon mau
        tuong ung neu click trung 1 o."""
        for x0, y0, x1, y1, index in self._cell_rects:
            if x0 <= x < x1 and y0 <= y < y1:
                self.select(index)
                return

    def draw(self, frame: np.ndarray) -> None:
        """Ve COT thumbnail sat CANH PHAI khung hinh. Chi thao tac ve don
        gian (copy mang, ve hinh chu nhat/chu) tren cac anh thumbnail DA
        CACHE san (kich thuoc co dinh - xem _make_thumbnail) - khong
        resize/tinh toan gi nang moi khung hinh nen khong lam tut FPS dang
        ke."""
        frame_h, frame_w = frame.shape[:2]
        self._cell_rects = []

        if not self.models:
            cv2.putText(frame, "Chua co mau kinh nao trong thu muc media/tryon/glasses",
                        (10, frame_h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2, cv2.LINE_AA)
            return

        col_x0 = frame_w - self.COLUMN_WIDTH
        cv2.rectangle(frame, (col_x0, 0), (frame_w, frame_h), (35, 35, 35), -1)

        visible = self.visible_count(frame_h)
        for slot in range(visible):
            index = self.scroll_offset + slot
            if index >= len(self.models):
                break
            name, _ = self.models[index]
            thumb = self._thumbnails[index]

            cell_y0 = self.TOP_MARGIN + slot * self.CELL_HEIGHT
            cell_y1 = cell_y0 + self.CELL_HEIGHT

            th, tw = thumb.shape[:2]
            thumb_x0 = col_x0 + self.PADDING
            thumb_y0 = cell_y0 + self.PADDING
            frame[thumb_y0:thumb_y0 + th, thumb_x0:thumb_x0 + tw] = thumb

            is_selected = (index == self.selected_index)
            border_color = (0, 255, 0) if is_selected else (110, 110, 110)
            cv2.rectangle(frame, (col_x0 + 2, cell_y0 + 2), (frame_w - 2, cell_y1 - self.LABEL_HEIGHT - 2),
                          border_color, 2)

            label = f"{slot + 1}:{name}"
            if len(label) > 16:
                label = label[:15] + "."
            cv2.putText(frame, label, (col_x0 + 4, cell_y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

            self._cell_rects.append((col_x0, cell_y0, frame_w, cell_y1, index))

        # Mui ten bao hieu con mau o ngoai vung hien (cot dai hon so o hien duoc)
        mid_x = col_x0 + self.COLUMN_WIDTH // 2
        if self.scroll_offset > 0:
            cv2.putText(frame, "^", (mid_x - 6, self.TOP_MARGIN - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
        if self.scroll_offset + visible < len(self.models):
            cv2.putText(frame, "v", (mid_x - 6, frame_h - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)


class FPSMeter:
    """Do FPS trung binh truot (rolling average) va thoi gian xu ly khung
    hinh gan nhat (ms), ve len goc tren-trai video."""

    def __init__(self, window: int = 30):
        self._timestamps = deque(maxlen=window)

    def tick(self):
        self._timestamps.append(time.perf_counter())

    def fps(self) -> float:
        if len(self._timestamps) < 2:
            return 0.0
        span = self._timestamps[-1] - self._timestamps[0]
        if span <= 0:
            return 0.0
        return (len(self._timestamps) - 1) / span

    def last_frame_ms(self) -> float:
        if len(self._timestamps) < 2:
            return 0.0
        return (self._timestamps[-1] - self._timestamps[-2]) * 1000.0

    def draw(self, frame: np.ndarray):
        text = f"FPS: {self.fps():.1f}  |  Frame: {self.last_frame_ms():.1f} ms"
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)


def _decode_wheel_delta(flags: int) -> int:
    """Giai ma huong/do lon lan chuot tu tham so 'flags' cua su kien
    cv2.EVENT_MOUSEWHEEL (muc 22). OpenCV co ham chinh thuc
    cv2.getMouseWheelDelta(flags) cho viec nay, NHUNG ban OpenCV dang cai
    trong venv nay (5.0.0) KHONG co ham do trong phan binding Python (da tu
    kiem tra bang hasattr() truoc khi viet ham nay, khong doan). Nen phai
    tu giai ma thu cong theo dung quy uoc Win32 duoc OpenCV ke thua
    (GET_WHEEL_DELTA_WPARAM): 16 BIT CAO cua flags la 1 so nguyen 16-bit CO
    DAU - duong = lan LEN (huong ra xa nguoi dung), am = lan XUONG. Da doi
    chieu cong thuc nay voi tai lieu OpenCV chinh thuc (delta la boi so cua
    120), nhung CHUA the tu bam thu tren chuot that de kiem chung 100% vi
    moi truong nay khong co man hinh/chuot that - neu lan chuot khong hoat
    dong dung nhu mong doi khi test, dung phim len/xuong (phim mui ten
    hoac w/s, da chac chan hoat dong qua waitKeyEx) lam phuong an thay
    the, khong phu thuoc ham nay."""
    high_word = (flags >> 16) & 0xFFFF
    if high_word >= 0x8000:
        high_word -= 0x10000
    return high_word


# Ma phim mo rong (tu cv2.waitKeyEx) cho phim mui ten LEN/XUONG tren
# Windows - day la gia tri PHO BIEN duoc nhieu tai lieu/vi du OpenCV xac
# nhan, nhung co the khac nhau tuy backend GUI (Win32/Qt/GTK) nen KHONG
# chac chan 100% dung tren moi may - vi vay w/s luon di kem lam phuong an
# chac chan hoat dong (xem xu ly phim trong main()).
_ARROW_KEY_UP = 2490368
_ARROW_KEY_DOWN = 2621440


def _picker_mouse_callback(event, x, y, flags, context) -> None:
    """Callback cho cv2.setMouseCallback (muc 20/22). Nhan 'context' =
    (picker, frame_size_holder) qua tham so param cua setMouseCallback
    (KHONG dung bien toan cuc) de OpenCV tu truyen vao moi lan co su kien
    chuot:
      - Click chuot trai vao 1 o thumbnail -> chon mau kinh do.
      - Lan chuot (EVENT_MOUSEWHEEL) -> cuon cot thumbnail len/xuong.
    frame_size_holder la 1 dict {"h": chieu_cao_khung_hinh_hien_tai} - can
    de biet gioi han cuon, cap nhat moi khung hinh o vong lap chinh (chieu
    cao khung hinh webcam thuc te khong doi trong luc chay, nhung van cap
    nhat cho chac chan)."""
    picker, frame_size_holder = context
    if event == cv2.EVENT_LBUTTONDOWN:
        picker.handle_mouse_click(x, y)
    elif event == cv2.EVENT_MOUSEWHEEL:
        delta = _decode_wheel_delta(flags)
        # lan LEN (delta duong) -> cuon danh sach LEN; lan XUONG -> cuon XUONG
        picker.scroll(-1 if delta > 0 else 1, frame_size_holder["h"])


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    glasses_dir = os.path.join(project_root, "media", "tryon", "glasses")

    parser = argparse.ArgumentParser(
        description="Prototype thu kinh ao qua webcam - Giai doan 2 + Buoc 1 + Buoc A (tu dong can kinh) + bang chon kinh cot doc (muc 20/22)")
    parser.add_argument("--camera-index", type=int, default=0, help="Chi so webcam (mac dinh 0)")
    parser.add_argument("--max-seconds", type=float, default=None,
                         help="Tu dong thoat sau N giay - dung de do FPS qua console khong can bam 'q'")
    parser.add_argument("--max-frames", type=int, default=None,
                         help="Tu dong thoat sau N khung hinh")
    parser.add_argument("--no-window", action="store_true",
                         help="Khong mo cua so hien thi, chi in FPS qua console (dung khi test tu dong khong co man hinh)")
    parser.add_argument("--glasses-png", type=str, default=None,
                         help="[KIEU CU] Duong dan 1 file PNG rieng le, BO QUA bang chon (muc 20) - "
                              "dung khi muon test nhanh 1 anh don le. Mac dinh: quet ca thu muc, hien bang chon.")
    parser.add_argument("--width-ratio", type=float, default=1.6,
                         help="Be rong kinh hien thi = eye_distance * width_ratio (mac dinh 1.6, tinh truc tiep bang phim +/- khi dang chay)")
    parser.add_argument("--vertical-offset", type=float, default=0.0,
                         help="Do lech doc tam kinh so voi trung diem 2 mat, ty le theo eye_distance, duong = xuong duoi (mac dinh 0.0, tinh truc tiep bang phim [/] khi dang chay)")
    args = parser.parse_args()

    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "face_landmarker.task")

    if args.glasses_png:
        entries = [("custom", args.glasses_png)]
    else:
        entries = discover_glasses_models(glasses_dir)
        print(f"Tim thay {len(entries)} mau kinh trong {glasses_dir}:")
        for name, _ in entries:
            print(f"  - {name}")

    picker = GlassesPicker(entries)
    for _name, overlay in picker.models:
        overlay.width_ratio = args.width_ratio
        overlay.vertical_offset = args.vertical_offset

    cap = cv2.VideoCapture(args.camera_index)
    if not cap.isOpened():
        print(f"LOI: khong mo duoc webcam (camera index {args.camera_index}).")
        print("Kiem tra: webcam co dang bi ung dung khac (Zoom, Teams...) chiem dung khong,")
        print("hoac thu doi --camera-index sang 1, 2 neu may co nhieu camera.")
        sys.exit(1)

    try:
        normalizer = LightNormalizer()
        detector = FaceMeshDetector(model_path)
    except FileNotFoundError as e:
        print(f"LOI: {e}")
        cap.release()
        sys.exit(1)

    fps_meter = FPSMeter()

    frame_count = 0
    faces_detected_count = 0
    start_time = time.perf_counter()
    window_name = ("Thu kinh ao - Prototype (q=thoat; 1-9/click=chon kinh, "
                    "len/xuong hoac w/s=doi chon + tu cuon, lan chuot=cuon; +/-/[/]/p=che do du phong)")

    # frame_size_holder: dict CHIA SE giua vong lap chinh va callback chuot
    # (muc 22) - callback can biet chieu cao khung hinh hien tai de gioi han
    # cuon dung, nhung callback KHONG the tu doc bien "frame" cua vong lap.
    frame_size_holder = {"h": 0}
    if not args.no_window:
        # Phai tao cua so TRUOC roi moi gan duoc callback chuot (muc 20) -
        # cv2.imshow trong vong lap se dung lai cua so nay, khong tao lai.
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, _picker_mouse_callback, (picker, frame_size_holder))

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("LOI: khong doc duoc khung hinh tu webcam, dung lai.")
                break

            # Lat ngang cho giong nhu soi guong (trai nguoi dung = trai man
            # hinh) - lam TRUOC khi detect de landmark khop voi anh hien thi.
            frame = cv2.flip(frame, 1)

            frame = normalizer.normalize(frame)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result = detector.detect(frame, int(elapsed_ms))

            frame_h, frame_w = frame.shape[:2]
            frame_size_holder["h"] = frame_h

            overlay = picker.current_overlay
            anchors = FaceMeshDetector.get_eye_anchor_points(result, frame_w, frame_h)
            if overlay is not None and anchors is not None:
                pt_a, pt_b = anchors
                frame = overlay.render_on_frame_auto(frame, pt_a, pt_b)
                faces_detected_count += 1
            elif anchors is None:
                cv2.putText(frame, "Khong phat hien khuon mat", (10, frame_h - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)

            fps_meter.tick()
            fps_meter.draw(frame)
            if overlay is not None:
                overlay.draw_calibration_hint(frame)
                cv2.putText(frame, f"Mau dang deo: {picker.current_name}", (10, frame_h - 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
            picker.draw(frame)
            frame_count += 1

            if not args.no_window:
                cv2.imshow(window_name, frame)
                # waitKeyEx (thay vi waitKey) de lay duoc MA PHIM DAY DU cua
                # phim mui ten (muc 22) - cac phim ASCII binh thuong (q, so,
                # +/-/[/]/p) van lay dung qua "& 0xFF" nhu truoc, khong doi.
                raw_key = cv2.waitKeyEx(1)
                key = raw_key & 0xFF
                if key == ord('q'):
                    print("Nguoi dung nhan 'q', dung chuong trinh.")
                    break
                elif ord('1') <= key <= ord('9'):
                    picker.select_visible_slot(key - ord('1'))
                elif raw_key == _ARROW_KEY_UP or key in (ord('w'), ord('W')):
                    picker.move_selection(-1, frame_h)
                elif raw_key == _ARROW_KEY_DOWN or key in (ord('s'), ord('S')):
                    picker.move_selection(1, frame_h)
                elif overlay is None:
                    pass  # khong co mau kinh nao dang chon - phim chinh tay ben duoi khong co gi de tac dung
                elif key in (ord('+'), ord('=')):
                    overlay.width_ratio = round(overlay.width_ratio + 0.05, 2)
                elif key == ord('-'):
                    overlay.width_ratio = round(max(0.1, overlay.width_ratio - 0.05), 2)
                elif key == ord(']'):
                    overlay.vertical_offset = round(overlay.vertical_offset + 0.01, 2)
                elif key == ord('['):
                    overlay.vertical_offset = round(overlay.vertical_offset - 0.01, 2)
                elif key == ord('p'):
                    print(f">>> Calibration hien tai ({picker.current_name}): "
                          f"--width-ratio {overlay.width_ratio} --vertical-offset {overlay.vertical_offset}")

            total_elapsed = time.perf_counter() - start_time
            if args.max_seconds is not None and total_elapsed >= args.max_seconds:
                print(f"Da dat gioi han {args.max_seconds}s, tu dong dung.")
                break
            if args.max_frames is not None and frame_count >= args.max_frames:
                print(f"Da dat gioi han {args.max_frames} khung hinh, tu dong dung.")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()

        total_elapsed = time.perf_counter() - start_time
        avg_fps = frame_count / total_elapsed if total_elapsed > 0 else 0.0
        detect_rate = (faces_detected_count / frame_count * 100.0) if frame_count else 0.0
        print("\n===== KET QUA DO HIEU NANG (Giai doan 2 - CHUA toi uu) =====")
        print(f"Tong so khung hinh xu ly    : {frame_count}")
        print(f"Tong thoi gian              : {total_elapsed:.2f} giay")
        print(f"FPS trung binh              : {avg_fps:.2f}")
        print(f"Khung hinh phat hien mat    : {faces_detected_count} ({detect_rate:.1f}%)")
        overlay = picker.current_overlay
        if overlay is None:
            print("\n===== KHONG CO MAU KINH NAO duoc nap (thu muc rong hoac tat ca loi anh) =====")
        elif overlay._lens_left is not None:
            print(f"\n===== Mau dang dung '{picker.current_name}': CHE DO TU DONG - khong can calibration =====")
        else:
            print(f"\n===== Mau dang dung '{picker.current_name}': CHE DO DU PHONG - CALIBRATION dan lai lam mac dinh moi =====")
            print(f"--width-ratio {overlay.width_ratio} --vertical-offset {overlay.vertical_offset}")


if __name__ == "__main__":
    main()
