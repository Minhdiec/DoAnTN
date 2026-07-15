"""
Django settings cho dự án core (ChuyenDeTN).

File này là "bộ não cấu hình" của toàn bộ website: khai báo những app nào
được bật, kết nối tới database nào, thư mục template/static/media nằm ở
đâu, v.v. Mọi thứ liên quan đến "hạ tầng" của dự án đều nằm ở đây, còn
logic nghiệp vụ (sản phẩm, ví tiền...) thì nằm trong từng app riêng.
"""

import os
from pathlib import Path

# python-dotenv cho phép ta đọc các biến cấu hình nhạy cảm (mật khẩu MySQL,
# SECRET_KEY...) từ một file ".env" nằm ngoài source code, thay vì viết
# thẳng (hardcode) chúng vào file settings.py rồi lỡ tay đẩy lên GitHub.
from dotenv import load_dotenv

# BASE_DIR là đường dẫn tuyệt đối tới thư mục gốc của dự án, tức là thư mục
# chứa file manage.py. Từ đây ta sẽ ghép (BASE_DIR / "ten_thu_muc") để ra
# đường dẫn tới các thư mục con khác một cách an toàn trên mọi hệ điều hành.
"""# File hiện tại: Project/core/settings.py

__file__                 # 'Project/core/settings.py'
Path(__file__)           # Path('Project/core/settings.py')
.resolve()               # Path('/đường/dẫn/đầy/đủ/Project/core/settings.py')
.parent                  # Path('/đường/dẫn/đầy/đủ/Project/core')
.parent.parent           # Path('/đường/dẫn/đầy/đủ/Project') ← Đây là BASE_DIR"""
BASE_DIR = Path(__file__).resolve().parent.parent

# Nạp toàn bộ biến trong file ".env" (nằm cùng cấp với manage.py) vào biến
# môi trường của tiến trình Python đang chạy. Nếu file .env chưa tồn tại,
# lệnh này sẽ không báo lỗi, chỉ đơn giản là không nạp được gì cả.
load_dotenv(BASE_DIR / ".env")


def get_env(key, default=None):
    """
    Hàm tiện ích: đọc một biến môi trường theo tên "key".
    Nếu biến đó không tồn tại trong file .env hoặc trong hệ điều hành,
    hàm sẽ trả về giá trị "default" mà ta truyền vào, tránh cho chương
    trình bị crash vì thiếu cấu hình.
    """
    return os.environ.get(key, default)


# ---------------------------------------------------------------------------
# BẢO MẬT
# ---------------------------------------------------------------------------

# SECRET_KEY được Django dùng để mã hóa session, token CSRF, v.v.
# Trong môi trường thật (production) TUYỆT ĐỐI không được lộ giá trị này,
# nên ta đọc nó từ file .env. Nếu file .env chưa có, dùng tạm giá trị mặc
# định phía sau dấu phẩy để code vẫn chạy được khi mới clone dự án về.
SECRET_KEY = get_env(
    "DJANGO_SECRET_KEY",
    "django-insecure-(t3aebzmboot&+0ay7lw*r3dnf23^fsup%#(9!v961&@i*=sqs",
)

# DEBUG = True nghĩa là đang ở môi trường phát triển (development): Django
# sẽ hiển thị trang lỗi chi tiết khi có exception, giúp ta dễ debug.
# Khi đưa lên server thật, PHẢI đổi thành False để không lộ thông tin nội bộ.
DEBUG = get_env("DJANGO_DEBUG", "True") == "True"

# Danh sách các tên miền/IP được phép truy cập vào website này.
# Khi DEBUG=True thì Django cho phép để trống danh sách này.
ALLOWED_HOSTS = get_env("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")


# ---------------------------------------------------------------------------
# KHAI BÁO ỨNG DỤNG (APPS)
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    # --- Các app có sẵn của Django ---
    "django.contrib.admin",  # Trang quản trị /admin
    "django.contrib.auth",  # Hệ thống đăng nhập, phân quyền
    "django.contrib.contenttypes",  # Hỗ trợ nội bộ cho auth/admin
    "django.contrib.sessions",  # Quản lý phiên đăng nhập
    "django.contrib.messages",  # Cơ chế thông báo (flash message)
    "django.contrib.staticfiles",  # Quản lý file CSS/JS/ảnh tĩnh
    "django.contrib.humanize",  # Cung cấp filter format số (intcomma) để hiển thị giá tiền đẹp hơn

    # --- Các app tự viết cho dự án (mỗi app đảm nhiệm một mảng nghiệp vụ) ---
    "accounts",  # Người dùng (User tùy biến), đăng ký/đăng nhập
    "products",  # Sản phẩm, danh mục sản phẩm
    "wishlist",  # Danh sách yêu thích
    "wallet",  # Ví điện tử, lịch sử giao dịch
    "cart",  # Giỏ hàng
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Tên module chứa danh sách URL gốc của dự án (chính là file core/urls.py).
ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # DIRS: nơi Django tìm các file .html dùng CHUNG cho nhiều app,
        # ví dụ base.html (khung sườn trang), navbar.html, footer.html...
        "DIRS": [BASE_DIR / "templates"],
        # APP_DIRS = True: ngoài thư mục templates chung ở trên, Django còn
        # tự động tìm thêm trong thư mục "templates/" nằm bên trong từng app
        # (ví dụ products/templates/products/...).
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.cart_summary",
            ],
        },
    },
]

# Đường dẫn tới ứng dụng WSGI, dùng khi triển khai server thật (Gunicorn...).
WSGI_APPLICATION = "core.wsgi.application"


# ---------------------------------------------------------------------------
# CƠ SỞ DỮ LIỆU (DATABASE) - KẾT NỐI MYSQL
# ---------------------------------------------------------------------------
#
# Mặc định khi chạy "django-admin startproject", Django dùng SQLite (một
# file .db nằm ngay trong dự án). SQLite tiện cho việc học và test nhanh,
# nhưng không phù hợp cho một website thương mại điện tử thật sự (nhiều
# người dùng ghi dữ liệu đồng thời). Vì vậy ta đổi sang MySQL.
#
# Driver kết nối: thay vì cài "mysqlclient" (thường rất khó build trên
# Windows vì cần trình biên dịch C), dự án này dùng PyMySQL - một thư viện
# Python thuần, cài đặt rất đơn giản bằng "pip install PyMySQL". Đoạn code
# "giả lập" PyMySQL thành mysqlclient được đặt trong core/__init__.py.
#
# Toàn bộ thông tin đăng nhập MySQL (tên database, user, password, host,
# port) đều được đọc từ file .env, KHÔNG hardcode trong source code, để:
#   1) Không lộ mật khẩu khi đưa code lên GitHub.
#   2) Mỗi máy (máy cá nhân, máy thầy cô chấm bài, server thật) có thể
#      dùng một cấu hình MySQL khác nhau mà không cần sửa code.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": get_env("DB_NAME", "chuyendetn_db"),
        "USER": get_env("DB_USER", "root"),
        "PASSWORD": get_env("DB_PASSWORD", ""),
        "HOST": get_env("DB_HOST", "127.0.0.1"),
        "PORT": get_env("DB_PORT", "3306"),
        "OPTIONS": {
            # utf8mb4 cho phép lưu đầy đủ tiếng Việt có dấu và cả emoji,
            # khác với utf8 mặc định của MySQL (chỉ lưu được 3 byte/ký tự).
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# ---------------------------------------------------------------------------
# XÁC THỰC NGƯỜI DÙNG (AUTHENTICATION)
# ---------------------------------------------------------------------------

# Báo cho Django biết: "Đừng dùng User mặc định của Django nữa, hãy dùng
# model User do chính app 'accounts' định nghĩa (xem accounts/models.py)."
# Việc khai báo AUTH_USER_MODEL PHẢI làm ngay từ đầu dự án, trước khi chạy
# migrate lần đầu tiên, vì Django rất khó đổi lại sau khi đã có dữ liệu.
AUTH_USER_MODEL = "accounts.User"

# Khi một view yêu cầu đăng nhập (@login_required) mà người dùng chưa đăng
# nhập, Django sẽ tự động chuyển hướng họ tới URL có tên "login" này.
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "products:home"
LOGOUT_REDIRECT_URL = "products:home"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ---------------------------------------------------------------------------
# NGÔN NGỮ & MÚI GIỜ
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

# Ghi đè định dạng số mặc định của locale "vi" (xem core/formats/vi/formats.py)
# để giá tiền hiển thị đúng kiểu Việt Nam, ví dụ "4.064.000" thay vì "4064000".
FORMAT_MODULE_PATH = "core.formats"


# ---------------------------------------------------------------------------
# STATIC FILES (CSS, JavaScript) & MEDIA FILES (ảnh do người dùng upload)
# ---------------------------------------------------------------------------

# STATIC_URL: tiền tố URL để trình duyệt truy cập file tĩnh, ví dụ:
# /static/css/style.css
STATIC_URL = "static/"

# STATICFILES_DIRS: nơi Django tìm file CSS/JS "thô" trong lúc phát triển
# (thư mục static/ nằm ở gốc dự án, KHÔNG nằm trong app nào cụ thể).
STATICFILES_DIRS = [BASE_DIR / "static"]

# STATIC_ROOT: nơi lệnh "python manage.py collectstatic" sẽ gom TẤT CẢ file
# tĩnh (từ mọi app + STATICFILES_DIRS) về một chỗ duy nhất để deploy lên
# server thật. Thư mục này không cần tạo tay, Django tự tạo khi chạy lệnh.
STATIC_ROOT = BASE_DIR / "staticfiles"

# MEDIA_URL: tiền tố URL để trình duyệt truy cập ảnh do người dùng upload,
# ví dụ ảnh sản phẩm sẽ có đường dẫn dạng /media/products/ao-thun.jpg
MEDIA_URL = "media/"

# MEDIA_ROOT: thư mục vật lý trên ổ đĩa, nơi Django thực sự lưu các file
# ảnh khi người dùng upload (ví dụ ảnh sản phẩm, ảnh đại diện...).
MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------------------
# CẤU HÌNH KHÁC
# ---------------------------------------------------------------------------

# Kiểu dữ liệu mặc định cho cột khóa chính (id) tự tăng của mọi model,
# BigAutoField hỗ trợ số lượng bản ghi lớn hơn AutoField mặc định cũ.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
