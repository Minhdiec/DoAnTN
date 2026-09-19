r"""Do FPS bang cach goi TRUC TIEP TryOnConsumer._process_frame_sync (dung
HAM THAT trong tryon/consumers.py, khong viet lai/copy logic) - bo qua lop
Channels/ASGI (channels.testing.WebsocketCommunicator bi treo khong ro
nguyen nhan khi thu, xem CLAUDE_PROGRESS.md muc 38 - khong phai muc tieu
toi uu cua Giai doan 3). Cach nay do DUNG 100% chi phi CPU thuc cua pipeline
xu ly anh (decode -> [CLAHE] -> MediaPipe -> dan kinh -> encode) ma Giai
doan 3 nham toi, chi bo qua phan framework/mang WebSocket.

Dung de tai lap bang FPS truoc/sau da ghi trong CLAUDE_PROGRESS.md muc 38.
Chay (tu thu muc goc project):
    .venv\Scripts\python.exe scripts\bench_tryon_direct.py [glasses_id] [n_frames]
"""
import os
import sys
import time
from collections import deque
from pathlib import Path

import django

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import cv2
import numpy as np

from tryon.consumers import TryOnConsumer
from tryon.models import GlassesOverlay as GlassesOverlayModel
from tryon.vision import AnchorSmoother, FaceMeshDetector, GlassesOverlay as GlassesRenderer, LightNormalizer

# Anh test co san trong media/avatars/ (khong lien quan tinh nang avatar -
# chi muon 1 anh co mat nguoi ro that de benchmark). Da do thu vung crop
# nay de MediaPipe nhan dien duoc mat (xem CLAUDE_PROGRESS.md muc 38).
FACE_IMAGE_PATH = PROJECT_ROOT / "media" / "avatars" / "4.jpg"
MODEL_PATH = str(PROJECT_ROOT / "prototype" / "models" / "face_landmarker.task")
WARMUP_FRAMES = 5


def build_test_frame_jpeg() -> bytes:
    with open(FACE_IMAGE_PATH, "rb") as f:
        data = f.read()
    img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(FACE_IMAGE_PATH)
    crop = img[1000:2200, 1400:2400]
    frame = cv2.resize(crop, (640, 480), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ok:
        raise RuntimeError("khong encode duoc khung hinh test")
    return buf.tobytes()


def build_consumer(glasses_id: int) -> TryOnConsumer:
    """Tao 1 instance TryOnConsumer o dung trang thai NHU SAU KHI
    connect() + select_glasses() chay xong (khong qua async/Channels), roi
    goi truc tiep _process_frame_sync - dung THAT cac ten thuoc tinh trong
    consumers.py nen se tu bao loi (AttributeError) neu sau nay connect()
    doi ten, nhac cap nhat script nay theo."""
    consumer = TryOnConsumer.__new__(TryOnConsumer)
    consumer._normalizer = LightNormalizer()
    consumer._renderers = {}
    consumer._current_glasses_id = None
    consumer._start_time = time.perf_counter()
    consumer._detector = FaceMeshDetector(MODEL_PATH)
    consumer._last_face_box = None
    consumer._last_raw_anchors = None
    consumer._last_detect_ms = float("-inf")
    consumer._smoother = AnchorSmoother()
    consumer._frame_timestamps = deque(maxlen=200)
    consumer._frame_process_ms_sum = 0.0
    consumer._frame_process_count = 0
    consumer._last_fps_log = time.perf_counter()

    row = GlassesOverlayModel.objects.get(pk=glasses_id)
    renderer = GlassesRenderer(row.image.path, row.width_ratio, row.vertical_offset)
    consumer._renderers[glasses_id] = renderer
    consumer._current_glasses_id = glasses_id
    return consumer


def run_benchmark(glasses_id: int, n_frames: int):
    jpeg_bytes = build_test_frame_jpeg()
    consumer = build_consumer(glasses_id)

    face_detected_count = 0
    per_frame_ms = []

    for _ in range(WARMUP_FRAMES):
        consumer._process_frame_sync(jpeg_bytes)

    t_start = time.perf_counter()
    for _ in range(n_frames):
        t0 = time.perf_counter()
        result = consumer._process_frame_sync(jpeg_bytes)
        t1 = time.perf_counter()
        per_frame_ms.append((t1 - t0) * 1000.0)
        if result is not None and len(result) >= 1 and result[0] == 1:
            face_detected_count += 1
    total_elapsed = time.perf_counter() - t_start

    fps = n_frames / total_elapsed if total_elapsed > 0 else 0.0
    avg_ms = sum(per_frame_ms) / len(per_frame_ms)
    p95_ms = sorted(per_frame_ms)[int(len(per_frame_ms) * 0.95) - 1]

    print(f"So khung hinh          : {n_frames}")
    print(f"Tong thoi gian          : {total_elapsed:.3f} s")
    print(f"FPS (pipeline thuc)     : {fps:.2f}")
    print(f"Trung binh moi khung    : {avg_ms:.1f} ms")
    print(f"p95 moi khung           : {p95_ms:.1f} ms")
    print(f"Khung phat hien mat     : {face_detected_count}/{n_frames} ({face_detected_count / n_frames * 100:.1f}%)")


if __name__ == "__main__":
    glasses_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    n_frames = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    run_benchmark(glasses_id, n_frames)
