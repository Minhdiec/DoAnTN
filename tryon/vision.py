r"""
"Bo nao" xu ly anh cua module thu kinh ao - chuyen the tu prototype doc lap
(prototype/tryon_demo.py, dung bang trang thai cuoi CLAUDE_PROGRESS.md muc 19
- "Buoc A": tu dong can kinh bang 2 diem neo tam trong kinh, CHUA co anh 3/4/
multi-view). Xem CLAUDE_PROGRESS.md muc 24 (Buoc B) de biet boi canh day du.

3 class duoi day GIU NGUYEN thuat toan da duoc nguoi dung xac nhan bang
webcam that o prototype (chi bo phan cv2.imshow/window/phim/chuot - khong
dung duoc tren web, thay bang WebSocket trong tryon/consumers.py):

  - LightNormalizer: chuan hoa anh sang (CLAHE tren kenh L/LAB).
  - FaceMeshDetector: boc mediapipe.tasks.python.vision.FaceLandmarker
    (Tasks API - xem CLAUDE_PROGRESS.md muc 2 quyet dinh #6), che do VIDEO de
    tu bam vet giua cac khung hinh.
  - GlassesOverlay: ghep anh PNG kinh (nen trong suot) len khuon mat, tu
    dong can bang 2 diem neo tam trong (che do CHINH), hoac width_ratio/
    vertical_offset (che do DU PHONG - 2 so nay lay tu model
    tryon.models.GlassesOverlay khi khoi tao, xem tryon/consumers.py).

KHONG chuyen GlassesPicker/FPSMeter/main() - do la phan giao dien cua so
OpenCV rieng cho prototype chay tren may, khong dung duoc tren web (gallery
chon kinh o web se la HTML/JS - xem templates/products/detail.html, va FPS
do o phia server se log qua print() don gian trong consumer, khong can class
rieng).
"""

import math
import os

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision


class LightNormalizer:
    """Chuan hoa anh sang bang CLAHE tren kenh L cua khong gian mau LAB -
    xem prototype/tryon_demo.py de biet ly do chon CLAHE thay vi
    cv2.equalizeHist thong thuong (giu nguyen docstring goc)."""

    def __init__(self, clip_limit: float = 2.0, tile_grid_size=(8, 8), dark_threshold: float = 90.0):
        self._clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
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
    """Boc mediapipe.tasks.python.vision.FaceLandmarker (Tasks API moi).
    CHE DO VIDEO (khong phai IMAGE) de MediaPipe tu bam vet giua cac khung
    hinh - xem prototype/tryon_demo.py de biet chi tiet.

    QUAN TRONG (khac prototype chay 1 nguoi dung tren may): moi KET NOI
    WebSocket (moi nguoi dung) phai co MOT instance FaceMeshDetector RIENG,
    vi che do VIDEO giu trang thai bam vet + doi hoi timestamp tang don
    dieu RIENG cho tung luong video - dung chung 1 instance cho nhieu nguoi
    dung se lam sai trang thai bam vet lan nhau. Xem tryon/consumers.py:
    detector duoc tao trong connect() (rieng cho tung ket noi) va dong trong
    disconnect().
    """

    RIGHT_EYE_OUTER = 33   # mat phai cua NGUOI (anatomical)
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
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        return self._landmarker.detect_for_video(mp_image, timestamp_ms)

    @classmethod
    def get_eye_anchor_points(cls, result, frame_width: int, frame_height: int):
        """Tra ve (diem_mat_a, diem_mat_b) toa do pixel, hoac None neu khong
        phat hien duoc mat nao."""
        if not result.face_landmarks:
            return None
        landmarks = result.face_landmarks[0]
        lm_a = landmarks[cls.RIGHT_EYE_OUTER]
        lm_b = landmarks[cls.LEFT_EYE_OUTER]
        pt_a = (lm_a.x * frame_width, lm_a.y * frame_height)
        pt_b = (lm_b.x * frame_width, lm_b.y * frame_height)
        return pt_a, pt_b

    def close(self):
        self._landmarker.close()


class GlassesOverlay:
    """Ghep anh kinh PNG (nen trong suot, RGBA) len khuon mat - GIU NGUYEN
    thuat toan "Buoc A" da duoc nguoi dung xac nhan bang webcam that (xem
    CLAUDE_PROGRESS.md muc 14/19). Xem prototype/tryon_demo.py de biet giai
    thich day du tung ky thuat (premultiplied alpha, tu dong tim tam trong
    kinh bang contour hierarchy + Otsu, tu chon chieu ghep it xoay nhat...)
    - o day chi giu code, khong lap lai toan bo docstring giai thich cho
    gon file.

    KHAC prototype: width_ratio/vertical_offset (che do DU PHONG) khong con
    la tham so CLI nua, ma doc tu model tryon.models.GlassesOverlay (2 truong
    cung ten) khi tao doi tuong nay trong tryon/consumers.py - nguoi dung
    canh chinh qua 2 thanh truot tren giao dien web (xem BUOC C), gia tri
    duoc gui len qua WebSocket va ap truc tiep vao instance dang chay.
    """

    def __init__(self, png_path: str = None, width_ratio: float = 1.6, vertical_offset: float = 0.0):
        self.width_ratio = width_ratio
        self.vertical_offset = vertical_offset
        self._image_premult = None
        self._anchor_x = None
        self._anchor_y = None
        self._src_width = None
        self._lens_left = None
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
            except Exception as e:
                print(f"CANH BAO: loi doc anh kinh '{png_path}' ({e}). Dung kinh demo ve bang code thay the.")
                self._set_image(self._draw_demo_glasses(), detect_lens_anchors=False)
        else:
            self._set_image(self._draw_demo_glasses(), detect_lens_anchors=False)

    def _draw_demo_glasses(self) -> np.ndarray:
        """Kinh demo ve bang code - CHI dung khi khong co/khong doc duoc PNG
        that (vi du GlassesOverlay model bi thieu file anh)."""
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
            self._lens_left = None
            self._lens_right = None
            return

        lens_anchors = self._find_lens_anchors(bgra)
        if lens_anchors is None:
            self._lens_left = None
            self._lens_right = None
            print("CANH BAO: khong tu tim duoc 2 tam trong kinh dang tin cay trong anh nay "
                  "- dung che do du phong (width_ratio/vertical_offset).")
        else:
            self._lens_left, self._lens_right = lens_anchors

    @staticmethod
    def _find_lens_anchors(bgra: np.ndarray):
        """Tu dong tim tam 2 trong kinh trong anh PNG (2 truong hop: lo that
        alpha=0, hoac trong duc nhat mau hon gong qua Otsu) - xem
        prototype/tryon_demo.py de biet giai thich day du. Tra ve None neu
        khong tim duoc 2 vung du tin cay."""
        alpha = bgra[:, :, 3]
        silhouette = (alpha > 10).astype(np.uint8) * 255
        if silhouette.sum() == 0:
            return None

        contours, hierarchy = cv2.findContours(silhouette, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if hierarchy is None or len(contours) == 0:
            return None
        hierarchy = hierarchy[0]

        outer_candidates = [i for i in range(len(contours)) if hierarchy[i][3] == -1]
        if not outer_candidates:
            return None
        outer_idx = max(outer_candidates, key=lambda i: cv2.contourArea(contours[i]))
        if cv2.contourArea(contours[outer_idx]) <= 0:
            return None
        _, _, w0, h0 = cv2.boundingRect(contours[outer_idx])
        min_area = (w0 * h0) * 0.02

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

        outer_mask = np.zeros(silhouette.shape, dtype=np.uint8)
        cv2.drawContours(outer_mask, contours, outer_idx, 255, thickness=-1)
        for i in holes:
            cv2.drawContours(outer_mask, contours, i, 0, thickness=-1)
        inside = outer_mask > 0
        if inside.sum() < min_area:
            return None

        gray = cv2.cvtColor(bgra[:, :, :3], cv2.COLOR_BGR2GRAY)
        vals = gray[inside]
        if vals.max() == vals.min():
            return None
        otsu_t, _ = cv2.threshold(vals.reshape(-1, 1).astype(np.uint8), 0, 255,
                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        class_low = inside & (gray <= otsu_t)
        class_high = inside & (gray > otsu_t)

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
        """Ma tran affine 2x3 chi gom xoay deu + ty le deu + tinh tien (xem
        prototype/tryon_demo.py de biet suy dien bang so phuc)."""
        src1c, src2c = complex(*src1), complex(*src2)
        dst1c, dst2c = complex(*dst1), complex(*dst2)
        a = (dst2c - dst1c) / (src2c - src1c)
        b = dst1c - a * src1c
        return np.array([
            [a.real, -a.imag, b.real],
            [a.imag, a.real, b.imag],
        ], dtype=np.float32)

    def render_on_frame_auto(self, frame_bgr: np.ndarray, eye_a, eye_b) -> np.ndarray:
        """Duong CHINH: can kinh TU DONG bang 2 diem neo tam trong. Neu anh
        kinh khong tu tim duoc 2 tam trong thi tu dong goi lai
        render_on_frame (che do du phong)."""
        if self._lens_left is None or self._lens_right is None:
            return self.render_on_frame(frame_bgr, eye_a, eye_b)

        dx, dy = eye_b[0] - eye_a[0], eye_b[1] - eye_a[1]
        if math.hypot(dx, dy) < 1e-3:
            return frame_bgr

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
        """Che do DU PHONG: co gian + xoay bang width_ratio/vertical_offset
        chinh tay (xem prototype/tryon_demo.py de biet giai thich day du)."""
        dx = pt_b[0] - pt_a[0]
        dy = pt_b[1] - pt_a[1]
        eye_distance = math.hypot(dx, dy)
        if eye_distance < 1e-3:
            return frame_bgr

        scale = (eye_distance * self.width_ratio) / self._src_width
        angle_deg = math.degrees(math.atan2(dy, dx))

        src_h, src_w = self._image_premult.shape[:2]
        new_w = max(1, int(src_w * scale))
        new_h = max(1, int(src_h * scale))
        resized = cv2.resize(self._image_premult, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

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

    @staticmethod
    def _alpha_blend(frame_bgr: np.ndarray, overlay_premult_bgra: np.ndarray, x: int, y: int) -> np.ndarray:
        frame_h, frame_w = frame_bgr.shape[:2]
        ov_h, ov_w = overlay_premult_bgra.shape[:2]

        src_x0, src_y0 = max(0, -x), max(0, -y)
        dst_x0, dst_y0 = max(0, x), max(0, y)
        dst_x1 = min(frame_w, x + ov_w)
        dst_y1 = min(frame_h, y + ov_h)
        if dst_x1 <= dst_x0 or dst_y1 <= dst_y0:
            return frame_bgr

        src_x1 = src_x0 + (dst_x1 - dst_x0)
        src_y1 = src_y0 + (dst_y1 - dst_y0)

        roi = frame_bgr[dst_y0:dst_y1, dst_x0:dst_x1]
        overlay_crop = overlay_premult_bgra[src_y0:src_y1, src_x0:src_x1]

        alpha = overlay_crop[:, :, 3:4].astype(np.float32) / 255.0
        premult_rgb = overlay_crop[:, :, :3].astype(np.float32)
        roi_f = roi.astype(np.float32)

        blended = premult_rgb + roi_f * (1.0 - alpha)
        frame_bgr[dst_y0:dst_y1, dst_x0:dst_x1] = np.clip(blended, 0, 255).astype(np.uint8)
        return frame_bgr
