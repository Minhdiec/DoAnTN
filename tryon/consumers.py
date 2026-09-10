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
"""

import json
import time

import cv2
import numpy as np
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from .models import GlassesOverlay as GlassesOverlayModel
from .vision import FaceMeshDetector, GlassesOverlay as GlassesRenderer, LightNormalizer

MODEL_PATH = str(settings.BASE_DIR / "prototype" / "models" / "face_landmarker.task")

# #region DEBUG
import pathlib
_DEBUG_LOG_PATH = pathlib.Path(settings.BASE_DIR) / ".claude" / "debug.log"


def _debug_log(msg: str) -> None:
    _DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[PY] {msg}\n")
# #endregion DEBUG

# Chat luong nen JPEG khi tra khung hinh ve client - 80 la muc can bang pho
# bien (dung lai duoc tren mang chat luong kha tot ma dung luong khong qua
# nang), CHUA phai gia tri toi uu do tre (viec do thuoc Giai doan 3 theo
# dung ke hoach da chot, xem CLAUDE_PROGRESS.md muc 24).
JPEG_ENCODE_PARAMS = [int(cv2.IMWRITE_JPEG_QUALITY), 80]


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

        try:
            # Khoi tao FaceLandmarker la thao tac I/O + CPU dang ke (doc file
            # model ~3.6MB, dung mang) - day qua thread de khong chan event
            # loop luc client khac dang ket noi cung luc.
            self._detector = await sync_to_async(FaceMeshDetector, thread_sensitive=False)(MODEL_PATH)
            # #region DEBUG
            _debug_log("[H4] connect() OK, FaceMeshDetector khoi tao thanh cong")
            # #endregion DEBUG
        except FileNotFoundError as e:
            # #region DEBUG
            _debug_log(f"[H4] connect() LOI khoi tao FaceMeshDetector: {e}")
            # #endregion DEBUG
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
            # #region DEBUG
            _debug_log(f"[H3] _select_glasses: KHONG tim thay row id={glasses_id}")
            # #endregion DEBUG
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
        # #region DEBUG
        _debug_log(
            f"[H3] _select_glasses OK id={glasses_id} image={row.image.path} "
            f"lens_left={renderer._lens_left} lens_right={renderer._lens_right}"
        )
        # #endregion DEBUG

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

    def _process_frame_sync(self, jpeg_bytes: bytes):
        """Toan bo pipeline CPU-bound (decode -> chuan hoa anh sang ->
        MediaPipe -> dan kinh -> encode lai) - HAM DONG BO, luon duoc goi
        qua sync_to_async(..., thread_sensitive=False) o tren, KHONG duoc
        goi truc tiep tu ham async (se chan event loop cua toan bo server)."""
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

        frame = self._normalizer.normalize(frame)

        elapsed_ms = int((time.perf_counter() - self._start_time) * 1000)
        result = self._detector.detect(frame, elapsed_ms)

        frame_h, frame_w = frame.shape[:2]
        anchors = FaceMeshDetector.get_eye_anchor_points(result, frame_w, frame_h)
        face_detected = anchors is not None

        renderer = self._renderers.get(self._current_glasses_id)
        if face_detected and renderer is not None:
            pt_a, pt_b = anchors
            frame = renderer.render_on_frame_auto(frame, pt_a, pt_b)
        # Khong co mat HOAC chua chon mau kinh nao -> tra khung hinh GOC (da
        # chuan hoa anh sang) khong dan gi ca, dung theo dung yeu cau muc 24
        # ("Khong co mat trong khung -> tra khung hinh goc + co bao").

        # #region DEBUG
        _debug_log(
            f"[H3] frame {frame_w}x{frame_h} face_detected={face_detected} "
            f"current_glasses_id={self._current_glasses_id} renderer_exists={renderer is not None} "
            f"da_dan_kinh={face_detected and renderer is not None}"
        )
        # #endregion DEBUG

        ok, buf = cv2.imencode(".jpg", frame, JPEG_ENCODE_PARAMS)
        if not ok:
            return None

        status_byte = bytes([1 if face_detected else 0])
        return status_byte + buf.tobytes()
