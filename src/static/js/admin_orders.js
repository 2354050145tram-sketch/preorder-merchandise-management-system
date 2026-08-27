let allOrdersData = [];
let currentPage = 1;
const PAGE_SIZE = 10;

let currentViewingOrder = null;
let orderSearchDebounce = null;
let orderFetchController = null;

const orderListView = document.getElementById("order-list-view");
const orderFormView = document.getElementById("order-form-view");
const orderListControlPanel = document.getElementById("order-list-control-panel");
const orderFormControlPanel = document.getElementById("order-form-control-panel");
const orderTable = document.getElementById("admin-order-table");
const orderTableBody = document.getElementById("admin-order-table-body");
const orderLoadingState = document.getElementById("admin-order-loading");
const orderEmptyState = document.getElementById("admin-order-empty");
const orderPagination = document.getElementById("admin-order-pagination");

function getAdminToken() {
    return localStorage.getItem("access_token")
        || localStorage.getItem("token")
        || localStorage.getItem("jwt_token")
        || sessionStorage.getItem("access_token")
        || sessionStorage.getItem("token");
}

function formatOrderPrice(val) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);
}

function escapeOrderHTML(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", () => {
    bindOrderEvents();
    showOrderListView();
    loadAdminOrders(true);
});

function bindOrderEvents() {
    document.getElementById("reload-orders-btn")?.addEventListener("click", () => loadAdminOrders(true));
    document.getElementById("discard-order-btn")?.addEventListener("click", showOrderListView);

    const keywordInput = document.getElementById("admin-order-keyword");
    keywordInput?.addEventListener("input", () => {
        clearTimeout(orderSearchDebounce);
        orderSearchDebounce = setTimeout(() => {
            currentPage = 1;
            renderOrderPaginatedTable();
        }, 300);
    });

    document.getElementById("admin-order-status")?.addEventListener("change", () => {
        currentPage = 1;
        renderOrderPaginatedTable();
    });

    document.getElementById("admin-order-sort")?.addEventListener("change", () => {
        currentPage = 1;
        renderOrderPaginatedTable();
    });

    document.getElementById("btn-submit-shipping")?.addEventListener("click", submitOrderShipping);

    document.querySelectorAll(".product-tab").forEach(button => {
        button.addEventListener("click", () => {
            switchOrderTab(button.dataset.orderTab);
        });
    });
}

function switchOrderTab(tabName) {
    document.querySelectorAll(".product-tab").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.orderTab === tabName);
    });
    document.querySelectorAll(".product-tab-content").forEach(content => {
        const isActive = content.dataset.orderContent === tabName;
        content.classList.toggle("active", isActive);
        content.style.setProperty("display", isActive ? "block" : "none", "important");
    });
}

function showOrderListView() {
    if (orderFormView) orderFormView.style.setProperty("display", "none", "important");
    if (orderListView) orderListView.style.setProperty("display", "block", "important");
    if (orderFormControlPanel) orderFormControlPanel.style.setProperty("display", "none", "important");
    if (orderListControlPanel) orderListControlPanel.style.setProperty("display", "flex", "important");

    const breadcrumb = document.getElementById("order-breadcrumb-current");
    if (breadcrumb) breadcrumb.textContent = "Danh sách";
    currentViewingOrder = null;
}

function showOrderDetailView() {
    if (orderListView) orderListView.style.setProperty("display", "none", "important");
    if (orderFormView) orderFormView.style.setProperty("display", "block", "important");
    if (orderListControlPanel) orderListControlPanel.style.setProperty("display", "none", "important");
    if (orderFormControlPanel) orderFormControlPanel.style.setProperty("display", "flex", "important");
}

async function loadAdminOrders(showSpinner = false) {
    if (orderFetchController) orderFetchController.abort();
    orderFetchController = new AbortController();

    if (showSpinner) {
        if (orderLoadingState) orderLoadingState.style.display = "flex";
        if (orderEmptyState) orderEmptyState.style.display = "none";
        if (orderTable) orderTable.style.display = "none";
        if (orderPagination) orderPagination.style.display = "none";
    }

    const token = getAdminToken();
    try {
        const res = await fetch(`/api/orders/admin`, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            signal: orderFetchController.signal
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Không thể tải danh sách đơn hàng");

        allOrdersData = result.data?.orders || result.orders || [];
        renderOrderPaginatedTable();
    } catch (e) {
        if (e.name === "AbortError") return;
        console.error("Load orders error:", e);
        showOrderToast(e.message || "Lỗi tải đơn hàng");
        allOrdersData = [];
        renderOrderPaginatedTable();
    } finally {
        if (showSpinner && orderLoadingState) orderLoadingState.style.display = "none";
    }
}

function renderOrderPaginatedTable() {
    const keyword = document.getElementById("admin-order-keyword")?.value.trim().toLowerCase() || "";
    const statusFilter = document.getElementById("admin-order-status")?.value || "";
    const sortType = document.getElementById("admin-order-sort")?.value || "newest";

    let filtered = allOrdersData.filter(order => {
        const buyerName = (order.user?.username || order.username || "").toLowerCase();
        const buyerEmail = (order.user?.email || order.email || "").toLowerCase();
        const orderIdStr = String(order.order_id || "");

        const matchKw = !keyword || buyerName.includes(keyword) || buyerEmail.includes(keyword) || orderIdStr.includes(keyword);
        const matchStatus = !statusFilter || order.order_status === statusFilter;

        return matchKw && matchStatus;
    });

    filtered.sort((a, b) => {
        const idA = Number(a.order_id || 0);
        const idB = Number(b.order_id || 0);

        if (sortType === "oldest") return idA - idB;
        if (sortType === "price_desc") return (Number(b.total_amount || 0) - Number(a.total_amount || 0)) || (idB - idA);
        if (sortType === "price_asc") return (Number(a.total_amount || 0) - Number(b.total_amount || 0)) || (idB - idA);
        
        return idB - idA;
    });

    const totalOrders = filtered.length;
    const countEl = document.getElementById("admin-table-order-count");
    if (countEl) countEl.textContent = `(${totalOrders})`;

    if (!totalOrders) {
        if (orderEmptyState) orderEmptyState.style.display = "flex";
        if (orderTable) orderTable.style.display = "none";
        if (orderPagination) orderPagination.style.display = "none";
        return;
    }

    if (orderEmptyState) orderEmptyState.style.display = "none";
    if (orderTable) orderTable.style.display = "table";

    const totalPages = Math.ceil(totalOrders / PAGE_SIZE) || 1;
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    const startIdx = (currentPage - 1) * PAGE_SIZE;
    const endIdx = Math.min(startIdx + PAGE_SIZE, totalOrders);
    const pageOrders = filtered.slice(startIdx, endIdx);

    orderTableBody.innerHTML = pageOrders.map((order, index) => {
        let statusClass = "dang-xu-ly";
        if (order.order_status === "CHỜ XÁC NHẬN") statusClass = "cho-xac-nhan";
        else if (order.order_status === "HOÀN THÀNH" || order.order_status === "ĐÃ XÁC NHẬN") statusClass = "hoan-thanh";
        else if (order.order_status === "ĐÃ HỦY") statusClass = "da-huy";

        const buyerName = order.user?.username || order.username || `User #${order.user_id}`;
        const buyerEmail = order.user?.email || order.email || "";
        const dateFormatted = order.order_date || (order.created_at ? String(order.created_at).split('T')[0] : '—');

        return `
        <tr onclick="openOrderDetail(${order.order_id})" style="cursor: pointer;">
            <td><strong style="color: #111827; font-size: 14px;">#${order.order_id}</strong></td>
            <td>
                <strong style="color: #111827; font-size: 14px;">${escapeOrderHTML(buyerName)}</strong>
                ${buyerEmail ? `<div style="font-size: 12px; color: var(--admin-muted, #6b7280); margin-top: 2px;">${escapeOrderHTML(buyerEmail)}</div>` : ''}
            </td>
            <td style="color: #374151; font-size: 13px;">${dateFormatted}</td>
            <td style="font-weight: 700; color: #d97706; font-size: 14px;">${formatOrderPrice(order.total_amount)}</td>
            <td style="color: #374151; font-size: 13px;">${formatOrderPrice(order.shipping_fee)}</td>
            <td style="text-align: center;">
                <span class="admin-product-status ${statusClass}">${escapeOrderHTML(order.order_status)}</span>
            </td>
        </tr>
    `;
    }).join("");

    renderPaginationControls(totalPages);
}

function renderPaginationControls(totalPages) {
    if (!orderPagination) return;

    if (totalPages <= 1) {
        orderPagination.style.display = "none";
        return;
    }

    orderPagination.style.display = "flex";
    const btnContainer = document.getElementById("admin-pagination-buttons");
    let btnsHtml = `
        <button class="admin-page-btn" onclick="goToOrderPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
            <i class='bx bx-chevron-left'></i>
        </button>
    `;

    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);

    for (let p = startPage; p <= endPage; p++) {
        btnsHtml += `
            <button class="admin-page-btn ${p === currentPage ? 'active' : ''}" onclick="goToOrderPage(${p})">
                ${p}
            </button>
        `;
    }

    btnsHtml += `
        <button class="admin-page-btn" onclick="goToOrderPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
            <i class='bx bx-chevron-right'></i>
        </button>
    `;

    btnContainer.innerHTML = btnsHtml;
}

function goToOrderPage(page) {
    currentPage = page;
    renderOrderPaginatedTable();
    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function openOrderDetail(orderId) {
    const token = getAdminToken();
    try {
        const res = await fetch(`/api/orders/admin/${orderId}`, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            }
        });

        if (!res.ok) throw new Error("Không thể lấy dữ liệu chi tiết đơn hàng");

        const result = await res.json();
        const order = result.data?.order || result.order;
        if (!order) throw new Error("Không tìm thấy đơn hàng");

        currentViewingOrder = order;

        document.getElementById("order-breadcrumb-current").textContent = `Đơn hàng #${order.order_id}`;
        document.getElementById("order-form-mode").textContent = `Đơn hàng #${order.order_id}`;

        document.getElementById("order-detail-id-display").textContent = `Đơn hàng #${order.order_id}`;

        const u = order.user || {};
        document.getElementById("order-buyer-name-display").textContent = u.username || order.username || `User #${order.user_id}`;
        const rawDate = order.order_date || order.created_at || "";
        document.getElementById("order-date-display").textContent = rawDate ? String(rawDate).split('T')[0] : "—";

        const items = order.order_items || order.items || [];
        const firstShipItem = items.find(i => i.tracking_code);
        if (firstShipItem) {
            document.getElementById("ship-tracking-code").value = firstShipItem.tracking_code || "";
            document.getElementById("ship-method").value = firstShipItem.shipping_method || "TIÊU CHUẨN";
            document.getElementById("ship-fee").value = Number(order.shipping_fee || 0);
        } else {
            document.getElementById("ship-tracking-code").value = "";
            document.getElementById("ship-fee").value = Number(order.shipping_fee || 0);
        }

        renderHeaderStatusActions(order);
        renderOrderItems(items);
        renderPaymentSummaryDirect(order);
        renderShippingList(items);

        switchOrderTab("items");
        showOrderDetailView();
    } catch (e) {
        showOrderToast(e.message || "Lỗi tải chi tiết đơn hàng");
    }
}

function renderHeaderStatusActions(order) {
    const container = document.getElementById("order-header-actions");
    if (!container) return;

    container.innerHTML = "";

    if (order.order_status === "CHỜ XÁC NHẬN") {
        container.innerHTML = `
            <button type="button"
                class="admin-btn admin-btn-primary"
                onclick="changeOrderStatus(${order.order_id}, 'ĐÃ XÁC NHẬN')">
                <i class='bx bx-check'></i>
                Xác nhận đơn hàng
            </button>
        `;
    }

    else if (order.order_status === "ĐÃ ĐẶT CỌC") {
        container.innerHTML = `
            <button type="button"
                class="admin-btn admin-btn-primary"
                onclick="changeOrderStatus(${order.order_id}, 'ĐÃ XÁC NHẬN')">
                <i class='bx bx-check'></i>
                Xác nhận đơn hàng
            </button>
        `;
    }

    else if (order.order_status === "ĐÃ XÁC NHẬN") {
        container.innerHTML = `
            <button type="button"
                class="admin-btn admin-btn-primary"
                onclick="changeOrderStatus(${order.order_id}, 'ĐANG XỬ LÝ')">
                <i class='bx bx-loader-circle'></i>
                Bắt đầu xử lý
            </button>
        `;
    }

    else if (order.order_status === "ĐANG XỬ LÝ") {
        container.innerHTML = `
            <button type="button"
                class="admin-btn admin-btn-primary"
                onclick="changeOrderStatus(${order.order_id}, 'HOÀN THÀNH')">
                <i class='bx bx-check-double'></i>
                Hoàn thành đơn hàng
            </button>
        `;
    }
}

function renderOrderItems(items) {
    const tbody = document.getElementById("order-items-table-body");
    if (!tbody) return;

    if (!items.length) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--admin-muted, #6b7280); padding: 15px;">Đơn hàng không có món nào.</td></tr>`;
        return;
    }

    tbody.innerHTML = items.map(item => {
        const isPreorder = Boolean(item.preorder_id);
        const subtotal = Number(item.price) * Number(item.quantity);

        return `
            <tr>
                <td>
                    <strong style="color: #111827;">${escapeOrderHTML(item.product?.product_name || `Sản phẩm #${item.product_id}`)}</strong>
                    <div style="font-size: 11px; color: var(--admin-muted, #6b7280);">ID: #${item.product_id}</div>
                </td>
                <td><span class="admin-product-status ${isPreorder ? 'cho-xac-nhan' : 'hoan-thanh'}">${isPreorder ? 'PRE-ORDER' : 'CÓ SẴN'}</span></td>
                <td>${formatOrderPrice(item.price)}</td>
                <td>${item.quantity}</td>
                <td style="font-weight: 700; color: #d97706;">${formatOrderPrice(subtotal)}</td>
                <td>
                    <span class="admin-product-status ${item.item_status === 'ĐÃ HỦY' ? 'da-huy' : 'hoan-thanh'}">${escapeOrderHTML(item.item_status)}</span>
                </td>
                <td style="text-align: center;">
                    ${item.item_status !== 'ĐÃ HỦY' ? `
                        <button type="button" class="admin-product-action delete" title="Hủy sản phẩm này" onclick="cancelItem(${item.order_item_id})">
                            <i class='bx bx-trash'></i>
                        </button>
                    ` : '—'}
                </td>
            </tr>
        `;
    }).join("");
}

function renderPaymentSummaryDirect(order) {
    const summaryBox = document.getElementById("order-payment-summary-box");
    const paymentsTbody = document.getElementById("order-payments-table-body");

    let totalGoodsAmt = 0;
    let preorderAmt = 0;
    let inStockAmt = 0;
    const items = order.order_items || order.items || [];
    items.forEach(i => {
        if (i.item_status !== "ĐÃ HỦY") {
            const amt = Number(i.price) * Number(i.quantity);
            totalGoodsAmt += amt;
            if (i.preorder_id) preorderAmt += amt;
            else inStockAmt += amt;
        }
    });

    const shippingFee = Number(order.shipping_fee || 0);
    const totalAmount = Number(order.total_amount || 0) + shippingFee;

    let totalPaid = 0;
    const payments = order.payments || [];
    payments.forEach(p => {
        if (p.payment_status === "ĐÃ THANH TOÁN") totalPaid += Number(p.amount || 0);
    });

    const remaining = Math.max(0, totalAmount - totalPaid);
    const goodsEl = document.getElementById("summary-goods-amount");
    const shipEl = document.getElementById("summary-shipping-fee");
    const totalEl = document.getElementById("summary-total-amount");
    const statusEl = document.getElementById("summary-order-status");

    if (goodsEl) goodsEl.textContent = formatOrderPrice(totalGoodsAmt);
    if (shipEl) shipEl.textContent = formatOrderPrice(shippingFee);
    if (totalEl) totalEl.textContent = formatOrderPrice(totalAmount);
    if (statusEl) statusEl.textContent = order.order_status || "—";

    if (summaryBox) {
        summaryBox.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; background: #f9fafb; padding: 16px; border-radius: 8px; border: 1px solid #e5e7eb;">
                <div><span style="color: #6b7280; font-size: 12px;">Tiền hàng có sẵn:</span> <strong style="display: block; font-size: 14px;">${formatOrderPrice(inStockAmt)}</strong></div>
                <div><span style="color: #6b7280; font-size: 12px;">Tiền hàng Pre-order:</span> <strong style="display: block; font-size: 14px;">${formatOrderPrice(preorderAmt)}</strong></div>
                <div><span style="color: #6b7280; font-size: 12px;">Phí vận chuyển:</span> <strong style="display: block; font-size: 14px;">${formatOrderPrice(shippingFee)}</strong></div>
                <div><span style="color: #6b7280; font-size: 12px;">Tổng giá trị đơn:</span> <strong style="display: block; font-size: 14px; color: #d97706;">${formatOrderPrice(totalAmount)}</strong></div>
                <div><span style="color: #6b7280; font-size: 12px;">Đã thanh toán:</span> <strong style="display: block; font-size: 14px; color: #22c55e;">${formatOrderPrice(totalPaid)}</strong></div>
                <div><span style="color: #6b7280; font-size: 12px;">Còn lại cần trả:</span> <strong style="display: block; font-size: 14px; color: #ef4444;">${formatOrderPrice(remaining)}</strong></div>
            </div>
        `;
    }

    if (paymentsTbody) {
        if (!payments.length) {
            paymentsTbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--admin-muted, #6b7280); padding: 15px;">Chưa có giao dịch thanh toán nào.</td></tr>`;
            return;
        }

        paymentsTbody.innerHTML = payments.map(p => `
            <tr>
                <td><strong>${escapeOrderHTML(p.transaction_id)}</strong></td>
                <td>${escapeOrderHTML(p.payment_type)}</td>
                <td>${escapeOrderHTML(p.payment_method)}</td>
                <td style="font-weight: 700; color: #d97706;">${formatOrderPrice(p.amount)}</td>
                <td><span class="admin-product-status ${p.payment_status === 'ĐÃ THANH TOÁN' ? 'hoan-thanh' : 'cho-xac-nhan'}">${escapeOrderHTML(p.payment_status)}</span></td>
                <td>${p.created_at ? String(p.created_at).split('T')[0] : '—'}</td>
                <td style="text-align: center;">
                    ${p.payment_status === 'ĐANG THANH TOÁN' ? `
                        <button type="button" class="admin-btn admin-btn-primary" style="padding: 2px 8px; font-size: 11px;" onclick="confirmPaymentAdmin(${p.payment_id})">
                            Xác nhận
                        </button>
                    ` : '—'}
                </td>
            </tr>
        `).join("");
    }
}

async function changeOrderStatus(orderId, newStatus) {
    if (!confirm(`Xác nhận chuyển trạng thái đơn hàng sang "${newStatus}"?`)) return;
    const token = getAdminToken();

    try {
        const res = await fetch(`/api/orders/admin/${orderId}/status`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ order_status: newStatus })
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Không thể cập nhật trạng thái");

        showOrderToast("Cập nhật trạng thái đơn thành công!");
        await openOrderDetail(orderId);
        await loadAdminOrders(false);
    } catch (e) {
        showOrderToast(e.message);
    }
}

async function submitOrderShipping() {
    if (!currentViewingOrder) return;
    const token = getAdminToken();
    const trackingCode = document.getElementById("ship-tracking-code")?.value.trim();
    const shippingMethod = document.getElementById("ship-method")?.value;
    const shippingFee = Number(document.getElementById("ship-fee")?.value) || 0;

    if (!trackingCode) {
        showOrderToast("Vui lòng nhập mã vận đơn");
        return;
    }

    const items = currentViewingOrder.order_items || currentViewingOrder.items || [];
    const validItemIds = items.filter(i => i.item_status !== 'ĐÃ HỦY' && !i.tracking_code).map(i => i.order_item_id);

    if (!validItemIds.length) {
        showOrderToast("Tất cả sản phẩm đã được gán mã vận chuyển hoặc đã bị hủy");
        return;
    }

    try {
        const res = await fetch(`/api/orders/admin/${currentViewingOrder.order_id}/shipping`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({
                order_item_ids: validItemIds,
                shipping_method: shippingMethod,
                shipping_fee: shippingFee,
                tracking_code: trackingCode
            })
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Không thể gán vận chuyển");

        showOrderToast("Gán thông tin vận chuyển thành công!");
        document.getElementById("ship-tracking-code").value = "";
        await openOrderDetail(currentViewingOrder.order_id);
    } catch (e) {
        showOrderToast(e.message);
    }
}

async function cancelItem(orderItemId) {
    if (!confirm("Bạn có chắc muốn hủy sản phẩm này trong đơn?")) return;
    const token = getAdminToken();
    try {
        const res = await fetch(`/api/orders/items/${orderItemId}/cancel`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Không thể hủy sản phẩm");

        showOrderToast("Đã hủy sản phẩm");
        if (currentViewingOrder) await openOrderDetail(currentViewingOrder.order_id);
    } catch (e) {
        showOrderToast(e.message);
    }
}

async function confirmPaymentAdmin(paymentId) {
    if (!confirm("Xác nhận đã nhận khoản thanh toán này?")) return;
    const token = getAdminToken();
    try {
        const res = await fetch(`/api/orders/admin/payments/${paymentId}/confirm`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Không thể xác nhận thanh toán");

        showOrderToast("Xác nhận thanh toán thành công");
        if (currentViewingOrder) await openOrderDetail(currentViewingOrder.order_id);
    } catch (e) {
        showOrderToast(e.message);
    }
}

function renderShippingList(items) {
    const tbody = document.getElementById("order-shipping-table-body");
    if (!tbody) return;

    const shippedItems = items.filter(i => i.tracking_code);

    if (!shippedItems.length) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--admin-muted, #6b7280); padding: 15px;">Chưa có kiện hàng / mã vận đơn nào.</td></tr>`;
        return;
    }

    const grouped = {};
    shippedItems.forEach(i => {
        if (!grouped[i.tracking_code]) {
            grouped[i.tracking_code] = {
                tracking_code: i.tracking_code,
                shipping_method: i.shipping_method,
                shipping_status: i.shipping_status || "ĐANG LẤY HÀNG",
                products: []
            };
        }
        grouped[i.tracking_code].products.push(i.product?.product_name || `Sản phẩm #${i.product_id} (x${i.quantity})`);
    });

    tbody.innerHTML = Object.values(grouped).map(pkg => {
        let nextStatus = null;
        let btnText = "";
        if (pkg.shipping_status === "ĐANG LẤY HÀNG") {
            nextStatus = "ĐANG GIAO HÀNG";
            btnText = "Chuyển sang: Đang giao hàng";
        } else if (pkg.shipping_status === "ĐANG GIAO HÀNG") {
            nextStatus = "ĐÃ GIAO";
            btnText = "Xác nhận: Đã giao";
        }

        return `
            <tr>
                <td><strong>${escapeOrderHTML(pkg.tracking_code)}</strong></td>
                <td>${escapeOrderHTML(pkg.shipping_method || "TIÊU CHUẨN")}</td>
                <td style="font-size: 12px; color: #4b5563;">${pkg.products.map(p => escapeOrderHTML(p)).join("<br>")}</td>
                <td>
                    <span class="admin-product-status ${pkg.shipping_status === 'ĐÃ GIAO' ? 'hoan-thanh' : 'dang-xu-ly'}">
                        ${escapeOrderHTML(pkg.shipping_status)}
                    </span>
                </td>
                <td style="text-align: center;">
                    ${nextStatus ? `
                        <button type="button" class="admin-btn admin-btn-primary" style="padding: 4px 10px; font-size: 12px;"
                            onclick="updateShippingStatusAdmin('${pkg.tracking_code}', '${nextStatus}')">
                            ${btnText}
                        </button>
                    ` : '<span style="color: #22c55e; font-weight: 600; font-size: 12px;"><i class="bx bx-check"></i> Đã hoàn tất giao</span>'}
                </td>
            </tr>
        `;
    }).join("");
}

async function updateShippingStatusAdmin(trackingCode, newStatus) {
    if (!confirm(`Xác nhận chuyển trạng thái mã vận đơn "${trackingCode}" sang "${newStatus}"?`)) return;
    const token = getAdminToken();

    try {
        const res = await fetch(`/api/orders/admin/shipping/${trackingCode}/status`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ shipping_status: newStatus })
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Không thể cập nhật trạng thái vận chuyển");

        showOrderToast("Cập nhật trạng thái vận chuyển thành công!");
        if (currentViewingOrder) await openOrderDetail(currentViewingOrder.order_id);
    } catch (e) {
        showOrderToast(e.message);
    }
}

function showOrderToast(msg) {
    const toast = document.getElementById("admin-order-toast");
    if (!toast) {
        alert(msg);
        return;
    }
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}

window.updateShippingStatusAdmin = updateShippingStatusAdmin;

window.goToOrderPage = goToOrderPage;
window.openOrderDetail = openOrderDetail;
window.changeOrderStatus = changeOrderStatus;
window.cancelItem = cancelItem;
window.confirmPaymentAdmin = confirmPaymentAdmin;