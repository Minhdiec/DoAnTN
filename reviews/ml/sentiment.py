"""
Dự đoán nhãn cảm xúc (POS/NEU/NEG) cho nội dung đánh giá sản phẩm.

Mô hình (`sentiment_model.joblib`, gồm TfidfVectorizer + LogisticRegression)
được huấn luyện ở phantichcamxuc/sentiment_analysis.ipynb - xem file đó để
biết cách huấn luyện, so sánh mô hình và các chỉ số đánh giá.

QUAN TRỌNG: hàm clean_text() và cách tách từ ở predict_sentiment() bên dưới
PHẢI giống hệt bước tiền xử lý lúc train, nếu không vector hóa câu mới sẽ
lệch không gian đặc trưng với lúc train, khiến mô hình dự đoán sai lệch.
"""

import re
from functools import lru_cache
from pathlib import Path

import joblib
from underthesea import word_tokenize

MODEL_PATH = Path(__file__).resolve().parent / "sentiment_model.joblib"


def clean_text(text: str) -> str:
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([!?.,])\1+", r"\1", text)
    return text


@lru_cache(maxsize=1)
def _load_bundle():
    # Nạp model MỘT LẦN DUY NHẤT rồi cache lại: file .joblib vài trăm KB,
    # đọc lại từ đĩa mỗi lần có đánh giá mới sẽ làm chậm request không cần thiết.
    return joblib.load(MODEL_PATH)


def predict_sentiment(text: str):
    """Trả về tuple (nhãn, độ tin cậy). Nhãn là 'POS'/'NEU'/'NEG'."""
    bundle = _load_bundle()
    processed = word_tokenize(clean_text(text), format="text")
    vector = bundle["vectorizer"].transform([processed])
    proba = bundle["model"].predict_proba(vector)[0]
    label = bundle["model"].classes_[proba.argmax()]
    confidence = float(proba.max())
    return label, confidence
