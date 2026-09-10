"""
Form cho app "reviews". Việc tải nhiều ảnh/video được xử lý riêng trong view
qua request.FILES.getlist() (Django ModelForm không hỗ trợ sẵn 1 trường nhận
nhiều file), nên form này chỉ gồm rating/content/is_anonymous.
"""

from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "content", "is_anonymous"]
        widgets = {
            # Số sao được chọn bằng widget JS (xem static/js/review-form.js),
            # input thật chỉ ẩn đi để gửi kèm giá trị lên server.
            "rating": forms.HiddenInput(),
            "content": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Chia sẻ cảm nhận của bạn về sản phẩm...",
                }
            ),
        }
        labels = {
            "content": "Nội dung đánh giá",
            "is_anonymous": "Ẩn danh (không hiển thị tên của bạn công khai)",
        }

    def clean_rating(self):
        rating = self.cleaned_data["rating"]
        if not 1 <= rating <= 5:
            raise forms.ValidationError("Vui lòng chọn số sao từ 1 đến 5.")
        return rating
