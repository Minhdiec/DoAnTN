# #region DEBUG
"""File TAM THOI phuc vu debug-mode (xem CLAUDE_PROGRESS.md - khong ghi vao
progress vi day chi la cong cu chan doan, se bi XOA hoan toan sau khi fix
xong va nguoi dung xac nhan). Nhan tin nhan debug tu JS phia trinh duyet
(khong the tu ghi file truc tiep) va ghi vao .claude/debug.log."""

from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

DEBUG_LOG_PATH = Path(settings.BASE_DIR) / ".claude" / "debug.log"


@csrf_exempt
def debug_log_view(request):
    DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(request.body.decode("utf-8", errors="replace") + "\n")
    return HttpResponse("ok")
# #endregion DEBUG
