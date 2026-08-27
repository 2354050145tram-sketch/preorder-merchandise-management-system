const MOMO_CONFIG = {
    phone: "0966053514",
    name: "NGUYEN THI NGOC TRAM"
};

const pathSegments = window.location.pathname.split('/');
const orderId = pathSegments[pathSegments.length - 1];

let isPaidSuccess = false;

async function initPaymentPage() {
    const token = localStorage.getItem("token") || localStorage.getItem("access_token");
    try {
        const res = await fetch(`/api/orders/${orderId}/payment-summary`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const result = await res.json();

        if (res.ok) {
            const summary = result.data;
            const totalAmount = summary.remaining_amount > 0 ? summary.remaining_amount : summary.total_amount;
            const memo = `DONHANG ${orderId}`;

            document.getElementById("pay-order-id").textContent = `#${orderId}`;
            document.getElementById("pay-phone").textContent = MOMO_CONFIG.phone;
            document.getElementById("pay-name").textContent = MOMO_CONFIG.name;
            document.getElementById("pay-amount").textContent = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(totalAmount);
            document.getElementById("pay-memo").textContent = memo;

            const qrUrl = `https://api.vietqr.io/image/970415-${MOMO_CONFIG.phone}-compact2.jpg?amount=${Math.round(totalAmount)}&addInfo=${encodeURIComponent(memo)}&accountName=${encodeURIComponent(MOMO_CONFIG.name)}`;
            document.getElementById("momo-qr-img").src = qrUrl;
        } else {
            alert(result.message || "Không thể tải thông tin đơn hàng.");
        }
    } catch (e) {
        console.error("Lỗi:", e);
        document.getElementById("pay-order-id").textContent = `#${orderId}`;
        document.getElementById("pay-phone").textContent = MOMO_CONFIG.phone;
        document.getElementById("pay-name").textContent = MOMO_CONFIG.name;
        document.getElementById("pay-memo").textContent = `DONHANG ${orderId}`;
        document.getElementById("momo-qr-img").src = `https://api.vietqr.io/image/970415-${MOMO_CONFIG.phone}-compact2.jpg?addInfo=${encodeURIComponent("DONHANG " + orderId)}`;
    }
}

function copyTextContent(elementId) {
    const text = document.getElementById(elementId).textContent;
    navigator.clipboard.writeText(text);
    alert("Đã sao chép: " + text);
}

// Bấm hoàn tất -> Ẩn khung QR, hiện khung thành công ngay tại chỗ
function finishPayment() {
    isPaidSuccess = true;

    // Ẩn khung thanh toán, hiện khung thành công
    document.getElementById("payment-view").style.display = "none";
    document.getElementById("success-view").style.display = "block";
    document.getElementById("success-order-id").textContent = `#${orderId}`;

    // Tải sản phẩm đề xuất hiển thị ở dưới
    loadRecommendedProducts();
}

async function loadRecommendedProducts() {
    try {
        const response = await fetch("/api/products");
        const result = await response.json();
        if (!response.ok) return;

        const products = result.data?.products || [];
        const recommendations = products.slice(0, 4);
        const grid = document.getElementById("recommended-grid");
        if (!grid) return;

        grid.innerHTML = "";
        recommendations.forEach(product => {
            const card = document.createElement("div");
            card.className = "rec-card-item";
            card.innerHTML = `
                <img src="${product.image}" alt="${product.product_name}">
                <div class="rec-card-info">
                    <div class="rec-card-name">${product.product_name}</div>
                    <div class="rec-card-price">${Number(product.price).toLocaleString("vi-VN")}đ</div>
                </div>
            `;
            card.addEventListener("click", () => {
                window.location.href = `/products/${product.product_id}`;
            });
            grid.appendChild(card);
        });
    } catch (err) {
        console.error("Lỗi tải đề xuất:", err);
    }
}

async function cancelOrderOnLeave() {
    if (isPaidSuccess) return;
    const token = localStorage.getItem("token") || localStorage.getItem("access_token");
    if (!token) return;

    try {
        await fetch(`/api/orders/admin/${orderId}/status`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ order_status: "ĐÃ HỦY" }),
            keepalive: true
        });
    } catch (err) {
        console.error("Không thể hủy đơn:", err);
    }
}

window.addEventListener("beforeunload", () => {
    if (!isPaidSuccess) cancelOrderOnLeave();
});

document.getElementById("btn-cancel-pay")?.addEventListener("click", (e) => {
    e.preventDefault();
    if (confirm("Bạn có muốn hủy đơn hàng này và quay lại mua sắm không?")) {
        cancelOrderOnLeave().then(() => {
            window.location.href = "/products";
        });
    }
});

document.addEventListener("DOMContentLoaded", initPaymentPage);

let paymentCheckInterval = null;

async function startAutoCheckPayment(orderId) {
    const token = localStorage.getItem("token") || localStorage.getItem("access_token");
    paymentCheckInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/orders/${orderId}/check-payment-status`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const result = await res.json();

            if (res.ok && result.data?.is_paid) {
                clearInterval(paymentCheckInterval);
                closeMoMoModal();
                window.location.href = `/orders/success?order_id=${orderId}`;
            }
        } catch (e) {
            console.error("Polling error:", e);
        }
    }, 3000)
}

function closeMoMoModal() {
    if (paymentCheckInterval) clearInterval(paymentCheckInterval);
    document.getElementById("momo-payment-modal").style.display = "none";
}
