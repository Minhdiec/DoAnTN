// Tương tác giao diện nhỏ cho toàn bộ site (không phụ thuộc thư viện ngoài).
document.addEventListener("DOMContentLoaded", function () {
    var toggle = document.querySelector(".menu-toggle");
    var categoryNav = document.querySelector(".category-nav");

    if (toggle && categoryNav) {
        toggle.addEventListener("click", function () {
            categoryNav.classList.toggle("is-open");
        });
    }

    initProductFilters();
    initProductGallery();
    initQuantitySteppers();
});

// Lọc sản phẩm trên trang chủ theo giới tính (Nữ/Nam) và dáng kính
// (Oval, Vuông, Tròn...) hoàn toàn phía client, không cần tải lại trang.
function initProductFilters() {
    var genderTabs = document.querySelectorAll("[data-gender-filter]");
    var shapeCards = document.querySelectorAll("[data-shape-filter]");
    var productCards = document.querySelectorAll(".product-card[data-gender]");
    var emptyState = document.querySelector("[data-filter-empty]");
    var activeChip = document.querySelector("[data-active-shape-chip]");
    var activeChipName = document.querySelector("[data-active-shape-name]");
    var clearShapeBtn = document.querySelector("[data-clear-shape]");
    var productsSection = document.getElementById("featured-products");

    if (!productCards.length) {
        return;
    }

    var state = { gender: "all", shape: "all" };

    function apply() {
        var visibleCount = 0;
        productCards.forEach(function (card) {
            var g = card.getAttribute("data-gender");
            var s = card.getAttribute("data-shape");
            var genderMatch = state.gender === "all" || g === state.gender || g === "unisex";
            var shapeMatch = state.shape === "all" || s === state.shape;
            var show = genderMatch && shapeMatch;
            card.style.display = show ? "" : "none";
            if (show) {
                visibleCount += 1;
            }
        });
        if (emptyState) {
            emptyState.hidden = visibleCount !== 0;
        }
    }

    genderTabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            state.gender = tab.getAttribute("data-gender-filter");
            genderTabs.forEach(function (t) {
                t.classList.toggle("is-active", t === tab);
            });
            apply();
        });
    });

    shapeCards.forEach(function (card) {
        card.addEventListener("click", function () {
            var value = card.getAttribute("data-shape-filter");
            state.shape = state.shape === value ? "all" : value;

            shapeCards.forEach(function (c) {
                c.classList.toggle("is-active", c.getAttribute("data-shape-filter") === state.shape);
            });

            if (activeChip) {
                if (state.shape === "all") {
                    activeChip.hidden = true;
                } else {
                    activeChip.hidden = false;
                    if (activeChipName) {
                        var nameEl = card.querySelector("span:nth-child(2)");
                        activeChipName.textContent = nameEl ? nameEl.textContent : value;
                    }
                }
            }

            apply();

            if (productsSection) {
                productsSection.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });

    if (clearShapeBtn) {
        clearShapeBtn.addEventListener("click", function () {
            state.shape = "all";
            shapeCards.forEach(function (c) {
                c.classList.remove("is-active");
            });
            if (activeChip) {
                activeChip.hidden = true;
            }
            apply();
        });
    }

    apply();
}

// Đổi ảnh chính khi bấm vào thumbnail trên trang chi tiết sản phẩm.
function initProductGallery() {
    var mainImage = document.querySelector("[data-gallery-main]");
    var thumbs = document.querySelectorAll("[data-gallery-thumb]");

    if (!mainImage || !thumbs.length) {
        return;
    }

    thumbs.forEach(function (thumb) {
        thumb.addEventListener("click", function () {
            var fullUrl = thumb.getAttribute("data-full");
            if (!fullUrl) {
                return;
            }
            mainImage.src = fullUrl;
            thumbs.forEach(function (t) {
                t.classList.toggle("is-active", t === thumb);
            });
        });
    });
}

// Nút +/- cho ô nhập số lượng (dùng ở trang chi tiết sản phẩm và trang giỏ
// hàng). Mỗi ".quantity-stepper" trên trang tự tìm input/nút của riêng nó,
// nên có thể có nhiều bộ đếm cùng lúc mà không ảnh hưởng lẫn nhau.
function initQuantitySteppers() {
    document.querySelectorAll(".quantity-stepper").forEach(function (stepper) {
        var input = stepper.querySelector("[data-qty-input]");
        var decreaseBtn = stepper.querySelector("[data-qty-decrease]");
        var increaseBtn = stepper.querySelector("[data-qty-increase]");

        if (!input) {
            return;
        }

        function clamp(value) {
            var min = parseInt(input.getAttribute("min"), 10) || 1;
            var max = parseInt(input.getAttribute("max"), 10) || Infinity;
            return Math.min(Math.max(value, min), max);
        }

        if (decreaseBtn) {
            decreaseBtn.addEventListener("click", function () {
                input.value = clamp((parseInt(input.value, 10) || 1) - 1);
            });
        }

        if (increaseBtn) {
            increaseBtn.addEventListener("click", function () {
                input.value = clamp((parseInt(input.value, 10) || 1) + 1);
            });
        }

        input.addEventListener("change", function () {
            input.value = clamp(parseInt(input.value, 10) || 1);
        });
    });
}
