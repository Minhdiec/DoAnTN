// Module "Thử kính ảo" (CLAUDE_PROGRESS.md mục 24/25, Bước C).
//
// Chỉ chạy khi trang có nút [data-tryon-open] (tức sản phẩm đang xem CÓ ảnh
// AR - xem products/views.py). Toàn bộ xử lý ảnh (chuẩn hoá ánh sáng, nhận
// diện khuôn mặt, dán kính) nằm ở SERVER (Python/OpenCV/MediaPipe qua
// tryon/consumers.py) - file này CHỈ lo: xin quyền camera, chụp khung hình
// gửi lên server qua WebSocket, và hiển thị khung hình đã xử lý nhận về.
// Xem docstring đầu tryon/consumers.py để biết đầy đủ giao thức 2 bên.
document.addEventListener("DOMContentLoaded", function () {
    initTryOn();
});

function initTryOn() {
    var openBtn = document.querySelector("[data-tryon-open]");
    var modal = document.getElementById("tryon-modal");
    if (!openBtn || !modal) {
        return; // san pham nay chua co anh AR - khong co gi de khoi tao
    }

    var closeButtons = modal.querySelectorAll("[data-tryon-close]");
    var placeholder = document.getElementById("tryon-placeholder");
    var placeholderText = document.getElementById("tryon-placeholder-text");
    var retryBtn = document.getElementById("tryon-retry");
    var video = document.getElementById("tryon-video");
    var captureCanvas = document.getElementById("tryon-canvas-capture");
    var outputImg = document.getElementById("tryon-output");
    var statusEl = document.getElementById("tryon-status");
    var galleryItems = modal.querySelectorAll("[data-glasses-id]");
    var defaultGlassesId = openBtn.getAttribute("data-glasses-id");

    // Gui toi da ~25 khung hinh/giay - QUAN TRONG HON la: KHONG BAO GIO gui
    // khung moi khi khung truoc chua co phan hoi (co "waitingForResponse"
    // ben duoi) - dung yeu cau muc 24 "tranh don u", nen so nay CHI la TRAN
    // TREN, toc do that su van do vong lap gui/nhan (waitingForResponse) tu
    // dieu tiet theo dung nang luc server + mang.
    //
    // Gia tri nay TUNG la 80ms (~12,5 fps) - da GIAM XUONG 40ms sau Giai
    // doan 3 (CLAUDE_PROGRESS.md muc 38-40): luc do server xu ly 1 khung
    // ~30ms (chua toi uu), 80ms la hop ly; SAU KHI toi uu server chi con
    // ~18-35ms/khung (do that qua WebSocket that, xem muc 41), 80ms gio la
    // ĐIEM NGHEN CHINH - nguoi dung van thay tre du server da nhanh hon
    // nhieu, vi client tu gioi han khong gui qua 12,5 lan/giay du server co
    // the tra loi nhanh hon. 40ms (~25fps) tan dung dung toc do server that
    // ma van con du bien an toan (server can ~20-35ms, thap hon 40ms).
    var CAPTURE_INTERVAL_MS = 40;
    var JPEG_QUALITY = 0.8;

    var stream = null;
    var socket = null;
    var captureTimer = null;
    var waitingForResponse = false;
    var firstFrameShown = false;
    var currentOutputUrl = null;

    // Bam TRY ON la da tinh la 1 "user gesture" (thao tac chuot that cua
    // nguoi dung) - du de trinh duyet cho phep goi getUserMedia() truc tiep
    // va tu hien hop thoai xin quyen camera, KHONG can them 1 nut "Bat
    // camera" trung gian nua (yeu cau muc 28, Loi 4).
    openBtn.addEventListener("click", function () {
        modal.hidden = false;
        startCamera();
    });

    closeButtons.forEach(function (el) {
        el.addEventListener("click", stopTryOn);
    });

    retryBtn.addEventListener("click", startCamera);

    galleryItems.forEach(function (item) {
        item.addEventListener("click", function () {
            galleryItems.forEach(function (i) {
                i.classList.toggle("is-active", i === item);
            });
            sendSelectGlasses(item.getAttribute("data-glasses-id"));
        });
    });

    function startCamera() {
        // BAT BUOC don sach phien cu (neu co) truoc khi mo phien moi - phat
        // hien qua debug-mode: vi placeholder/nut "Thu lai" bi ket dinh hien
        // thi (loi CSS da sua o tren) nen nguoi dung hoan toan co ly do bam
        // lai du camera dang chay tot, moi lan bam lai ma khong don se de
        // thanh 2 MediaStream + 2 WebSocket + 2 FaceMeshDetector chay song
        // song, cung ghi de len 1 the <img> -> gay "dơ"/giat hinh va lam
        // nhu doi kinh khong co tac dung. Goi ham nay dam bao startCamera()
        // luon an toan khi goi lai nhieu lan, du la tu TRY ON hay "Thu lai".
        teardownSession();

        // Man hinh cho mac dinh (khong phai man hinh loi) trong luc trinh
        // duyet dang hien hop thoai xin quyen - se bi an ngay khi co khung
        // hinh dau tien, hoac doi thanh thong bao loi + nut "Thu lai" neu
        // getUserMedia that bai.
        placeholder.hidden = false;
        placeholderText.textContent = "Đang mở camera…";
        retryBtn.hidden = true;
        statusEl.hidden = true;

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showCameraError("Trình duyệt này không hỗ trợ truy cập camera. Hãy thử Chrome/Edge/Firefox bản mới.");
            return;
        }
        navigator.mediaDevices
            .getUserMedia({ video: { width: 640, height: 480 }, audio: false })
            .then(function (mediaStream) {
                stream = mediaStream;
                video.srcObject = stream;
                video.hidden = false;
                placeholder.hidden = true;
                statusEl.hidden = true;
                connectSocket();
            })
            .catch(function (err) {
                var reason = err && err.message ? err.message : "quyền truy cập camera bị từ chối";
                showCameraError("Không thể mở camera (" + reason + "). Vui lòng cho phép quyền camera trong trình duyệt rồi thử lại.");
            });
    }

    function showCameraError(message) {
        placeholderText.textContent = message;
        retryBtn.hidden = false;
        placeholder.hidden = false;
    }

    function connectSocket() {
        var wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        socket = new WebSocket(wsProtocol + window.location.host + "/ws/tryon/");
        socket.binaryType = "arraybuffer";

        socket.addEventListener("open", function () {
            sendSelectGlasses(defaultGlassesId);
            captureTimer = window.setInterval(captureAndSend, CAPTURE_INTERVAL_MS);
        });

        socket.addEventListener("message", function (event) {
            if (typeof event.data === "string") {
                handleControlMessage(event.data);
                return;
            }
            waitingForResponse = false;
            renderFrame(event.data);
        });

        socket.addEventListener("error", function (ev) {
            showStatus("Mất kết nối tới server xử lý ảnh. Vui lòng đóng và mở lại.");
        });

        socket.addEventListener("close", function (ev) {
            waitingForResponse = false;
        });
    }

    function handleControlMessage(rawText) {
        var payload;
        try {
            payload = JSON.parse(rawText);
        } catch (err) {
            return;
        }
        if (payload.type === "error") {
            showStatus(payload.message);
        }
    }

    function captureAndSend() {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            return;
        }
        if (waitingForResponse) {
            return; // khung truoc chua xu ly xong - bo qua lan nay, khong don u hang doi
        }
        if (video.readyState < video.HAVE_CURRENT_DATA) {
            return; // webcam chua co du lieu khung hinh dau tien
        }

        captureCanvas.width = video.videoWidth;
        captureCanvas.height = video.videoHeight;
        var ctx = captureCanvas.getContext("2d");
        ctx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

        captureCanvas.toBlob(
            function (blob) {
                if (!blob || !socket || socket.readyState !== WebSocket.OPEN) {
                    return;
                }
                waitingForResponse = true;
                socket.send(blob);
            },
            "image/jpeg",
            JPEG_QUALITY
        );
    }

    function renderFrame(arrayBuffer) {
        var bytes = new Uint8Array(arrayBuffer);
        if (bytes.length < 1) {
            return;
        }
        var faceDetected = bytes[0] === 1;
        var jpegBytes = bytes.subarray(1);
        var blob = new Blob([jpegBytes], { type: "image/jpeg" });
        var url = URL.createObjectURL(blob);
        var oldUrl = currentOutputUrl;
        currentOutputUrl = url;
        outputImg.src = url;
        if (oldUrl) {
            URL.revokeObjectURL(oldUrl);
        }

        if (!firstFrameShown) {
            firstFrameShown = true;
            video.hidden = true;
            outputImg.hidden = false;
        }

        if (faceDetected) {
            statusEl.hidden = true;
        } else {
            showStatus("Không phát hiện khuôn mặt - vui lòng nhìn thẳng vào camera, đủ ánh sáng.");
        }
    }

    function showStatus(message) {
        statusEl.textContent = message;
        statusEl.hidden = false;
    }

    function sendSelectGlasses(glassesId) {
        if (!glassesId || !socket || socket.readyState !== WebSocket.OPEN) {
            return;
        }
        socket.send(JSON.stringify({ action: "select_glasses", glasses_id: parseInt(glassesId, 10) }));
    }

    // Don sach MOI tai nguyen cua 1 phien thu kinh (interval chup khung,
    // WebSocket, MediaStream camera) - dung CHUNG boi ca stopTryOn() (dong
    // hang hoan toan) LAN startCamera() (dam bao khong bao gio co 2 phien
    // chay song song, xem ghi chu trong startCamera()). KHONG dong modal/
    // doi trang thai placeholder o day - 2 noi goi ham nay can 2 hanh vi UI
    // khac nhau sau khi don xong (stopTryOn dong modal, startCamera mo phien
    // moi ngay sau do).
    function teardownSession() {
        if (captureTimer) {
            window.clearInterval(captureTimer);
            captureTimer = null;
        }
        if (socket) {
            socket.close();
            socket = null;
        }
        // Tat den camera vat ly - BAT BUOC phai goi getTracks().forEach(stop()),
        // chi dong WebSocket khong lam tat duoc camera (yeu cau muc 24).
        if (stream) {
            stream.getTracks().forEach(function (track) {
                track.stop();
            });
            stream = null;
        }
        waitingForResponse = false;
        firstFrameShown = false;
    }

    function stopTryOn() {
        modal.hidden = true;
        teardownSession();

        video.hidden = true;
        video.srcObject = null;
        outputImg.hidden = true;
        outputImg.removeAttribute("src");
        if (currentOutputUrl) {
            URL.revokeObjectURL(currentOutputUrl);
            currentOutputUrl = null;
        }
        placeholder.hidden = false;
        placeholderText.textContent = "Đang mở camera…";
        retryBtn.hidden = true;
        statusEl.hidden = true;
    }
}
