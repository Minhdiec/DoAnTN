import os
import sys
import time

from django.apps import AppConfig


class TryonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tryon'

    def ready(self):
        # "Lam nong" MediaPipe FaceLandmarker 1 LAN khi server THUC SU khoi
        # dong - xem CLAUDE_PROGRESS.md muc 40 (bug "nhan dang kinh len mat
        # hoi lau"): da do duoc lan TAO FaceMeshDetector DAU TIEN trong 1
        # tien trinh Python ton ~3-6 GIAY (MediaPipe/TFLite/XNNPACK tu khoi
        # tao kernel tinh toan + nap graph mo hinh), nhung lan TAO THU 2, 3
        # trong CUNG tien trinh chi con ~25ms (~100 lan nhanh hon) - chi phi
        # do la 1 LAN CHO CA TIEN TRINH, khong phai cho tung instance.
        #
        # Truoc day chi phi nay roi vao dung lan `connect()` CUA NGUOI DUNG
        # DAU TIEN sau moi lan server khoi dong/tu nap lai (autoreload moi
        # khi sua file .py) - nguoi dung do thay "nhan dang kinh len mat
        # hoi lau" chinh vi rơi trung luc nay. Chuyen chi phi nay ra day (1
        # LAN luc `python manage.py runserver` khoi dong, TRUOC KHI ai mo
        # trang web) de moi ket noi WebSocket THUC SU cua nguoi dung sau do
        # deu nhanh nhu lan tao thu 2/3 (~25ms) chu khong con roi vao ai ca.
        #
        # Chi chay khi THUC SU la `runserver` (khong chay khi migrate/
        # makemigrations/shell/test - khong can va se lam cham cac lenh do
        # vo ich) - VA chi trong tien trinh WORKER thuc su phuc vu request
        # (khong chay 2 lan o tien trinh "watcher" ngoai cua autoreload):
        # RUN_MAIN='true' CHI duoc Django dat trong tien trinh con khi
        # autoreload dang bat; neu chay voi --noreload thi khong co tien
        # trinh con rieng, ready() chay thang trong tien trinh chinh.
        if "runserver" not in sys.argv:
            return
        if os.environ.get("RUN_MAIN") != "true" and "--noreload" not in sys.argv:
            return

        from threading import Thread
        Thread(target=_warm_up_face_landmarker, daemon=True).start()


def _warm_up_face_landmarker() -> None:
    from django.conf import settings

    from .vision import FaceMeshDetector

    model_path = str(settings.BASE_DIR / "prototype" / "models" / "face_landmarker.task")
    print("[TryOn] Dang lam nong MediaPipe FaceLandmarker (1 lan luc khoi dong server)...")
    t0 = time.perf_counter()
    try:
        detector = FaceMeshDetector(model_path)
        detector.close()
    except FileNotFoundError as e:
        print(f"[TryOn] BO QUA lam nong - khong tim thay model: {e}")
        return
    print(f"[TryOn] Lam nong xong sau {(time.perf_counter() - t0) * 1000:.0f} ms - "
          f"cac ket noi WebSocket thu kinh tu gio se nhanh ngay tu lan dau.")
