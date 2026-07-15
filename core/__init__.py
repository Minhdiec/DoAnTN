# File này chạy MỘT LẦN DUY NHẤT ngay khi Python import package "core"
# (tức là ngay khi Django khởi động). Ta tận dụng nó để "giả lập" thư viện
# PyMySQL thành mysqlclient (module tên là MySQLdb) - thư viện mà Django
# mặc định mong đợi khi ENGINE = "django.db.backends.mysql".
#
# Lý do dùng PyMySQL thay vì mysqlclient: PyMySQL là thư viện Python thuần,
# cài đặt chỉ bằng "pip install PyMySQL", không cần trình biên dịch C như
# mysqlclient (rất hay gặp lỗi khi cài trên Windows).
import pymysql

pymysql.install_as_MySQLdb()
