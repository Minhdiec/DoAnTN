"""
Ghi đè định dạng số cho locale "vi".

Bộ định dạng "vi" có sẵn của Django khai báo THOUSAND_SEPARATOR = "." nhưng
lại không bật NUMBER_GROUPING (mặc định = 0, tức KHÔNG chèn dấu phân cách
hàng nghìn), khiến filter "intcomma" hiển thị giá tiền dạng "4064000" thay
vì "4.064.000". File này bật lại NUMBER_GROUPING = 3 để giá tiền hiển thị
đúng kiểu Việt Nam trên toàn bộ site.
"""

THOUSAND_SEPARATOR = "."
NUMBER_GROUPING = 3
DECIMAL_SEPARATOR = ","
