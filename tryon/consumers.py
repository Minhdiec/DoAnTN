r"""
WebSocket consumer cho module thu kinh ao (CLAUDE_PROGRESS.md muc 24, Buoc B).

GIAO THUC (tu thiet ke, khong phai chuan co san - ghi ro o day de nguoi doc
sau nay khoi doan): moi ket noi WebSocket xu ly 2 loai tin nhan:

  - Client -> Server, tin nhan VAN BAN (JSON): lenh dieu khien.
        {"action": "select_glasses", "glasses_id": 3}   doi mau kinh dang deo
        {"action": "calibrate", "width_ratio": 1.7, "vertical_offset": 0.02}
            chinh 2 so che do du phong (chi co tac dung khi mau kinh dang
            chon dang o che do du phong - xem tryon/vision.py GlassesOverlay)

  - Client -> Server, tin nhan NHI PHAN (bytes): DUNG 1 khung hinh JPEG chup
    tu webcam nguoi dung.

  - Server -> Client, tin nhan NHI PHAN (bytes) - PHAN HOI cho MOI khung hinh
    nhan duoc: byte DAU TIEN la co trang thai (1 = co phat hien khuon mat,
    0 = khong), CAC BYTE CON LAI la du lieu JPEG cua khung hinh da xu ly (co
    dan kinh neu co mat + da chon mau kinh, hoac la khung hinh goc da chuan
    hoa anh sang neu khong co mat - dung "tra khung hinh goc" theo dung yeu
    cau muc 24). Gop 2 thu vao 1 tin nhan NHI PHAN DUY NHAT (thay vi 2 tin
    nhan rieng: 1 JSON trang thai + 1 binary anh) de KHONG phu thuoc gia
    dinh "thu tu tin nhan" mong manh phia client - don gian va chac chan
    hon la tach 2 tin nhan.

  - Server -> Client, tin nhan VAN BAN (JSON) - CHI gui khi co loi:
        {"type": "error", "message": "..."}

MOI KET NOI (moi nguoi dung mo trang thu kinh) co MOT instance
FaceMeshDetector RIENG - BAT BUOC vi che do VIDEO cua MediaPipe giu trang
thai bam vet (tracking) + doi hoi timestamp tang don dieu RIENG cho tung
luong video (xem tryon/vision.py). Dung chung 1 instance cho nhieu nguoi se
lam sai trang thai bam vet cua nhau.

GIAI DOAN 3 - TOI UU DO TRE (CLAUDE_PROGRESS.md muc 11, ap dung trong
_process_frame_sync/_select_detection_region duoi day):
  1. Thu nho anh dua vao MediaPipe (DETECT_DOWNSCALE_WIDTH) khi CHUA co vi
     tri mat tu khung truoc, nhung LUON ve/dan kinh len khung hinh GOC
     (frame khong bi thu nho) - landmark cua MediaPipe la toa do CHUAN
     HOA nen doc lap voi do phan giai anh dua vao, xem
     FaceMeshDetector.get_eye_anchor_points.
  2. Gioi han tan suat goi detect() ~MIN_DETECT_INTERVAL_MS (chi khi DANG
     bam vet on dinh - _last_face_box khong None); giua 2 lan detect, tai
     dung anh neo tho cua lan detect gan nhat (van duoc dua qua
     AnchorSmoother de khong "dung hinh" cung nhac).
  3. AnchorSmoother (One-Euro filter, xem tryon/vision.py) lam muot
     tam/be rong/goc cua 2 diem neo mat truoc khi ve kinh.
  4. Cache renderer (anh PNG kinh da giai ma + do tam trong 1 lan) theo
     glasses_id trong self._renderers - da co tu truoc Giai doan 3, giu
     nguyen.
  5. Khi DA co vi tri mat tu khung truoc, chi cat + resize vung ROI quanh
     mat (ROI_DETECT_SIZE, rong hon eye_distance*ROI_PADDING_RATIO de
     chua ca khuon mat) de dua vao MediaPipe thay vi ca khung hinh; VA chi
     chay CLAHE (LightNormalizer) khi should_normalize() thuc su bao thieu
     sang, thay vi vo dieu kien moi khung nhu truoc.
Do FPS truoc/sau: xem CLAUDE_PROGRESS.md (muc ghi lai Giai doan 3) - dung
scripts/bench_tryon_direct.py (goi truc tiep _process_frame_sync, bo qua
lop Channels/ASGI vi khong phai muc tieu toi uu cua giai doan nay).

SUA LOI "GIAT/NHAP NHAY" phat hien khi test tren web thuc (CLAUDE_PROGRESS.md
muc 39, sau khi trien khai Giai doan 3 ban dau):
  a. AnchorSmoother.beta qua lon so voi don vi PIXEL (0.4, copy tu vi du
     dung don vi CHUAN HOA 0..1) lam bo loc GAN NHU VO HIEU voi nhieu that
     cua MediaPipe - da do lai va giam xuong 0.015 (xem tryon/vision.py).
  b. should_normalize() (hysteresis) thay is_low_light() (nguong cung) -
     tranh CLAHE bat/tat moi khung khi do sang dao dong quanh nguong.
  c. MAX_CONSECUTIVE_MISSES: khong xoa _last_face_box/_last_raw_anchors
     ngay tu 1 lan detect() hut - chi coi la mat mat sau nhieu lan LIEN
     TIEP, tranh kinh bien-mat-roi-hien-lai gay cam giac nhap nhay.
"""

import json
import math
import time
from collections import deque

import cv2
import numpy as np
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from .models import GlassesOverlay as GlassesOverlayModel
from .vision import AnchorSmoother, FaceMeshDetector, GlassesOverlay as GlassesRenderer, LightNormalizer

MODEL_PATH = str(settings.BASE_DIR / "prototype" / "models" / "face_landmarker.task")

# Chat luong nen JPEG khi tra khung hinh ve client - 80 la muc can bang pho
# bien (dung lai duoc tren mang chat luong kha tot ma dung luong khong qua
# nang). Da do thu (xem CLAUDE_PROGRESS.md, Giai doan 3): chi phi CPU thuc
# su nam o MediaPipe/CLAHE/warpAffine, khong nam o buoc nen JPEG nay, nen
# gia tri 80 KHONG can doi khi toi uu do tre.
JPEG_ENCODE_PARAMS = [int(cv2.IMWRITE_JPEG_QUALITY), 80]

# ---- Hang so Giai doan 3 (toi uu do tre) ---------------------------------

# Ky thuat 2: gioi han tan suat goi MediaPipe detect() ~15 lan/giay (~66ms)
# khi dang bam vet on dinh - MediaPipe la buoc ton CPU nhat trong pipeline.
MIN_DETECT_INTERVAL_MS = 1000.0 / 15.0

# Ky thuat 1: be rong (px) thu nho khung hinh VE truoc khi dua vao
# MediaPipe khi CHUA co vi tri mat tu khung truoc (tim mat lan dau, hoac
# vua bi mat dau) - can quet ca khung hinh nen khong the dung ROI nho.
DETECT_DOWNSCALE_WIDTH = 400

# Ky thuat 5: kich thuoc (px, hinh vuong) resize ROI truoc khi dua vao
# MediaPipe khi DA co vi tri mat tu khung truoc - vung tim kiem nho hon
# nhieu so voi ca khung hinh nen re hon dang ke.
ROI_DETECT_SIZE = 256

# Ky thuat 5: canh ROI = eye_distance (khoang cach 2 khoe mat ngoai) nhan
# ti le nay - du rong de chua ca khuon mat (khong chi 2 mat) va con dem
# cho dau xoay/dich nhe giua 2 lan detect. Da DO THAT bang 478 landmark
# MediaPipe tren anh mau (xem CLAUDE_PROGRESS.md muc 39): bbox toan bo mat
# ~1.58x eye_distance -> 2.4 la ~1.5x biên an toan so voi kich thuoc mat
# LUC DUNG YEN; giu nguyen (khong phai nguyen nhan gay giat/nhap nhay -
# xem muc 39, nguyen nhan thuc la 2 cho khac ben duoi).
ROI_PADDING_RATIO = 2.4

# Ky thuat 2 mo rong - "dung sai" khi mat: cho phep toi da bao nhieu lan
# detect() LIEN TIEP khong tim thay mat truoc khi THUC SU coi la mat mat
# (xoa _last_face_box, tra ve khung khong dan kinh). Neu xoa NGAY tu lan
# dau (nguong = 1), 1 khung nhieu/lgi ROI don le se lam kinh BIEN MAT roi
# HIEN LAI ngay sau do -> cam giac "nhap nhay" - xem CLAUDE_PROGRESS.md
# muc 39.
MAX_CONSECUTIVE_MISSES = 3

# In FPS trung binh truot + thoi gian xu ly trung binh ra console moi
# khoang thoi gian nay (giay) - THEO DUNG huong dan trong docstring dau
# tryon/vision.py: "FPS do o phia server se log qua print() don gian
# trong consumer, khong can class rieng" - KHONG ghi file moi khung hinh
# (khac voi debug_log cu da bi xoa vi chinh no gay them do tre I/O).
FPS_LOG_INTERVAL_S = 5.0


class TryOnConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        self._normalizer = LightNormalizer()
        # Cache instance GlassesRenderer theo glasses_id - moi mau kinh chi
        # can doc file PNG + tu dong tim tam trong kinh MOT LAN, doi kinh qua
        # lai nhieu lan trong 1 phien khong doc lai file.
        self._renderers = {}
        self._current_glasses_id = None
        self._start_time = time.perf_counter()

        # Trang thai bam vet cho Giai doan 3 (ky thuat 2 + 5) - xem
        # _select_detection_region/_process_frame_sync.
        self._last_face_box = None       # (x0,y0,w,h) trong toa do khung GOC, tu khung truoc; None = chua/vua mat mat
        self._last_raw_anchors = None    # (pt_a,pt_b) THO (chua qua smoother) tu lan detect() gan nhat
        self._last_detect_ms = float("-inf")
        self._consecutive_misses = 0     # so lan detect() LIEN TIEP khong ra mat - xem MAX_CONSECUTIVE_MISSES
        self._smoother = AnchorSmoother()

        # Do FPS tren pipeline thuc (khong ghi file moi khung - xem
        # FPS_LOG_INTERVAL_S o tren) - phuc vu bang so sanh truoc/sau cua
        # Giai doan 3.
        self._frame_timestamps = deque(maxlen=200)
        self._frame_process_ms_sum = 0.0
        self._frame_process_count = 0
        self._last_fps_log = time.perf_counter()

        try:
            # Khoi tao FaceLandmarker la thao tac I/O + CPU dang ke (doc file
            # model ~3.6MB, dung mang) - day qua thread de khong chan event
            # loop luc client khac dang ket noi cung luc.
            self._detector = await sync_to_async(FaceMeshDetector, thread_sensitive=False)(MODEL_PATH)
        except FileNotFoundError as e:
            await self.send(text_data=json.dumps({"type": "error", "message": str(e)}))
            await self.close()

    async def disconnect(self, close_code):
        detector = getattr(self, "_detector", None)
        if detector is not None:
            await sync_to_async(detector.close, thread_sensitive=False)()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is not None:
            await self._handle_control_message(text_data)
        elif bytes_data is not None:
            await self._handle_frame(bytes_data)

    # ---- Xu ly tin nhan dieu khien (JSON) --------------------------------

    async def _handle_control_message(self, text_data: str) -> None:
        try:
            payload = json.loads(text_data)
        except ValueError:
            await self.send(text_data=json.dumps({"type": "error", "message": "Tin nhan JSON khong hop le"}))
            return

        action = payload.get("action")
        if action == "select_glasses":
            await self._select_glasses(payload.get("glasses_id"))
        elif action == "calibrate":
            self._apply_calibration(payload)
        else:
            await self.send(text_data=json.dumps({"type": "error", "message": f"Khong hieu lenh '{action}'"}))

    @database_sync_to_async
    def _load_glasses_row(self, glasses_id):
        try:
            return GlassesOverlayModel.objects.select_related("product").get(pk=glasses_id)
        except (GlassesOverlayModel.DoesNotExist, ValueError, TypeError):
            return None

    async def _select_glasses(self, glasses_id) -> None:
        if glasses_id is None:
            return
        if glasses_id in self._renderers:
            self._current_glasses_id = glasses_id
            return

        row = await self._load_glasses_row(glasses_id)
        if row is None:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Khong tim thay mau kinh id={glasses_id}",
            }))
            return

        # Doc file PNG + tu dong tim tam trong kinh (co the mat vai chuc ms
        # voi anh lon) - day qua thread, khong chan cac client khac.
        renderer = await sync_to_async(GlassesRenderer, thread_sensitive=False)(
            row.image.path, row.width_ratio, row.vertical_offset,
        )
        self._renderers[glasses_id] = renderer
        self._current_glasses_id = glasses_id

    def _apply_calibration(self, payload: dict) -> None:
        renderer = self._renderers.get(self._current_glasses_id)
        if renderer is None:
            return
        if "width_ratio" in payload:
            try:
                renderer.width_ratio = float(payload["width_ratio"])
            except (TypeError, ValueError):
                pass
        if "vertical_offset" in payload:
            try:
                renderer.vertical_offset = float(payload["vertical_offset"])
            except (TypeError, ValueError):
                pass

    # ---- Xu ly khung hinh webcam (binary) ---------------------------------

    async def _handle_frame(self, jpeg_bytes: bytes) -> None:
        result = await sync_to_async(self._process_frame_sync, thread_sensitive=False)(jpeg_bytes)
        if result is not None:
            await self.send(bytes_data=result)

    def _select_detection_region(self, frame: np.ndarray):
        """Giai doan 3, ky thuat 1 + 5: chon VUNG anh + do phan giai dua
        vao MediaPipe detect(), TACH RIENG voi khung hinh GOC dung de ve
        kinh (frame khong bi anh huong). Tra ve (anh_dua_vao_detect,
        offset_goc_tren_trai, (rong_that, cao_that)) - 2 gia tri cuoi la
        kich thuoc THAT (truoc khi resize) cua vung, dung de
        get_eye_anchor_points anh xa nguoc ve toa do khung goc.

        - DA co _last_face_box (dang bam vet on dinh): cat ROI quanh mat
          tu khung TRUOC + resize ve ROI_DETECT_SIZE - vung tim kiem nho
          hon nhieu so voi ca khung hinh.
        - CHUA co (lan dau, hoac vua mat mat): phai quet CA khung hinh (vi
          chua biet mat o dau), nhung thu nho truoc khi dua vao MediaPipe
          de giam chi phi.
        """
        frame_h, frame_w = frame.shape[:2]

        if self._last_face_box is not None:
            x0, y0, w, h = self._last_face_box
            crop = frame[y0:y0 + h, x0:x0 + w]
            if crop.size > 0:
                detect_input = cv2.resize(
                    crop, (ROI_DETECT_SIZE, ROI_DETECT_SIZE), interpolation=cv2.INTER_LINEAR,
                )
                return detect_input, (x0, y0), (w, h)

        if frame_w > DETECT_DOWNSCALE_WIDTH:
            scale = DETECT_DOWNSCALE_WIDTH / frame_w
            small_size = (DETECT_DOWNSCALE_WIDTH, max(1, int(round(frame_h * scale))))
            detect_input = cv2.resize(frame, small_size, interpolation=cv2.INTER_LINEAR)
        else:
            detect_input = frame  # khung hinh da nho hon nguong - khong can thu them
        return detect_input, (0, 0), (frame_w, frame_h)

    @staticmethod
    def _compute_face_box(pt_a, pt_b, frame_w: int, frame_h: int):
        """Giai doan 3, ky thuat 5: tinh ROI (x0,y0,w,h) quanh mat cho
        _select_detection_region dung o KHUNG KE TIEP - canh ROI =
        eye_distance*ROI_PADDING_RATIO (du rong chua ca khuon mat), tam tai
        trung diem 2 diem neo, clamp trong bien khung hinh."""
        dx, dy = pt_b[0] - pt_a[0], pt_b[1] - pt_a[1]
        eye_distance = math.hypot(dx, dy)
        if eye_distance < 1e-3:
            return None
        cx, cy = (pt_a[0] + pt_b[0]) / 2.0, (pt_a[1] + pt_b[1]) / 2.0
        side = eye_distance * ROI_PADDING_RATIO

        x0 = max(0, min(int(round(cx - side / 2)), frame_w - 1))
        y0 = max(0, min(int(round(cy - side / 2)), frame_h - 1))
        w = max(1, min(int(round(side)), frame_w - x0))
        h = max(1, min(int(round(side)), frame_h - y0))
        return x0, y0, w, h

    def _record_frame_timing(self, process_ms: float) -> None:
        """In FPS trung binh truot ra console moi FPS_LOG_INTERVAL_S giay -
        xem hang so o dau file de biet ly do KHONG ghi file moi khung."""
        now = time.perf_counter()
        self._frame_timestamps.append(now)
        self._frame_process_ms_sum += process_ms
        self._frame_process_count += 1

        if now - self._last_fps_log < FPS_LOG_INTERVAL_S:
            return
        if len(self._frame_timestamps) >= 2:
            span = self._frame_timestamps[-1] - self._frame_timestamps[0]
            fps = (len(self._frame_timestamps) - 1) / span if span > 0 else 0.0
        else:
            fps = 0.0
        avg_ms = self._frame_process_ms_sum / self._frame_process_count
        print(f"[TryOn][GiaiDoan3] FPS~={fps:.1f}  avg_process_ms={avg_ms:.1f}  n={self._frame_process_count}")
        self._last_fps_log = now
        self._frame_process_ms_sum = 0.0
        self._frame_process_count = 0

    def _process_frame_sync(self, jpeg_bytes: bytes):
        """Toan bo pipeline CPU-bound (decode -> [CLAHE co dieu kien] ->
        MediaPipe (co gioi han tan suat + ROI/thu nho) -> lam muot -> dan
        kinh -> encode lai) - HAM DONG BO, luon duoc goi qua
        sync_to_async(..., thread_sensitive=False) o tren, KHONG duoc goi
        truc tiep tu ham async (se chan event loop cua toan bo server)."""
        frame_start = time.perf_counter()

        frame_arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return None  # du lieu JPEG hong/khong doc duoc - bo qua khung hinh nay

        # Lat ngang cho giong soi guong (trai nguoi dung = trai man hinh) -
        # PORT TU prototype/tryon_demo.py main() (dong nay nam trong vong
        # lap orchestration, khong nam trong 3 class o vision.py nen de sot
        # khi port ban dau - da tu phat hien khi ra soat lai). Phai lam
        # TRUOC khi detect de landmark khop dung voi anh hien thi cho client.
        frame = cv2.flip(frame, 1)

        # Giai doan 3, ky thuat 5: CLAHE ton chi phi dang ke (doi khong
        # gian mau LAB + xu ly kenh L + doi lai BGR tren CA khung hinh) -
        # CHI chay khi anh THUC SU thieu sang. Dung should_normalize() (co
        # HYSTERESIS + trang thai dinh, xem tryon/vision.py) THAY VI
        # is_low_light() (nguong cung) - da phat hien qua test tren web
        # thuc: nguong cung lam CLAHE bat/tat MOI KHUNG khi do sang trung
        # binh dao dong tu nhien quanh diem nguong, gay CA KHUNG HINH nhap
        # nhay sang/toi (xem CLAUDE_PROGRESS.md muc 39).
        if self._normalizer.should_normalize(frame):
            frame = self._normalizer.normalize(frame)

        frame_h, frame_w = frame.shape[:2]
        now_ms = (time.perf_counter() - self._start_time) * 1000.0

        # Giai doan 3, ky thuat 2: chi goi lai MediaPipe detect() (buoc ton
        # CPU nhat) khi CHUA co vi tri mat dang bam vet, HOAC da qua du lau
        # tu lan detect gan nhat - giua 2 lan, tai dung ket qua tho cua lan
        # detect gan nhat (van duoc AnchorSmoother lam muot moi khung).
        should_detect = (
            self._last_face_box is None
            or (now_ms - self._last_detect_ms) >= MIN_DETECT_INTERVAL_MS
        )
        if should_detect:
            detect_input, offset, region_size = self._select_detection_region(frame)
            result = self._detector.detect(detect_input, int(now_ms))
            detected_anchors = FaceMeshDetector.get_eye_anchor_points(
                result, region_size[0], region_size[1], offset,
            )
            self._last_detect_ms = now_ms

            if detected_anchors is not None:
                self._consecutive_misses = 0
                self._last_raw_anchors = detected_anchors
                self._last_face_box = self._compute_face_box(
                    detected_anchors[0], detected_anchors[1], frame_w, frame_h,
                )
            else:
                # Giai doan 3, ky thuat 2 mo rong: KHONG xoa trang thai bam
                # vet ngay tu 1 khung mat 1 lan - phat hien qua test tren
                # web thuc: 1 lan detect() hut (nhieu ROI/nhay khung nhat
                # thoi) lam kinh BIEN MAT roi HIEN LAI ngay khung sau, gay
                # cam giac "nhap nhay" ro hon la mat that (xem muc 39). Chi
                # thuc su coi la mat mat sau MAX_CONSECUTIVE_MISSES lan
                # LIEN TIEP khong ra ket qua - giua luc do van GIU nguyen
                # vi tri/ROI cu (kinh dung yen tai cho, khong bien mat).
                self._consecutive_misses += 1
                if self._consecutive_misses >= MAX_CONSECUTIVE_MISSES:
                    self._last_raw_anchors = None
                    self._last_face_box = None

        raw_anchors = self._last_raw_anchors
        face_detected = raw_anchors is not None

        renderer = self._renderers.get(self._current_glasses_id)
        if face_detected:
            # Giai doan 3, ky thuat 3: lam muot tam/be rong/goc truoc khi
            # ve, thay vi dung thang toa do tho (hay rung do nhieu nhan
            # dien tung khung).
            pt_a, pt_b = self._smoother.smooth(raw_anchors[0], raw_anchors[1], now_ms / 1000.0)
            if renderer is not None:
                frame = renderer.render_on_frame_auto(frame, pt_a, pt_b)
        else:
            # Mat mat (hoac chua tung thay) - reset smoother de lan tim lai
            # mat bam THANG vao vi tri moi, khong bi "keo" tu vi tri cu.
            self._smoother.reset()
        # Khong co mat HOAC chua chon mau kinh nao -> tra khung hinh GOC (da
        # chuan hoa anh sang neu can) khong dan gi ca, dung theo dung yeu
        # cau muc 24 ("Khong co mat trong khung -> tra khung hinh goc + co bao").

        ok, buf = cv2.imencode(".jpg", frame, JPEG_ENCODE_PARAMS)
        if not ok:
            return None

        self._record_frame_timing((time.perf_counter() - frame_start) * 1000.0)

        status_byte = bytes([1 if face_detected else 0])
        return status_byte + buf.tobytes()
