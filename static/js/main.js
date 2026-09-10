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
    initPaymentModal();
    initAjaxCart();
    initConfirmForms();
});

// Bất kỳ <form> nào gắn thuộc tính "data-confirm" (ví dụ nút "Hủy đơn hàng")
// đều được hỏi xác nhận trước khi submit thật - dùng chung 1 hàm thay vì
// viết onclick="confirm(...)" rải rác từng nơi.
function initConfirmForms() {
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (!window.confirm(form.getAttribute("data-confirm"))) {
                event.preventDefault();
            }
        });
    });
}

// Lọc sản phẩm trên trang chủ theo giới tính (Nữ/Nam) và dáng kính
// (Oval, Vuông, Tròn...) hoàn toàn phía client, không cần tải lại trang.
function initProductFilters() {
    var genderTabs = document.querySelectorAll("[data-gender-filter]");
    var shapeCards = document.querySelectorAll("[data-shape-filter]");
    var priceSelect = document.querySelector("[data-price-filter]");
    var productCards = document.querySelectorAll(".product-card[data-gender]");
    var emptyState = document.querySelector("[data-filter-empty]");
    var activeChip = document.querySelector("[data-active-shape-chip]");
    var activeChipName = document.querySelector("[data-active-shape-name]");
    var clearShapeBtn = document.querySelector("[data-clear-shape]");
    var productsSection = document.getElementById("featured-products");

    if (!productCards.length) {
        return;
    }

    var state = { gender: "all", shape: "all", price: "all" };

    // Kiểm tra giá sản phẩm có nằm trong khoảng đã chọn hay không - value có
    // dạng "min-max" (ví dụ "1000000-2000000") hoặc "min-" (không giới hạn
    // trên, ví dụ "3000000-" nghĩa là "trên 3 triệu").
    function priceMatches(price, rangeValue) {
        if (rangeValue === "all") {
            return true;
        }
        var parts = rangeValue.split("-");
        var min = parseInt(parts[0], 10) || 0;
        var max = parts[1] ? parseInt(parts[1], 10) : Infinity;
        return price >= min && price < max;
    }

    function apply() {
        var visibleCount = 0;
        productCards.forEach(function (card) {
            var g = card.getAttribute("data-gender");
            var s = card.getAttribute("data-shape");
            var p = parseInt(card.getAttribute("data-price"), 10) || 0;
            var genderMatch = state.gender === "all" || g === state.gender || g === "unisex";
            var shapeMatch = state.shape === "all" || s === state.shape;
            var show = genderMatch && shapeMatch && priceMatches(p, state.price);
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

    if (priceSelect) {
        priceSelect.addEventListener("change", function () {
            state.price = priceSelect.value;
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

// Mở/đóng modal chọn hình thức thanh toán ở trang giỏ hàng (bấm nền đen hoặc
// nút X để đóng, giống hệt cách tryon-modal đã làm ở trang chi tiết sản phẩm).
function initPaymentModal() {
    var openBtn = document.querySelector("[data-payment-open]");
    var modal = document.getElementById("payment-modal");

    if (!openBtn || !modal) {
        return;
    }

    openBtn.addEventListener("click", function () {
        modal.hidden = false;
    });

    modal.querySelectorAll("[data-payment-close]").forEach(function (el) {
        el.addEventListener("click", function () {
            modal.hidden = true;
        });
    });
}

// Cập nhật số lượng / xóa sản phẩm ở trang giỏ hàng bằng AJAX (fetch), không
// tải lại cả trang. Header "X-Requested-With" báo cho cart/views.py biết
// đây là request AJAX để trả JSON thay vì redirect kèm flash message.
// Nếu giỏ hàng hết sạch sản phẩm (xóa dòng cuối cùng), tải lại trang cho
// đơn giản - lúc đó server sẽ tự render đúng phần "Giỏ hàng đang trống".
function initAjaxCart() {
    var cartItems = document.querySelector(".cart-items");
    if (!cartItems) {
        return;
    }

    function updateSharedTotals(data) {
        document.querySelectorAll("[data-cart-subtotal]").forEach(function (el) {
            el.textContent = data.cart_total_price + "₫";
        });
        document.querySelectorAll("[data-cart-total-count]").forEach(function (el) {
            el.textContent = data.cart_total_items;
        });
        document.querySelectorAll("[data-cart-badge]").forEach(function (el) {
            el.textContent = data.cart_total_items;
        });
    }

    function submitCartForm(form, isRemove) {
        fetch(form.action, {
            method: "POST",
            body: new FormData(form),
            headers: { "X-Requested-With": "XMLHttpRequest" },
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("cart request failed");
                }
                return response.json();
            })
            .then(function (data) {
                if (!data.ok || data.cart_total_items === 0) {
                    window.location.reload();
                    return;
                }

                var row = form.closest("[data-cart-item-row]");
                if (isRemove) {
                    if (row) {
                        row.remove();
                    }
                } else if (row) {
                    var totalEl = row.querySelector("[data-item-total]");
                    if (totalEl) {
                        totalEl.textContent = data.item_line_total + "₫";
                    }
                    var qtyInput = row.querySelector("[data-qty-input]");
                    if (qtyInput) {
                        qtyInput.value = data.item_quantity;
                    }
                }

                updateSharedTotals(data);
            })
            .catch(function () {
                // Có lỗi mạng/không đọc được JSON - an toàn nhất là tải lại
                // trang để đồng bộ lại đúng trạng thái thật từ server.
                window.location.reload();
            });
    }

    cartItems.querySelectorAll(".cart-item-qty").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            submitCartForm(form, false);
        });
    });

    cartItems.querySelectorAll(".cart-item-remove").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            submitCartForm(form, true);
        });
    });
}
