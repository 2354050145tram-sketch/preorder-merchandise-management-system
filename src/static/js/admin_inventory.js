let allInvData = [];
let currentInvPage = 1;
const INV_PAGE_SIZE = 10;

let currentViewingInv = null;
let invSearchDebounce = null;
let invFetchController = null;

// DOM Elements
const invListView = document.getElementById("inv-list-view");
const invFormView = document.getElementById("inv-form-view");
const invListControlPanel = document.getElementById("inv-list-control-panel");
const invFormControlPanel = document.getElementById("inv-form-control-panel");
const invTable = document.getElementById("admin-inv-table");
const invTableBody = document.getElementById("admin-inv-table-body");
const invLoadingState = document.getElementById("admin-inv-loading");
const invEmptyState = document.getElementById("admin-inv-empty");
const invPagination = document.getElementById("admin-inv-pagination");

function getAdminToken() {
    return localStorage.getItem("access_token")
        || localStorage.getItem("token")
        || localStorage.getItem("jwt_token")
        || sessionStorage.getItem("access_token")
        || sessionStorage.getItem("token");
}

function formatInvPrice(val) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);
}

function escapeInvHTML(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function showInvToast(msg) {
    const toast = document.getElementById("admin-inv-toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    clearTimeout(toast.hideTimer);
    toast.hideTimer = setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
}

document.addEventListener("DOMContentLoaded", () => {
    bindInvEvents();
    showInvListView();
    loadAdminInventory(true);
});

function bindInvEvents() {
    document.getElementById("reload-inv-btn")?.addEventListener("click", () => loadAdminInventory(true));
    document.getElementById("discard-inv-btn")?.addEventListener("click", showInvListView);

    // Tìm kiếm
    const keywordInput = document.getElementById("admin-inv-keyword");
    keywordInput?.addEventListener("input", () => {
        clearTimeout(invSearchDebounce);
        invSearchDebounce = setTimeout(() => {
            currentInvPage = 1;
            loadAdminInventory(false);
        }, 300);
    });

    // Lọc trạng thái Backend
    document.getElementById("admin-inv-filter")?.addEventListener("change", () => {
        currentInvPage = 1;
        loadAdminInventory(false);
    });

    // Sắp xếp Client
    document.getElementById("admin-inv-sort")?.addEventListener("change", () => {
        currentInvPage = 1;
        renderInvPaginatedTable();
    });

    // Thay đổi loại thao tác kho
    document.getElementById("inv-action-type")?.addEventListener("change", (e) => {
        const type = e.target.value;
        const priceField = document.getElementById("inv-price-field-block");
        const qtyLabel = document.getElementById("inv-action-qty-label");

        if (type === "IMPORT") {
            if (priceField) priceField.style.display = "flex";
            if (qtyLabel) qtyLabel.textContent = "Số lượng nhập thêm (+)";
        } else if (type === "EXPORT") {
            if (priceField) priceField.style.display = "none";
            if (qtyLabel) qtyLabel.textContent = "Số lượng xuất kho (-)";
        } else {
            if (priceField) priceField.style.display = "none";
            if (qtyLabel) qtyLabel.textContent = "Số lượng tồn mới";
        }
    });

    document.getElementById("btn-submit-inv-action")?.addEventListener("click", submitInvAction);

    // Chuyển tab
    document.querySelectorAll(".product-tab").forEach(button => {
        button.addEventListener("click", () => {
            switchInvTab(button.dataset.invTab);
        });
    });
}

function switchInvTab(tabName) {
    document.querySelectorAll(".product-tab").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.invTab === tabName);
    });
    document.querySelectorAll(".product-tab-content").forEach(content => {
        const isActive = content.dataset.invContent === tabName;
        content.classList.toggle("active", isActive);
        content.style.setProperty("display", isActive ? "block" : "none", "important");
    });
}

function showInvListView() {
    if (invFormView) invFormView.style.setProperty("display", "none", "important");
    if (invListView) invListView.style.setProperty("display", "block", "important");
    if (invFormControlPanel) invFormControlPanel.style.setProperty("display", "none", "important");
    if (invListControlPanel) invListControlPanel.style.setProperty("display", "flex", "important");

    const breadcrumb = document.getElementById("inv-breadcrumb-current");
    if (breadcrumb) breadcrumb.textContent = "Tồn kho";
    currentViewingInv = null;
}

function showInvDetailView() {
    if (invListView) invListView.style.setProperty("display", "none", "important");
    if (invFormView) invFormView.style.setProperty("display", "block", "important");
    if (invListControlPanel) invListControlPanel.style.setProperty("display", "none", "important");
    if (invFormControlPanel) invFormControlPanel.style.setProperty("display", "flex", "important");
}

// 1. TẢI DỮ LIỆU TỒN KHO TỪ BACKEND
async function loadAdminInventory(showSpinner = false) {
    if (invFetchController) invFetchController.abort();
    invFetchController = new AbortController();

    const keyword = document.getElementById("admin-inv-keyword")?.value.trim() || "";
    const status = document.getElementById("admin-inv-filter")?.value || "";

    const params = new URLSearchParams();
    if (keyword) params.set("keyword", keyword);
    if (status) params.set("status", status);

    if (showSpinner) {
        if (invLoadingState) invLoadingState.style.display = "flex";
        if (invEmptyState) invEmptyState.style.display = "none";
        if (invTable) invTable.style.display = "none";
        if (invPagination) invPagination.style.display = "none";
    }

    const token = getAdminToken();
    try {
        const res = await fetch(`/api/inventories/admin?${params.toString()}`, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            signal: invFetchController.signal
        });

        if (!res.ok) throw new Error("Không thể tải danh sách tồn kho");

        const result = await res.json();
        allInvData = result.data?.inventories || result.inventories || [];
        renderInvPaginatedTable();
    } catch (e) {
        if (e.name === "AbortError") return;
        console.error("Load inventory error:", e);
        showInvToast(e.message || "Lỗi tải kho");
        allInvData = [];
        renderInvPaginatedTable();
    } finally {
        if (showSpinner && invLoadingState) invLoadingState.style.display = "none";
    }
}

// 2. RENDER BẢNG VÀ PHÂN TRANG
function renderInvPaginatedTable() {
    const sortType = document.getElementById("admin-inv-sort")?.value || "qty_desc";

    let sortedList = [...allInvData];
    sortedList.sort((a, b) => {
        const qtyA = Number(a.quantity || 0);
        const qtyB = Number(b.quantity || 0);
        const nameA = String(a.product?.product_name || a.product_name || "");
        const nameB = String(b.product?.product_name || b.product_name || "");

        if (sortType === "qty_desc") return qtyB - qtyA;
        if (sortType === "qty_asc") return qtyA - qtyB;
        if (sortType === "name_asc") return nameA.localeCompare(nameB);
        if (sortType === "name_desc") return nameB.localeCompare(nameA);
        return 0;
    });

    const total = sortedList.length;
    const countEl = document.getElementById("admin-table-inv-count");
    if (countEl) countEl.textContent = `(${total})`;

    if (!total) {
        if (invEmptyState) invEmptyState.style.display = "flex";
        if (invTable) invTable.style.display = "none";
        if (invPagination) invPagination.style.display = "none";
        return;
    }

    if (invEmptyState) invEmptyState.style.display = "none";
    if (invTable) invTable.style.display = "table";

    const totalPages = Math.ceil(total / INV_PAGE_SIZE) || 1;
    if (currentInvPage > totalPages) currentInvPage = totalPages;
    if (currentInvPage < 1) currentInvPage = 1;

    const startIdx = (currentInvPage - 1) * INV_PAGE_SIZE;
    const endIdx = Math.min(startIdx + INV_PAGE_SIZE, total);
    const paged = sortedList.slice(startIdx, endIdx);

    invTableBody.innerHTML = paged.map(item => {
        const qty = Number(item.quantity || 0);
        const statusText = item.status || (qty === 0 ? "HẾT HÀNG" : (qty < 10 ? "SẮP HẾT HÀNG" : "CÒN HÀNG"));

        let statusClass = "instock";
        if (statusText === "HẾT HÀNG") statusClass = "outstock";
        else if (statusText === "SẮP HẾT HÀNG") statusClass = "lowstock";

        const pName = item.product?.product_name || item.product_name || `Sản phẩm #${item.product_id}`;

        return `
        <tr onclick="openInvDetail(${item.product_id})" style="cursor: pointer;">
            <td><strong style="color: #111827; font-size: 14px;">#${item.product_id}</strong></td>
            <td>
                <strong style="color: #111827; font-size: 14px;">${escapeInvHTML(pName)}</strong>
            </td>
            <td style="color: #374151; font-size: 13px;">${formatInvPrice(item.price)}</td>
            <td style="font-weight: 700; color: #d97706; font-size: 15px;">${qty}</td>
            <td style="text-align: center;">
                <span class="admin-product-status ${statusClass}">${escapeInvHTML(statusText)}</span>
            </td>
            <td style="color: #6b7280; font-size: 13px;">${item.created_at ? String(item.created_at).split('T')[0] : '—'}</td>
        </tr>
    `;
    }).join("");

    renderInvPaginationControls(totalPages);
}

function renderInvPaginationControls(totalPages) {
    if (!invPagination) return;

    if (totalPages <= 1) {
        invPagination.style.display = "none";
        return;
    }

    invPagination.style.display = "flex";
    const btnContainer = document.getElementById("admin-inv-pagination-buttons");
    let btnsHtml = `
        <button class="admin-page-btn" onclick="goToInvPage(${currentInvPage - 1})" ${currentInvPage === 1 ? 'disabled' : ''}>
            <i class='bx bx-chevron-left'></i>
        </button>
    `;

    let startPage = Math.max(1, currentInvPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);

    for (let p = startPage; p <= endPage; p++) {
        btnsHtml += `
            <button class="admin-page-btn ${p === currentInvPage ? 'active' : ''}" onclick="goToInvPage(${p})">
                ${p}
            </button>
        `;
    }

    btnsHtml += `
        <button class="admin-page-btn" onclick="goToInvPage(${currentInvPage + 1})" ${currentInvPage === totalPages ? 'disabled' : ''}>
            <i class='bx bx-chevron-right'></i>
        </button>
    `;

    btnContainer.innerHTML = btnsHtml;
}

function goToInvPage(page) {
    currentInvPage = page;
    renderInvPaginatedTable();
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// 3. MỞ CHI TIẾT KHO & LẤY NHẬT KÝ GIAO DỊCH TỪ BACKEND
async function openInvDetail(productId) {
    const item = allInvData.find(i => Number(i.product_id) === Number(productId));
    if (!item) return;

    currentViewingInv = item;

    const pName = item.product?.product_name || item.product_name || `Sản phẩm #${item.product_id}`;
    document.getElementById("inv-breadcrumb-current").textContent = pName;
    document.getElementById("inv-form-mode").textContent = `Kho #${item.product_id}`;

    document.getElementById("inv-product-name-display").textContent = pName;
    document.getElementById("inv-product-id-display").textContent = `#${item.product_id}`;
    document.getElementById("inv-current-qty-display").textContent = item.quantity || 0;

    // Reset Form
    document.getElementById("inv-action-type").value = "IMPORT";
    document.getElementById("inv-action-qty").value = "";
    document.getElementById("inv-action-price").value = item.price ? Number(item.price) : "";
    document.getElementById("inv-price-field-block").style.display = "flex";
    document.getElementById("inv-action-qty-label").textContent = "Số lượng nhập thêm (+)";

    // Tải nhật ký giao dịch
    await loadInventoryTransactions(item.product_id);

    switchInvTab("adjust");
    showInvDetailView();
}

async function loadInventoryTransactions(productId) {
    const token = getAdminToken();
    const tbody = document.getElementById("inv-history-table-body");
    if (!tbody) return;

    try {
        const res = await fetch(`/api/inventories/admin/transactions?product_id=${productId}`, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            }
        });

        if (!res.ok) throw new Error(`HTTP Error ${res.status}`);

        const result = await res.json();
        const transactions = result.data?.transactions || result.transactions || [];

        if (!transactions.length) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--admin-muted, #6b7280); padding: 16px;">Chưa có lịch sử giao dịch nào cho sản phẩm này.</td></tr>`;
            return;
        }

        tbody.innerHTML = transactions.map(t => {
            const isPlus = t.transaction_type === "NHẬP" || t.transaction_type === "HOÀN KHO";
            let typeBadge = "instock";
            if (t.transaction_type === "XUẤT") typeBadge = "outstock";
            else if (t.transaction_type === "ĐIỀU CHỈNH") typeBadge = "lowstock";

            // Lấy đúng mã giao dịch
            const transId = t.transaction_id || t.inventory_transaction_id || "—";

            return `
                <tr>
                    <td><strong>#${transId}</strong></td>
                    <td><span class="admin-product-status ${typeBadge}">${escapeInvHTML(t.transaction_type)}</span></td>
                    <td style="font-weight: 700; color: ${isPlus ? '#22c55e' : (t.transaction_type === 'XUẤT' ? '#ef4444' : '#d97706')};">
                        ${isPlus ? '+' : '-'}${t.quantity}
                    </td>
                    <td>${t.price ? formatInvPrice(t.price) : '—'}</td>
                    <td style="color: #6b7280; font-size: 13px;">${t.created_at ? String(t.created_at).replace('T', ' ').slice(0, 19) : '—'}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error("Lỗi loadInventoryTransactions:", e);
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #ef4444; padding: 16px;">Lỗi tải nhật ký kho.</td></tr>`;
    }
}

// 4. THỰC HIỆN THAO TÁC KHO (KẾT NỐI ROUTE IMPORT, EXPORT, QUANTITY)
async function submitInvAction() {
    if (!currentViewingInv) return;
    const actionType = document.getElementById("inv-action-type")?.value;
    const qty = Number(document.getElementById("inv-action-qty")?.value);
    const price = Number(document.getElementById("inv-action-price")?.value);
    const productId = currentViewingInv.product_id;

    if (!qty || qty <= 0) {
        showInvToast("Vui lòng nhập số lượng hợp lệ (> 0)");
        return;
    }

    let url = "";
    let method = "POST";
    let payload = {};

    if (actionType === "IMPORT") {
        if (!price || price <= 0) {
            showInvToast("Vui lòng nhập giá nhập hợp lệ (> 0)");
            return;
        }
        url = `/api/inventories/admin/${productId}/import`;
        payload = { quantity: qty, price: price };
    } else if (actionType === "EXPORT") {
        url = `/api/inventories/admin/${productId}/export`;
        payload = { quantity: qty };
    } else if (actionType === "UPDATE") {
        url = `/api/inventories/admin/${productId}/quantity`;
        method = "PUT";
        payload = { quantity: qty };
    }

    const token = getAdminToken();
    try {
        const res = await fetch(url, {
            method: method,
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Không thể thực hiện thao tác");

        showInvToast(result.message || "Cập nhật kho thành công!");
        await loadAdminInventory(false);
        showInvListView();
    } catch (e) {
        showInvToast(e.message);
    }
}

window.goToInvPage = goToInvPage;
window.openInvDetail = openInvDetail;