r"""Bang so sanh FPS truoc/sau TUNG KY THUAT cua Giai doan 3 (yeu cau cua
CLAUDE_PROGRESS.md muc 11: "ap tung ky thuat va do FPS truoc/sau tung cai,
lap bang so sanh"), bang cach monkeypatch tam thoi cac hang so/ham trong
tryon.consumers/tryon.vision de TAT rieng 1 ky thuat, giu cac ky thuat con
lai nguyen, roi so voi ban DA TOI UU DAY DU (5 ky thuat) - CHAY TREN HAM
THAT trong code (khong viet lai logic), chi doi tham so/hanh vi tu ben
ngoai qua monkeypatch. Ket qua da ghi lai trong CLAUDE_PROGRESS.md muc 38.

Chay (tu thu muc goc project):
    .venv\Scripts\python.exe scripts\bench_tryon_ablation.py
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

import tryon.consumers as consumers_mod
from tryon.consumers import TryOnConsumer
from tryon.models import GlassesOverlay as GlassesOverlayModel
from tryon.vision import AnchorSmoother, FaceMeshDetector, GlassesOverlay as GlassesRenderer, LightNormalizer

FACE_IMAGE_PATH = PROJECT_ROOT / "media" / "avatars" / "4.jpg"
MODEL_PATH = str(PROJECT_ROOT / "prototype" / "models" / "face_landmarker.task")
WARMUP_FRAMES = 5
N_FRAMES = 120
GLASSES_ID = 1


def build_test_frame_jpeg() -> bytes:
    with open(FACE_IMAGE_PATH, "rb") as f:
        data = f.read()
    img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    crop = img[1000:2200, 1400:2400]
    frame = cv2.resize(crop, (640, 480), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    return buf.tobytes()


def build_consumer() -> TryOnConsumer:
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

    row = GlassesOverlayModel.objects.get(pk=GLASSES_ID)
    renderer = GlassesRenderer(row.image.path, row.width_ratio, row.vertical_offset)
    consumer._renderers[GLASSES_ID] = renderer
    consumer._current_glasses_id = GLASSES_ID
    return consumer


def run_config(label: str, jpeg_bytes: bytes):
    consumer = build_consumer()
    for _ in range(WARMUP_FRAMES):
        consumer._process_frame_sync(jpeg_bytes)

    t0 = time.perf_counter()
    for _ in range(N_FRAMES):
        consumer._process_frame_sync(jpeg_bytes)
    elapsed = time.perf_counter() - t0

    fps = N_FRAMES / elapsed
    avg_ms = elapsed / N_FRAMES * 1000.0
    print(f"{label:<60} FPS={fps:6.2f}   avg={avg_ms:5.1f} ms")
    return fps, avg_ms


def main():
    jpeg_bytes = build_test_frame_jpeg()

    orig = dict(
        MIN_DETECT_INTERVAL_MS=consumers_mod.MIN_DETECT_INTERVAL_MS,
        DETECT_DOWNSCALE_WIDTH=consumers_mod.DETECT_DOWNSCALE_WIDTH,
        ROI_DETECT_SIZE=consumers_mod.ROI_DETECT_SIZE,
        ROI_PADDING_RATIO=consumers_mod.ROI_PADDING_RATIO,
    )
    orig_is_low_light = LightNormalizer.is_low_light
    orig_smooth = AnchorSmoother.smooth
    orig_select_region = TryOnConsumer._select_detection_region

    def _always_full_frame(self, frame):
        frame_h, frame_w = frame.shape[:2]
        return frame, (0, 0), (frame_w, frame_h)

    print("=" * 90)
    print(f"Anh test: {FACE_IMAGE_PATH} (crop mat), {N_FRAMES} khung/config, warmup={WARMUP_FRAMES}")
    print("=" * 90)

    run_config("FULL (5/5 ky thuat, sau toi uu)", jpeg_bytes)

    AnchorSmoother.smooth = lambda self, pt_a, pt_b, ts: (pt_a, pt_b)
    run_config("- TAT ky thuat 3 (bo smoothing)", jpeg_bytes)
    AnchorSmoother.smooth = orig_smooth

    LightNormalizer.is_low_light = lambda self, frame: True
    run_config("- TAT ky thuat 5a (CLAHE luon chay, bo is_low_light gating)", jpeg_bytes)
    LightNormalizer.is_low_light = orig_is_low_light

    # Van cat ROI (khoanh vung quanh mat) nhung KHONG resize nho di truoc detect.
    consumers_mod.ROI_DETECT_SIZE = 480
    run_config("- TAT ky thuat 5b (ROI van khoanh vung, khong giam do phan giai)", jpeg_bytes)
    consumers_mod.ROI_DETECT_SIZE = orig["ROI_DETECT_SIZE"]

    consumers_mod.MIN_DETECT_INTERVAL_MS = 0.0
    run_config("- TAT ky thuat 2 (detect moi khung, van co ROI)", jpeg_bytes)
    consumers_mod.MIN_DETECT_INTERVAL_MS = orig["MIN_DETECT_INTERVAL_MS"]

    TryOnConsumer._select_detection_region = _always_full_frame
    consumers_mod.MIN_DETECT_INTERVAL_MS = 0.0
    run_config("- TAT ky thuat 1+2+5 (detect moi khung, full-frame, nhu truoc GD3)", jpeg_bytes)
    TryOnConsumer._select_detection_region = orig_select_region
    consumers_mod.MIN_DETECT_INTERVAL_MS = orig["MIN_DETECT_INTERVAL_MS"]

    # Sanity check: tat het 4 ky thuat co the tat cung luc -> phai ra so gan
    # baseline goc (~33 FPS, do truoc khi sua code) de xac nhan refactor
    # khong lam sai pipeline, chi lam nhanh hon.
    AnchorSmoother.smooth = lambda self, pt_a, pt_b, ts: (pt_a, pt_b)
    LightNormalizer.is_low_light = lambda self, frame: True
    TryOnConsumer._select_detection_region = _always_full_frame
    consumers_mod.MIN_DETECT_INTERVAL_MS = 0.0
    run_config("TAT CA (doi chieu voi baseline goc ~33 FPS)", jpeg_bytes)
    AnchorSmoother.smooth = orig_smooth
    LightNormalizer.is_low_light = orig_is_low_light
    TryOnConsumer._select_detection_region = orig_select_region
    consumers_mod.MIN_DETECT_INTERVAL_MS = orig["MIN_DETECT_INTERVAL_MS"]

    print("=" * 90)
    print("(Ky thuat 4 - cache renderer PNG - da co tu truoc Giai doan 3, khong tat duoc")
    print(" cong bang trong 1 phien vi renderer chi tao 1 lan luc build_consumer(); xem")
    print(" CLAUDE_PROGRESS.md muc 38 phan ghi chu rieng cho ky thuat 4.)")


if __name__ == "__main__":
    main()
