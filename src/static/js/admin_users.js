let allUsersData = [];
let currentUserPage = 1;
const USER_PAGE_SIZE = 10;

let currentViewingUser = null;
let userSearchDebounce = null;
let userFetchController = null;

const userListView = document.getElementById("user-list-view");
const userFormView = document.getElementById("user-form-view");
const userListControlPanel = document.getElementById("user-list-control-panel");
const userFormControlPanel = document.getElementById("user-form-control-panel");
const userTable = document.getElementById("admin-user-table");
const userTableBody = document.getElementById("admin-user-table-body");
const userLoadingState = document.getElementById("admin-user-loading");
const userEmptyState = document.getElementById("admin-user-empty");
const userPagination = document.getElementById("admin-user-pagination");

function getAdminToken() {
    return localStorage.getItem("access_token")
        || localStorage.getItem("token")
        || localStorage.getItem("jwt_token")
        || sessionStorage.getItem("access_token")
        || sessionStorage.getItem("token");
}

function formatUserPrice(val) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);
}

function escapeUserHTML(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function showUserToast(msg) {
    const toast = document.getElementById("admin-user-toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    clearTimeout(toast.hideTimer);
    toast.hideTimer = setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
}

document.addEventListener("DOMContentLoaded", () => {
    bindUserEvents();
    showUserListView();
    loadAdminUsers(true);
});

function bindUserEvents() {
    document.getElementById("reload-users-btn")?.addEventListener("click", () => loadAdminUsers(true));
    document.getElementById("discard-user-btn")?.addEventListener("click", showUserListView);

    const keywordInput = document.getElementById("admin-user-keyword");
    keywordInput?.addEventListener("input", () => {
        clearTimeout(userSearchDebounce);
        userSearchDebounce = setTimeout(() => {
            currentUserPage = 1;
            renderUserPaginatedTable();
        }, 300);
    });

    document.getElementById("admin-user-sort")?.addEventListener("change", () => {
        currentUserPage = 1;
        renderUserPaginatedTable();
    });

    document.querySelectorAll(".user-tab-btn").forEach(button => {
        button.addEventListener("click", () => {
            switchUserTab(button.dataset.userTab);
        });
    });
}

function switchUserTab(tabName) {
    document.querySelectorAll(".user-tab-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.userTab === tabName);
    });
    document.querySelectorAll(".user-tab-pane").forEach(content => {
        const isActive = content.dataset.userContent === tabName;
        content.classList.toggle("active", isActive);
        content.style.setProperty("display", isActive ? "block" : "none", "important");
    });
}

function showUserListView() {
    if (userFormView) userFormView.style.setProperty("display", "none", "important");
    if (userListView) userListView.style.setProperty("display", "block", "important");
    if (userFormControlPanel) userFormControlPanel.style.setProperty("display", "none", "important");
    if (userListControlPanel) userListControlPanel.style.setProperty("display", "flex", "important");

    const breadcrumb = document.getElementById("user-breadcrumb-current");
    if (breadcrumb) breadcrumb.textContent = "Danh sách";
    currentViewingUser = null;
}

function showUserDetailView() {
    if (userListView) userListView.style.setProperty("display", "none", "important");
    if (userFormView) userFormView.style.setProperty("display", "block", "important");
    if (userListControlPanel) userListControlPanel.style.setProperty("display", "none", "important");
    if (userFormControlPanel) userFormControlPanel.style.setProperty("display", "flex", "important");
}

async function loadAdminUsers(showSpinner = false) {
    if (userFetchController) userFetchController.abort();
    userFetchController = new AbortController();

    if (showSpinner) {
        if (userLoadingState) userLoadingState.style.display = "flex";
        if (userEmptyState) userEmptyState.style.display = "none";
        if (userTable) userTable.style.display = "none";
        if (userPagination) userPagination.style.display = "none";
    }

    const token = getAdminToken();
    try {
        const res = await fetch(`/api/users/admin`, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            signal: userFetchController.signal
        });

        if (!res.ok) {
            throw new Error(`Lỗi máy chủ (${res.status})`);
        }

        const result = await res.json();
        allUsersData = result.data?.users || result.users || (Array.isArray(result) ? result : []);
        renderUserPaginatedTable();
    } catch (e) {
        if (e.name === "AbortError") return;
        console.error("Load users error:", e);
        showUserToast(e.message || "Lỗi tải người dùng");
        allUsersData = [];
        renderUserPaginatedTable();
    } finally {
        if (showSpinner && userLoadingState) userLoadingState.style.display = "none";
    }
}

function renderUserPaginatedTable() {
    const keyword = document.getElementById("admin-user-keyword")?.value.trim().toLowerCase() || "";
    const sortType = document.getElementById("admin-user-sort")?.value || "newest";

    let filtered = allUsersData.filter(u => {
        const name = (u.username || "").toLowerCase();
        const email = (u.email || "").toLowerCase();
        const uid = String(u.user_id || "");
        return !keyword || name.includes(keyword) || email.includes(keyword) || uid.includes(keyword);
    });

    filtered.sort((a, b) => {
        const idA = Number(a.user_id || 0);
        const idB = Number(b.user_id || 0);
        const walletA = Number(a.wallet_balance || 0);
        const walletB = Number(b.wallet_balance || 0);
        const ordersCountA = (a.orders || []).length;
        const ordersCountB = (b.orders || []).length;

        if (sortType === "oldest") return idA - idB;
        if (sortType === "wallet_desc") return (walletB - walletA) || (idB - idA);
        if (sortType === "wallet_asc") return (walletA - walletB) || (idB - idA);
        if (sortType === "orders_desc") return (ordersCountB - ordersCountA) || (idB - idA);
        if (sortType === "orders_asc") return (ordersCountA - ordersCountB) || (idB - idA);
        
        return idB - idA;
    });

    const total = filtered.length;
    const countEl = document.getElementById("admin-table-user-count");
    if (countEl) countEl.textContent = `(${total})`;

    if (!total) {
        if (userEmptyState) userEmptyState.style.display = "flex";
        if (userTable) userTable.style.display = "none";
        if (userPagination) userPagination.style.display = "none";
        return;
    }

    if (userEmptyState) userEmptyState.style.display = "none";
    if (userTable) userTable.style.display = "table";

    const totalPages = Math.ceil(total / USER_PAGE_SIZE) || 1;
    if (currentUserPage > totalPages) currentUserPage = totalPages;
    if (currentUserPage < 1) currentUserPage = 1;

    const startIdx = (currentUserPage - 1) * USER_PAGE_SIZE;
    const endIdx = Math.min(startIdx + USER_PAGE_SIZE, total);
    const paged = filtered.slice(startIdx, endIdx);

    userTableBody.innerHTML = paged.map(u => {
        const isAdmin = u.role_id === 0;
        const isActive = u.active !== false && u.active !== 0;

        return `
        <tr onclick="openUserDetail(${u.user_id})" style="cursor: pointer;">
            <td><strong style="color: #111827; font-size: 14px;">#${u.user_id}</strong></td>
            <td>
                <strong style="color: #111827; font-size: 14px;">${escapeUserHTML(u.username)}</strong>
            </td>
            <td style="color: #374151; font-size: 13px;">${escapeUserHTML(u.email || '—')}</td>
            <td>
                <span class="admin-product-status ${isAdmin ? 'admin-role' : 'customer-role'}">
                    ${isAdmin ? 'ADMIN' : 'CUSTOMER'}
                </span>
            </td>
            <td style="font-weight: 700; color: #d97706; font-size: 14px;">
                ${formatUserPrice(u.wallet_balance || 0)}
            </td>
            <td style="text-align: center;">
                <span class="admin-product-status ${isActive ? 'active-status' : 'locked-status'}">
                    ${isActive ? 'HOẠT ĐỘNG' : 'BỊ KHÓA'}
                </span>
            </td>
        </tr>
    `;
    }).join("");

    renderUserPaginationControls(totalPages);
}

function renderUserPaginationControls(totalPages) {
    if (!userPagination) return;

    if (totalPages <= 1) {
        userPagination.style.display = "none";
        return;
    }

    userPagination.style.display = "flex";
    const btnContainer = document.getElementById("admin-user-pagination-buttons");
    let btnsHtml = `
        <button class="admin-page-btn" onclick="goToUserPage(${currentUserPage - 1})" ${currentUserPage === 1 ? 'disabled' : ''}>
            <i class='bx bx-chevron-left'></i>
        </button>
    `;

    let startPage = Math.max(1, currentUserPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);

    for (let p = startPage; p <= endPage; p++) {
        btnsHtml += `
            <button class="admin-page-btn ${p === currentUserPage ? 'active' : ''}" onclick="goToUserPage(${p})">
                ${p}
            </button>
        `;
    }

    btnsHtml += `
        <button class="admin-page-btn" onclick="goToUserPage(${currentUserPage + 1})" ${currentUserPage === totalPages ? 'disabled' : ''}>
            <i class='bx bx-chevron-right'></i>
        </button>
    `;

    btnContainer.innerHTML = btnsHtml;
}

function goToUserPage(page) {
    currentUserPage = page;
    renderUserPaginatedTable();
    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function openUserDetail(userId) {
    const token = getAdminToken();
    try {
        const res = await fetch(`/api/users/admin/${userId}`, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            }
        });

        if (!res.ok) throw new Error("Không thể lấy dữ liệu người dùng");

        const result = await res.json();
        const user = result.data?.user || result.user || result;
        if (!user) throw new Error("Không tìm thấy người dùng");

        currentViewingUser = user;

        document.getElementById("user-breadcrumb-current").textContent = user.username;
        document.getElementById("user-form-mode").textContent = `Người dùng #${user.user_id}`;

        const initial = (user.username || "U").charAt(0).toUpperCase();
        document.getElementById("user-avatar-text").textContent = initial;

        document.getElementById("user-detail-name-display").textContent = user.username;
        document.getElementById("user-email-display").textContent = user.email || "—";
        const rawDate = user.created_at || "";
        document.getElementById("user-created-date-display").textContent = rawDate ? String(rawDate).split('T')[0] : "—";

        const walBal = Number(user.wallet_balance || 0);
        const ords = user.orders || [];
        document.getElementById("user-hero-wallet").textContent = formatUserPrice(walBal);
        document.getElementById("user-hero-orders").textContent = `${ords.length} đơn`;

        renderUserHeaderActions(user);
        renderUserOrders(ords);
        renderUserWallet(user);

        switchUserTab("orders");
        showUserDetailView();
    } catch (e) {
        showUserToast(e.message || "Lỗi tải chi tiết người dùng");
    }
}

function renderUserHeaderActions(user) {
    const container = document.getElementById("user-header-actions");
    if (!container) return;
    const isActive = user.active !== false && user.active !== 0;

    if (user.role_id === 0) {
        container.innerHTML = "";
        return;
    }

    container.innerHTML = `
        <button type="button" class="admin-btn ${isActive ? 'admin-btn-secondary' : 'admin-btn-primary'}" onclick="toggleUserActive(${user.user_id}, ${!isActive})">
            <i class='bx ${isActive ? 'bx-lock-alt' : 'bx-lock-open-alt'}'></i> ${isActive ? 'Khóa tài khoản' : 'Mở khóa'}
        </button>
    `;
}

function renderUserOrders(orders) {
    const tbody = document.getElementById("user-orders-table-body");
    if (!tbody) return;

    let totalSpent = 0;
    if (!orders.length) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--admin-muted, #6b7280); padding: 20px;">Chưa có đơn hàng nào.</td></tr>`;
    } else {
        tbody.innerHTML = orders.map(o => {
            const amt = Number(o.total_amount || 0);
            if (o.order_status !== 'ĐÃ HỦY') totalSpent += amt;

            let statusClass = "customer-role";
            if (o.order_status === "HOÀN THÀNH" || o.order_status === "ĐÃ XÁC NHẬN") statusClass = "active-status";
            else if (o.order_status === "ĐÃ HỦY") statusClass = "locked-status";
            else if (o.order_status === "CHỜ XÁC NHẬN") statusClass = "admin-role";

            return `
                <tr>
                    <td><strong style="color: #111827;">#${o.order_id}</strong></td>
                    <td style="color: #374151; font-size: 13px;">${o.order_date || (o.created_at ? String(o.created_at).split('T')[0] : '—')}</td>
                    <td style="font-weight: 700; color: #d97706;">${formatUserPrice(amt)}</td>
                    <td style="text-align: center;">
                        <span class="admin-product-status ${statusClass}">${escapeUserHTML(o.order_status)}</span>
                    </td>
                </tr>
            `;
        }).join("");
    }

    const totalOrdersEl = document.getElementById("user-summary-total-orders");
    const totalSpentEl = document.getElementById("user-summary-total-spent");
    const walletBalEl = document.getElementById("user-summary-wallet-balance");
    const statusEl = document.getElementById("user-summary-status");

    if (totalOrdersEl) totalOrdersEl.textContent = `${orders.length} đơn`;
    if (totalSpentEl) totalSpentEl.textContent = formatUserPrice(totalSpent);
    if (walletBalEl) walletBalEl.textContent = formatUserPrice(currentViewingUser?.wallet_balance || 0);

    if (statusEl) {
        const isActive = currentViewingUser?.active !== false && currentViewingUser?.active !== 0;
        statusEl.textContent = isActive ? "Đang hoạt động" : "Bị khóa";
        statusEl.style.color = isActive ? "#16a34a" : "#dc2626";
    }
}

function renderUserWallet(user) {
    const tbody = document.getElementById("user-wallet-table-body");
    if (!tbody) return;

    const trans = user.wallet_transactions || [];
    if (!trans.length) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--admin-muted, #6b7280); padding: 20px;">Chưa có giao dịch ví nào.</td></tr>`;
        return;
    }

    tbody.innerHTML = trans.map(t => {
        const isPlus = t.transaction_type === 'NẠP TIỀN' || t.transaction_type === 'HOÀN TIỀN';

        return `
            <tr>
                <td><strong>#${t.transaction_id || '—'}</strong></td>
                <td><span class="admin-product-status ${isPlus ? 'active-status' : 'customer-role'}">${escapeUserHTML(t.transaction_type)}</span></td>
                <td style="font-weight: 700; color: ${isPlus ? '#16a34a' : '#111827'};">
                    ${isPlus ? '+' : '-'}${formatUserPrice(t.amount)}
                </td>
                <td style="color: #374151; font-size: 13px;">${escapeUserHTML(t.description || '—')}</td>
                <td>${t.created_at ? String(t.created_at).replace('T', ' ').slice(0, 19) : '—'}</td>
            </tr>
        `;
    }).join("");
}

async function toggleUserActive(userId, willActive) {
    const actionText = willActive ? "mở khóa" : "khóa";
    if (!confirm(`Bạn có chắc muốn ${actionText} tài khoản này?`)) return;

    const token = getAdminToken();
    try {
        const res = await fetch(`/api/users/admin/${userId}/status`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ active: willActive })
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.message || `Lỗi ${actionText} tài khoản`);

        showUserToast(`Đã ${actionText} tài khoản thành công!`);
        await loadAdminUsers(false);
        showUserListView();
    } catch (e) {
        showUserToast(e.message);
    }
}

window.goToUserPage = goToUserPage;
window.openUserDetail = openUserDetail;
window.toggleUserActive = toggleUserActive;