const BANK_CONFIG = {
    bankBin: "970423",
    accountNumber: "00000880145",
    accountName: "NGUYEN THI NGOC TRAM"
};

const urlParams = new URLSearchParams(window.location.search);
const pageType = urlParams.get("type");
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
let currentPaymentMethod = "TPBANK";
let currentSummary = null;
let depositData = null;
let isPaidSuccess = false;

document.addEventListener("DOMContentLoaded", initPaymentPage);

async function initPaymentPage() {
    const token = getUserToken();

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

            document.querySelector(".payment-card-header h2").innerHTML = "<i class='bx bx-wallet'></i> Nạp tiền vào Ví Verd";
            const tabVerd = document.getElementById("tab-btn-verd");
            if (tabVerd) tabVerd.style.display = "none";

            document.getElementById("tpbank-order-id").textContent = `#${depositData.wallet_transaction_id}`;
            document.getElementById("tpbank-pay-amount").textContent = formatCurrency(amount);
            document.getElementById("tpbank-pay-memo").textContent = memo;

            const qrUrl = (
                `https://api.vietqr.io/image/`
                + `${BANK_CONFIG.bankBin}-`
                + `${BANK_CONFIG.accountNumber}`
                + `-compact2.jpg`
                + `?amount=${Math.round(amount)}`
                + `&addInfo=${encodeURIComponent(memo)}`
                + `&accountName=${encodeURIComponent(
                    BANK_CONFIG.accountName
                )}`
            );
            const qrImg = document.getElementById("tpbank-qr-img");
            if (qrImg) qrImg.src = qrUrl;

            document.getElementById("btn-cancel-pay").textContent = "Hủy yêu cầu nạp";
            switchPayMethod("TPBANK");
        } catch (e) {
            alert(e.message || "Lỗi tải yêu cầu nạp tiền");
            window.location.href = "/profile";
        }
        return;
    }

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

            document.getElementById("tpbank-order-id").textContent = `#${orderId}`;
            document.getElementById("tpbank-pay-amount").textContent = formatCurrency(totalAmount);
            document.getElementById("tpbank-pay-memo").textContent = memo;

            const qrUrl = (
                `https://api.vietqr.io/image/`
                + `${BANK_CONFIG.bankBin}-`
                + `${BANK_CONFIG.accountNumber}`
                + `-compact2.jpg`
                + `?amount=${Math.round(totalAmount)}`
                + `&addInfo=${encodeURIComponent(memo)}`
                + `&accountName=${encodeURIComponent(
                    BANK_CONFIG.accountName
                )}`
            );
            const qrImg = document.getElementById("tpbank-qr-img");
            if (qrImg) qrImg.src = qrUrl;

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

        } else {
            alert(
                result.message
                || "Không tải được thông tin thanh toán"
            );
        }

    } catch (e) {
        alert(
            e.message
            || "Có lỗi khi tải thông tin thanh toán"
        );
    }
}

function switchPayMethod(method) {
    currentPaymentMethod = method;

    const isTpbank = method === "TPBANK";

    const tabTpbank =
        document.getElementById("tab-btn-tpbank");

    const tabVerd =
        document.getElementById("tab-btn-verd");

    if (tabTpbank) {
        tabTpbank.classList.toggle(
            "active",
            isTpbank
        );
    }

    if (tabVerd) {
        tabVerd.classList.toggle(
            "active",
            !isTpbank
        );
    }

    const sectionTpbank =
        document.getElementById("section-tpbank");

    const sectionVerd =
        document.getElementById("section-verd");

    if (sectionTpbank) {
        sectionTpbank.style.display =
            isTpbank ? "block" : "none";
    }

    if (sectionVerd) {
        sectionVerd.style.display =
            isTpbank ? "none" : "block";
    }

    const submitButton =
        document.getElementById(
            "btn-confirm-payment"
        );

    if (submitButton) {
        submitButton.textContent = isTpbank
            ? "Tôi đã chuyển khoản xong"
            : "Thanh toán bằng Ví Verd";
    }
}

async function handlePaymentSubmit() {
    if (pageType === "deposit" && depositTransId) {
        isPaidSuccess = true;
        document.getElementById("payment-view").style.display = "none";
        document.getElementById("success-view").style.display = "block";
        document.querySelector("#success-view h1").textContent = "Đã gửi yêu cầu nạp tiền!";
        document.querySelector("#success-view p").innerHTML = `Hệ thống đã ghi nhận yêu cầu nạp <strong>#${depositTransId}</strong>. Vui lòng chờ Quản trị viên duyệt để số dư được cộng vào ví.`;
        return;
    }

    if (!currentSummary) return;
    const totalAmount = currentSummary.remaining_amount > 0 ? currentSummary.remaining_amount : currentSummary.total_amount;
    const walletBalance = Number(currentSummary.wallet_balance || 0);

    if (currentPaymentMethod === "TPBANK") {
        await executePaymentAPI("TPBANK");

    } else if (
        currentPaymentMethod === "VÍ VERD"
    ) {
        if (walletBalance < totalAmount) {
            document.getElementById(
                "wallet-modal-desc"
            ).innerHTML = `
            Số dư ví hiện tại:
            <strong>
                ${formatCurrency(walletBalance)}
            </strong>.<br>

            Bạn còn thiếu
            <strong style="color: #dc2626;">
                ${formatCurrency(
                totalAmount - walletBalance
            )}
            </strong>
            để thanh toán.
        `;

            document.getElementById(
                "wallet-insufficient-modal"
            ).style.display = "flex";

            return;
        }

        await executePaymentAPI("VÍ VERD");
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
    document.getElementById(
        "wallet-insufficient-modal"
    ).style.display = "none";

    switchPayMethod("TPBANK");
}

function goToProfileWallet() {
    window.location.href = "/profile";
}

window.switchPayMethod = switchPayMethod;
window.handlePaymentSubmit = handlePaymentSubmit;
window.closeWalletModal = closeWalletModal;
window.goToProfileWallet = goToProfileWallet;