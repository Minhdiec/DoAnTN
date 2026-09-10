// Widget chọn số sao (1-5) cho form đánh giá sản phẩm: bấm vào 1 ngôi sao sẽ
// tô đậm các sao từ trái tới đó và ghi giá trị vào input ẩn "rating".
document.addEventListener("DOMContentLoaded", function () {
    var wrapper = document.querySelector("[data-star-input]");
    var hiddenInput = document.getElementById("id_rating");

    if (!wrapper || !hiddenInput) {
        return;
    }

    var buttons = wrapper.querySelectorAll("[data-star-value]");

    function setRating(value) {
        hiddenInput.value = value;
        buttons.forEach(function (btn) {
            var starValue = Number(btn.getAttribute("data-star-value"));
            var filled = starValue <= value;
            btn.classList.toggle("is-filled", filled);
            // Đổi luôn ký tự sao (★/☆), không chỉ đổi màu - để vẫn phân biệt
            // được sao đã chọn ngay cả khi CSS chưa kịp tải/cache cũ.
            btn.textContent = filled ? "★" : "☆";
        });
    }

    buttons.forEach(function (btn) {
        btn.addEventListener("click", function () {
            setRating(Number(btn.getAttribute("data-star-value")));
        });
    });

    if (hiddenInput.value) {
        setRating(Number(hiddenInput.value));
    }
});
