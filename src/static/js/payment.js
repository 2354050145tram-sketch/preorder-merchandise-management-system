const MOMO_CONFIG = {
    phone: "0966053514",
    name: "NGUYEN THI NGOC TRAM"
};

const urlParams = new URLSearchParams(window.location.search);
const pageType = urlParams.get("type"); // "deposit" hoặc null (đơn hàng)
const depositTransId = urlParams.get("trans_id");

function getOrderIdFromUrl() {
    if (urlParams.get("order_id")) return urlParams.get("order_id");
    if (urlParams.get("id")) return urlParams.get("id");

    const segments = window.location.pathname.split('/').filter(Boolean);
    for (let i = segments.length - 1; i >= 0; i--) {
        if (!isNaN(segments[i]) && Number(segments[i]) > 0) return segments[i];
    }
    return sessionStorage.getItem("current_order_id") || "";
}

function getUserToken() {
    return localStorage.getItem("token")
        || localStorage.getItem("access_token")
        || localStorage.getItem("jwt_token")
        || sessionStorage.getItem("token")
        || sessionStorage.getItem("access_token");
}

function formatCurrency(val) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);
}

const orderId = getOrderIdFromUrl();
let currentPaymentMethod = "MOMO";
let currentSummary = null;
let depositData = null;
let isPaidSuccess = false;

document.addEventListener("DOMContentLoaded", initPaymentPage);

async function initPaymentPage() {
    const token = getUserToken();

    // 1. TRƯỜNG HỢP NẠP TIỀN VÍ VERD (CHỈ HIỆN MOMO)
    if (pageType === "deposit" && depositTransId) {
        try {
            const res = await fetch(`/api/wallets/deposit/${depositTransId}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const result = await res.json();

            if (!res.ok) throw new Error(result.message || "Không tìm thấy yêu cầu nạp tiền");

            depositData = result.data?.transaction || result.transaction;
            const amount = Number(depositData.amount || 0);
            const memo = depositData.transaction_code || `NAP ${depositTransId}`;

            // Ẩn tab Ví Verd, đổi tiêu đề
            document.querySelector(".payment-card-header h2").innerHTML = "<i class='bx bx-wallet'></i> Nạp tiền vào Ví Verd";
            const tabVerd = document.getElementById("tab-btn-verd");
            if (tabVerd) tabVerd.style.display = "none";

            // Điền thông tin MoMo
            document.getElementById("momo-order-id").textContent = `#${depositData.wallet_transaction_id}`;
            document.getElementById("momo-pay-amount").textContent = formatCurrency(amount);
            document.getElementById("momo-pay-memo").textContent = memo;

            const qrUrl = `https://api.vietqr.io/image/970415-${MOMO_CONFIG.phone}-compact2.jpg?amount=${Math.round(amount)}&addInfo=${encodeURIComponent(memo)}&accountName=${encodeURIComponent(MOMO_CONFIG.name)}`;
            const qrImg = document.getElementById("momo-qr-img");
            if (qrImg) qrImg.src = qrUrl;

            document.getElementById("btn-cancel-pay").textContent = "Hủy yêu cầu nạp";
            switchPayMethod("MOMO");
        } catch (e) {
            alert(e.message || "Lỗi tải yêu cầu nạp tiền");
            window.location.href = "/profile";
        }
        return;
    }

    // 2. TRƯỜNG HỢP THANH TOÁN ĐƠN HÀNG
    if (!orderId) {
        alert("Không tìm thấy mã đơn hàng hợp lệ!");
        return;
    }

    try {
        const res = await fetch(`/api/orders/${orderId}/payment-summary`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const result = await res.json();

        if (res.ok && result.data) {
            currentSummary = result.data;
            const totalAmount = currentSummary.remaining_amount > 0 ? currentSummary.remaining_amount : currentSummary.total_amount;
            const walletBalance = Number(currentSummary.wallet_balance || 0);
            const memo = `DONHANG ${orderId}`;

            // MoMo
            document.getElementById("momo-order-id").textContent = `#${orderId}`;
            document.getElementById("momo-pay-amount").textContent = formatCurrency(totalAmount);
            document.getElementById("momo-pay-memo").textContent = memo;

            const qrUrl = `https://api.vietqr.io/image/970415-${MOMO_CONFIG.phone}-compact2.jpg?amount=${Math.round(totalAmount)}&addInfo=${encodeURIComponent(memo)}&accountName=${encodeURIComponent(MOMO_CONFIG.name)}`;
            const qrImg = document.getElementById("momo-qr-img");
            if (qrImg) qrImg.src = qrUrl;

            // Ví Verd
            document.getElementById("verd-order-id").textContent = `#${orderId}`;
            document.getElementById("verd-pay-amount").textContent = formatCurrency(totalAmount);
            document.getElementById("verd-wallet-balance").textContent = formatCurrency(walletBalance);

            const isEnough = walletBalance >= totalAmount;
            const statusTextEl = document.getElementById("verd-status-text");
            if (isEnough) {
                statusTextEl.textContent = "Đủ điều kiện thanh toán";
                statusTextEl.style.color = "#16a34a";
            } else {
                statusTextEl.textContent = `Thiếu ${formatCurrency(totalAmount - walletBalance)}`;
                statusTextEl.style.color = "#dc2626";
            }

            switchPayMethod(currentPaymentMethod);
        }
    } catch (e) {
        console.error("Lỗi:", e);
    }
}

function switchPayMethod(method) {
    currentPaymentMethod = method;
    const isMomo = method === "MOMO";

    const tabMomo = document.getElementById("tab-btn-momo");
    const tabVerd = document.getElementById("tab-btn-verd");
    if (tabMomo) tabMomo.classList.toggle("active", isMomo);
    if (tabVerd) tabVerd.classList.toggle("active", !isMomo);

    const secMomo = document.getElementById("section-momo");
    const secVerd = document.getElementById("section-verd");
    if (secMomo) secMomo.style.display = isMomo ? "block" : "none";
    if (secVerd) secVerd.style.display = isMomo ? "none" : "block";

    const submitBtn = document.getElementById("btn-confirm-payment");
    if (submitBtn) {
        submitBtn.textContent = isMomo ? "Tôi đã chuyển khoản xong" : "Thanh toán bằng Ví Verd";
    }
}

async function handlePaymentSubmit() {
    // 1. Khi nạp tiền ví
    if (pageType === "deposit" && depositTransId) {
        isPaidSuccess = true;
        document.getElementById("payment-view").style.display = "none";
        document.getElementById("success-view").style.display = "block";
        document.querySelector("#success-view h1").textContent = "Đã gửi yêu cầu nạp tiền!";
        document.querySelector("#success-view p").innerHTML = `Hệ thống đã ghi nhận yêu cầu nạp <strong>#${depositTransId}</strong>. Vui lòng chờ Quản trị viên duyệt để số dư được cộng vào ví.`;
        return;
    }

    // 2. Khi thanh toán đơn hàng
    if (!currentSummary) return;
    const totalAmount = currentSummary.remaining_amount > 0 ? currentSummary.remaining_amount : currentSummary.total_amount;
    const walletBalance = Number(currentSummary.wallet_balance || 0);

    if (currentPaymentMethod === "MOMO") {
        await executePaymentAPI("MOMO");
    } else if (currentPaymentMethod === "VI_VERD") {
        if (walletBalance < totalAmount) {
            document.getElementById("wallet-modal-desc").innerHTML = `
                Số dư ví hiện tại: <strong>${formatCurrency(walletBalance)}</strong>.<br>
                Bạn còn thiếu <strong style="color: #dc2626;">${formatCurrency(totalAmount - walletBalance)}</strong> để thanh toán.
            `;
            document.getElementById("wallet-insufficient-modal").style.display = "flex";
            return;
        }
        await executePaymentAPI("VI_VERD");
    }
}

async function executePaymentAPI(method) {
    const token = getUserToken();
    const paymentType = currentSummary.remaining_amount > 0 && currentSummary.total_paid > 0 ? "THANH TOÁN CÒN LẠI" : "THANH TOÁN FULL";

    try {
        const res = await fetch(`/api/orders/${orderId}/payments`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                payment_method: method,
                payment_type: paymentType,
                transaction_id: `${method}_${orderId}_${Date.now()}`
            })
        });

        const result = await res.json();
        if (!res.ok) {
            alert(result.message || "Lỗi xử lý thanh toán.");
            return;
        }

        isPaidSuccess = true;
        document.getElementById("payment-view").style.display = "none";
        document.getElementById("success-view").style.display = "block";
        document.getElementById("success-order-id").textContent = `#${orderId}`;
    } catch (e) {
        alert("Lỗi kết nối máy chủ khi gửi thanh toán.");
    }
}

// Khách bấm Hủy / Quay lại
document.getElementById("btn-cancel-pay")?.addEventListener("click", async (e) => {
    e.preventDefault();
    if (pageType === "deposit" && depositTransId) {
        if (confirm("Bạn có chắc muốn hủy yêu cầu nạp tiền này?")) {
            const token = getUserToken();
            try {
                await fetch(`/api/wallets/deposit/${depositTransId}/cancel`, {
                    method: "PUT",
                    headers: { "Authorization": `Bearer ${token}` }
                });
            } catch (err) {
                console.error(err);
            }
            window.location.href = "/profile";
        }
        return;
    }
    window.location.href = "/products";
});

function closeWalletModal() {
    document.getElementById("wallet-insufficient-modal").style.display = "none";
    switchPayMethod("MOMO");
}

function goToProfileWallet() {
    window.location.href = "/profile";
}

window.switchPayMethod = switchPayMethod;
window.handlePaymentSubmit = handlePaymentSubmit;
window.closeWalletModal = closeWalletModal;
window.goToProfileWallet = goToProfileWallet;