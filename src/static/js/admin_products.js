let adminProducts = [];
let editingProduct = null;
let searchDebounceTimer = null;
let currentFetchController = null;

let allSystemTags = [];
let currentSelectedTags = [];
let currentProductImageBase64 = "";

let currentPreorderId = null;
let currentPreorderObject = null;
let progressGalleryImages = [];

const productListView = document.getElementById("product-list-view");
const productFormView = document.getElementById("product-form-view");
const listControlPanel = document.getElementById("product-list-control-panel");
const formControlPanel = document.getElementById("product-form-control-panel");
const form = document.getElementById("admin-product-form");
const productTable = document.getElementById("admin-product-table");
const productTableBody = document.getElementById("admin-product-table-body");
const loadingState = document.getElementById("admin-product-loading");
const emptyState = document.getElementById("admin-product-empty");

const fileInput = document.getElementById("product-file-input");
const imagePreviewBox = document.getElementById("product-image-preview-box");

// Elements Pre-order
const productStatusSelect = document.getElementById("product-status");
const tabBtnPreorderProgress = document.getElementById("tab-btn-preorder-progress");
const tabBtnPreorderCustomers = document.getElementById("tab-btn-preorder-customers");
const galleryInput = document.getElementById("progress-gallery-input");
const galleryAddBtn = document.getElementById("gallery-add-btn");
const galleryContainer = document.getElementById("preorder-progress-gallery");
const btnSubmitProgress = document.getElementById("btn-submit-progress");

function getAdminToken() {
    return localStorage.getItem("access_token")
        || localStorage.getItem("token")
        || localStorage.getItem("jwt_token")
        || sessionStorage.getItem("access_token")
        || sessionStorage.getItem("token");
}

function formatAdminPrice(val) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);
}

function escapeAdminHTML(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", async () => {
    bindProductEvents();
    bindProductTagEvents();
    bindImageUploadEvents();
    bindPreorderProgressEvents();
    await loadProducts(true);
    await loadCategories();
    await loadAllSystemTags();
});

function bindProductEvents() {
    document.getElementById("create-product-btn").addEventListener("click", openCreateProduct);
    document.getElementById("discard-product-btn").addEventListener("click", showProductList);
    document.getElementById("reload-products-btn").addEventListener("click", () => loadProducts(true));

    const keywordInput = document.getElementById("admin-product-keyword");
    keywordInput.addEventListener("input", () => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            loadProducts(false);
        }, 300);
    });

    document.getElementById("admin-product-status").addEventListener("change", () => loadProducts(false));
    document.getElementById("product-category").addEventListener("change", handleCategoryChange);
    document.getElementById("product-sub-category").addEventListener("change", handleSubCategoryChange);

    productStatusSelect.addEventListener("change", togglePreorderTabsByStatus);
    form.addEventListener("submit", saveProduct);

    document.querySelectorAll(".product-tab").forEach(button => {
        button.addEventListener("click", () => {
            switchProductTab(button.dataset.productTab);
        });
    });
}

function togglePreorderTabsByStatus() {
    const isPreorder = productStatusSelect.value === "PREORDER";
    tabBtnPreorderProgress.style.display = isPreorder ? "inline-block" : "none";
    tabBtnPreorderCustomers.style.display = isPreorder ? "inline-block" : "none";

    if (!isPreorder) {
        const activeTab = document.querySelector(".product-tab.active");
        if (activeTab && (activeTab.dataset.productTab === "preorder-progress" || activeTab.dataset.productTab === "preorder-customers")) {
            switchProductTab("general");
        }
    }
}

// 1. TẢI THÔNG TIN PREORDER & LỊCH SỬ TIẾN ĐỘ
async function fetchPreorderInfo(productId) {
    const token = getAdminToken();
    try {
        const res = await fetch(`/api/preorders/admin`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        const result = await res.json();
        const preorders = result.data?.preorders || result.preorders || [];

        const found = preorders.find(p => Number(p.product_id) === Number(productId));
        if (found) {
            currentPreorderId = found.preorder_id;
            currentPreorderObject = found;
            if (document.getElementById("progress-status-select") && found.progress_status) {
                document.getElementById("progress-status-select").value = found.progress_status;
            }
            renderProgressHistory(found);
        } else {
            currentPreorderId = null;
            currentPreorderObject = null;
            renderProgressHistory(null);
        }
    } catch (e) {
        console.error("Fetch preorder error:", e);
        currentPreorderId = null;
        renderProgressHistory(null);
    }
}

function renderProgressHistory(preorder) {
    const container = document.getElementById("progress-history-container");
    if (!container) return;

    if (!preorder || !preorder.progress_note) {
        container.innerHTML = `<span style="font-size: 7.5px; color: var(--admin-muted);">Chưa có tiến độ nào được ghi nhận cho đợt đặt trước này. Bạn có thể cập nhật ở form phía trên.</span>`;
        return;
    }

    container.innerHTML = `
        <div class="progress-history-item">
            <div class="progress-history-dot"></div>
            <div class="progress-history-header">
                <strong>${escapeAdminHTML(preorder.progress_status || 'MỞ PREORDER')}</strong>
                <span>${preorder.start_date ? preorder.start_date + ' ~ ' + preorder.end_date : 'Đang diễn ra'}</span>
            </div>
            <div class="progress-history-body">
                ${escapeAdminHTML(preorder.progress_note)}
            </div>
        </div>
    `;
}

// 2. UPLOAD ẢNH TIẾN ĐỘ & GỬI NOTIFICATION (Tự động tạo Preorder nếu chưa có)
function bindPreorderProgressEvents() {
    galleryAddBtn.addEventListener("click", () => {
        if (progressGalleryImages.length >= 10) {
            showProductToast("Chỉ được tải lên tối đa 10 hình ảnh");
            return;
        }
        galleryInput.click();
    });

    galleryInput.addEventListener("change", (e) => {
        const files = Array.from(e.target.files);
        const remainingSlots = 10 - progressGalleryImages.length;
        const filesToProcess = files.slice(0, remainingSlots);

        filesToProcess.forEach(file => {
            const reader = new FileReader();
            reader.onload = (event) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement("canvas");
                    const maxDim = 800;
                    let width = img.width;
                    let height = img.height;
                    if (width > height && width > maxDim) {
                        height *= maxDim / width;
                        width = maxDim;
                    } else if (height > maxDim) {
                        width *= maxDim / height;
                        height = maxDim;
                    }
                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext("2d");
                    ctx.drawImage(img, 0, 0, width, height);

                    progressGalleryImages.push(canvas.toDataURL("image/jpeg", 0.85));
                    renderProgressGallery();
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        });
        galleryInput.value = "";
    });

    btnSubmitProgress.addEventListener("click", submitPreorderProgressAndNotify);
}

function renderProgressGallery() {
    const existingThumbs = galleryContainer.querySelectorAll(".gallery-thumb-item");
    existingThumbs.forEach(t => t.remove());

    progressGalleryImages.forEach((src, idx) => {
        const thumb = document.createElement("div");
        thumb.className = "gallery-thumb-item";
        thumb.innerHTML = `
            <img src="${src}" alt="Ảnh tiến độ ${idx + 1}">
            <button type="button" class="gallery-remove-btn" onclick="removeProgressImage(${idx})">&times;</button>
        `;
        galleryContainer.insertBefore(thumb, galleryAddBtn);
    });

    galleryAddBtn.style.display = progressGalleryImages.length >= 10 ? "none" : "flex";
}

function removeProgressImage(idx) {
    progressGalleryImages.splice(idx, 1);
    renderProgressGallery();
}

async function submitPreorderProgressAndNotify() {
    const productId = document.getElementById("edit-product-id").value;
    const progressStatus = document.getElementById("progress-status-select").value;
    const title = document.getElementById("progress-title").value.trim();
    const content = document.getElementById("progress-content").value.trim();
    const token = getAdminToken();

    if (!productId) {
        showProductToast("Vui lòng lưu sản phẩm trước khi cập nhật tiến độ");
        return;
    }

    if (!title || !content) {
        showProductToast("Vui lòng nhập đầy đủ tiêu đề và nội dung tiến độ");
        return;
    }

    try {
        if (!currentPreorderId) {
            const today = new Date().toISOString().split("T")[0];
            const nextYear = new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString().split("T")[0];

            const createRes = await fetch(`/api/preorders/admin`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    product_id: Number(productId),
                    start_date: today,
                    end_date: nextYear,
                    progress_note: `${title}: ${content}`
                })
            });
            const createData = await createRes.json();
            if (createRes.ok && createData.data?.preorder) {
                currentPreorderId = createData.data.preorder.preorder_id;
            }
        } else {
            await fetch(`/api/preorders/admin/${currentPreorderId}/progress`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    progress_status: progressStatus,
                    progress_note: `${title}: ${content}`
                })
            });
        }

        if (currentPreorderId) {
            await fetch(`/api/notifications/admin/preorders/${currentPreorderId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    title: title,
                    message: content
                })
            });
        }

        showProductToast("Đã cập nhật tiến độ và gửi thông báo thành công!");
        document.getElementById("progress-title").value = "";
        document.getElementById("progress-content").value = "";
        progressGalleryImages = [];
        renderProgressGallery();

        await fetchPreorderInfo(productId);
    } catch (e) {
        showProductToast(e.message || "Lỗi cập nhật tiến độ");
    }
}

async function loadPreorderCustomers(productId) {
    const tbody = document.getElementById("preorder-customers-body");
    const token = getAdminToken();
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--admin-muted); padding: 18px;">Đang tải danh sách khách hàng...</td></tr>`;

    try {
        const res = await fetch(`/api/orders/admin/product/${productId}/preorder-customers`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        const result = await res.json();
        const customers = result.data?.customers || [];

        if (!customers.length) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--admin-muted); padding: 18px;">Chưa có khách hàng nào đặt trước sản phẩm này trong hệ thống.</td></tr>`;
            return;
        }

        tbody.innerHTML = customers.map(o => `
            <tr>
                <td><strong>#${o.order_id}</strong></td>
                <td><strong>${escapeAdminHTML(o.username)}</strong></td>
                <td>${o.quantity}</td>
                <td style="color: var(--admin-gold); font-weight: 600;">${formatAdminPrice(o.subtotal || o.price * o.quantity)}</td>
                <td><span class="admin-product-status preorder">${o.order_status}</span></td>
                <td>${o.created_at ? String(o.created_at).split('T')[0] : '—'}</td>
            </tr>
        `).join("");
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--admin-muted); padding: 18px;">Chưa có dữ liệu đặt trước.</td></tr>`;
    }
}

// 4. MỞ TRANG CHI TIẾT SẢN PHẨM (Đảm bảo nhấp đúp luôn mở form)
async function openEditProduct(productId) {
    const product = adminProducts.find(item => Number(item.product_id) === Number(productId));
    if (!product) return;

    editingProduct = product;
    document.getElementById("edit-product-id").value = product.product_id;
    document.getElementById("product-form-mode").textContent = `Sản phẩm #${product.product_id}`;
    document.getElementById("product-breadcrumb-current").textContent = product.product_name;

    document.getElementById("product-name").value = product.product_name || "";
    document.getElementById("product-price").value = product.price || "";
    document.getElementById("product-description").value = product.description || "";
    document.getElementById("product-status").value = product.status || "IN_STOCK";

    currentProductImageBase64 = product.image || "";
    renderImagePreview(currentProductImageBase64);
    fileInput.value = "";

    currentSelectedTags = (product.tags || []).map(t => ({
        tag_id: t.tag_id || t,
        name: t.name || String(t)
    }));
    renderProductTags();

    progressGalleryImages = [];
    renderProgressGallery();

    resetFormDependencies();
    togglePreorderTabsByStatus();

    switchProductTab("general");
    showProductForm();

    fillProductCategorySafe(product);

    if (product.status === "PREORDER") {
        fetchPreorderInfo(product.product_id);
        loadPreorderCustomers(product.product_id);
    }
}

async function fillProductCategorySafe(product) {
    try {
        const currentTags = product.tags || [];
        if (!currentTags.length) return;

        const firstTag = currentTags[0];
        const tagObj = allSystemTags.find(t => Number(t.tag_id) === Number(firstTag.tag_id || firstTag));
        if (!tagObj || !tagObj.sub_category_id) return;

        const subCategoryId = tagObj.sub_category_id;
        const categoryId = await findCategoryBySubCategory(subCategoryId);
        if (!categoryId) return;

        document.getElementById("product-category").value = categoryId;
        await loadSubCategories(categoryId);
        document.getElementById("product-sub-category").value = subCategoryId;
    } catch (e) {
        console.error("Lỗi gán danh mục sản phẩm:", e);
    }
}

function bindImageUploadEvents() {
    imagePreviewBox.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement("canvas");
                const maxDim = 800;
                let width = img.width;
                let height = img.height;

                if (width > height && width > maxDim) {
                    height *= maxDim / width;
                    width = maxDim;
                } else if (height > maxDim) {
                    width *= maxDim / height;
                    height = maxDim;
                }

                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0, width, height);

                currentProductImageBase64 = canvas.toDataURL("image/jpeg", 0.85);
                renderImagePreview(currentProductImageBase64);
            };
            img.src = event.target.result;
        };
        reader.readAsDataURL(file);
    });
}

function renderImagePreview(src) {
    if (src) {
        imagePreviewBox.innerHTML = `
            <img src="${src}" alt="Ảnh sản phẩm">
            <div class="uploader-hover-overlay">
                <i class='bx bx-refresh' style="font-size: 24px; color: #fff;"></i>
                <span>Bấm để đổi ảnh</span>
            </div>
        `;
    } else {
        imagePreviewBox.innerHTML = `
            <i class='bx bx-cloud-upload'></i>
            <span>Bấm để tải ảnh lên</span>
        `;
    }
}

function bindProductTagEvents() {
    const tagInput = document.getElementById("product-tag-input");
    tagInput.addEventListener("keydown", async (e) => {
        if (e.key === "Enter" || e.key === "+") {
            e.preventDefault();
            const val = tagInput.value.trim().replace(/^\+/, '');
            if (!val) return;

            let existing = allSystemTags.find(t => t.name.trim().toLowerCase() === val.toLowerCase());
            if (!existing) {
                existing = await createQuickTag(val);
            }

            if (existing && !currentSelectedTags.some(t => t.name.trim().toLowerCase() === existing.name.trim().toLowerCase())) {
                currentSelectedTags.push(existing);
                renderProductTags();
            }
            tagInput.value = "";
        }
    });
}

async function createQuickTag(tagName) {
    const subCategoryId = document.getElementById("product-sub-category").value;
    const token = getAdminToken();

    try {
        const res = await fetch("/api/products/tags", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({
                name: tagName,
                sub_category_id: subCategoryId ? Number(subCategoryId) : null
            })
        });
        const result = await res.json();
        const newTag = result.data?.tag || { tag_id: Date.now(), name: tagName };

        if (!allSystemTags.some(t => t.name.trim().toLowerCase() === newTag.name.trim().toLowerCase())) {
            allSystemTags.push(newTag);
        }
        renderAvailableTags();
        return newTag;
    } catch (e) {
        const localTag = { tag_id: Date.now(), name: tagName };
        allSystemTags.push(localTag);
        renderAvailableTags();
        return localTag;
    }
}

function renderProductTags() {
    const container = document.getElementById("selected-tags-list");
    container.innerHTML = currentSelectedTags.map(tag => `
        <span class="verdia-tag-item">
            ${escapeAdminHTML(tag.name)}
            <i class='bx bx-x' onclick="removeSelectedTag(${tag.tag_id})"></i>
        </span>
    `).join("");
}

function removeSelectedTag(tagId) {
    currentSelectedTags = currentSelectedTags.filter(t => Number(t.tag_id) !== Number(tagId));
    renderProductTags();
}

function renderAvailableTags() {
    const list = document.getElementById("available-tags-list");
    const uniqueTagsMap = new Map();
    allSystemTags.forEach(tag => {
        const normalized = String(tag.name || "").trim().toLowerCase();
        if (normalized && !uniqueTagsMap.has(normalized)) {
            uniqueTagsMap.set(normalized, tag);
        }
    });

    const uniqueTags = Array.from(uniqueTagsMap.values());

    if (!uniqueTags.length) {
        list.innerHTML = `<span style="font-size: 7.5px; color: var(--admin-muted);">Chưa có thẻ</span>`;
        return;
    }

    list.innerHTML = uniqueTags.map(tag => `
        <span class="available-tag-pill" onclick="selectAvailableTag(${tag.tag_id}, '${escapeAdminHTML(tag.name)}')">
            <i class='bx bx-plus'></i> ${escapeAdminHTML(tag.name)}
        </span>
    `).join("");
}

function selectAvailableTag(tagId, tagName) {
    if (!currentSelectedTags.some(t => t.name.trim().toLowerCase() === tagName.trim().toLowerCase())) {
        currentSelectedTags.push({ tag_id: tagId, name: tagName });
        renderProductTags();
    }
}

async function loadAllSystemTags() {
    try {
        const res = await fetch("/api/products/tags");
        const result = await res.json();
        const rawTags = result.data?.tags || result.tags || [];

        const map = new Map();
        rawTags.forEach(t => {
            const k = String(t.name || "").trim().toLowerCase();
            if (k && !map.has(k)) map.set(k, t);
        });
        allSystemTags = Array.from(map.values());
        renderAvailableTags();
    } catch (e) {
        console.error("Load tags error:", e);
    }
}

function showProductList() {
    productFormView.style.display = "none";
    productListView.style.display = "block";
    formControlPanel.style.display = "none";
    listControlPanel.style.display = "flex";
    document.getElementById("product-breadcrumb-current").textContent = "Danh sách";
    editingProduct = null;
}

function showProductForm() {
    productListView.style.display = "none";
    productFormView.style.display = "block";
    listControlPanel.style.display = "none";
    formControlPanel.style.display = "flex";
}

async function loadProducts(showInitialSpinner = false) {
    if (currentFetchController) currentFetchController.abort();
    currentFetchController = new AbortController();

    const keyword = document.getElementById("admin-product-keyword").value.trim();
    const statusFilter = document.getElementById("admin-product-status").value;

    const params = new URLSearchParams();
    if (keyword) params.set("keyword", keyword);
    if (statusFilter && statusFilter !== "INACTIVE") params.set("status", statusFilter);

    if (showInitialSpinner) {
        loadingState.style.display = "flex";
        emptyState.style.display = "none";
        productTable.style.display = "none";
    }

    const token = getAdminToken();
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    try {
        const response = await fetch(`/api/products?${params.toString()}`, {
            headers,
            credentials: "include",
            signal: currentFetchController.signal
        });
        const result = await response.json();

        if (!response.ok) throw new Error(result.message || "Không thể tải sản phẩm");

        let rawProducts = result.data?.products
            || result.products
            || (Array.isArray(result.data) ? result.data : [])
            || (Array.isArray(result) ? result : []);

        if (statusFilter === "INACTIVE") {
            rawProducts = rawProducts.filter(p => p.active === false || p.active === 0);
        }

        adminProducts = rawProducts.sort((a, b) => {
            const aActive = a.active !== false && a.active !== 0 ? 1 : 0;
            const bActive = b.active !== false && b.active !== 0 ? 1 : 0;
            return bActive - aActive;
        });

        renderProducts();
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error("Load products error:", error);
        showProductToast(error.message);
        adminProducts = [];
        renderProducts();
    } finally {
        if (showInitialSpinner) loadingState.style.display = "none";
    }
}

function renderProducts() {
    const tableCountElement = document.getElementById("admin-table-product-count");
    if (tableCountElement) {
        tableCountElement.textContent = `(${adminProducts.length})`;
    }

    if (!adminProducts.length) {
        emptyState.style.display = "flex";
        productTable.style.display = "none";
        return;
    }

    emptyState.style.display = "none";
    productTable.style.display = "table";
    productTableBody.innerHTML = adminProducts.map(product => createProductRow(product)).join("");
}

function createProductRow(product) {
    const tags = (product.tags || []).map(tag => escapeAdminHTML(tag.name || tag)).join(", ");
    const isPreorder = String(product.status).toUpperCase() === "PREORDER";
    const statusClass = isPreorder ? "preorder" : "instock";
    const statusText = isPreorder ? "PRE-ORDER" : "CÓ SẴN";
    const isActive = product.active !== false && product.active !== 0;

    return `
        <tr class="${isActive ? '' : 'product-inactive'}" 
            onclick="openEditProduct(${product.product_id})">
            <td>
                <div class="admin-product-cell">
                    <div class="admin-product-thumb">
                        ${product.image ? `
                            <img src="${product.image}" alt="${escapeAdminHTML(product.product_name)}">
                        ` : `
                            <i class='bx bx-image'></i>
                        `}
                    </div>
                    <div class="admin-product-name">
                        <strong>${escapeAdminHTML(product.product_name)}</strong>
                        <span>ID #${product.product_id}</span>
                    </div>
                </div>
            </td>
            <td>${formatAdminPrice(product.price)}</td>
            <td>
                <span class="admin-product-status ${statusClass}">
                    ${statusText}
                </span>
            </td>
            <td>${tags || "—"}</td>
            <td>
                <span class="admin-product-active ${isActive ? '' : 'inactive'}">
                    ${isActive ? 'Hoạt động' : 'Ngừng kinh doanh'}
                </span>
            </td>
            <td>
                <div class="admin-row-actions" onclick="event.stopPropagation()">
                    ${isActive ? `
                        <button type="button" class="admin-product-action delete" title="Ngừng kinh doanh" onclick="toggleProductStatus(${product.product_id}, false)">
                            <i class='bx bx-trash'></i>
                        </button>
                    ` : `
                        <button type="button" class="admin-product-action restore" title="Mở bán lại" onclick="toggleProductStatus(${product.product_id}, true)">
                            <i class='bx bx-undo'></i>
                        </button>
                    `}
                </div>
            </td>
        </tr>
    `;
}

function openCreateProduct() {
    editingProduct = null;
    currentPreorderId = null;
    currentPreorderObject = null;
    form.reset();
    document.getElementById("edit-product-id").value = "";
    document.getElementById("product-form-mode").textContent = "Sản phẩm mới";
    document.getElementById("product-breadcrumb-current").textContent = "Mới";

    currentProductImageBase64 = "";
    renderImagePreview("");
    fileInput.value = "";

    currentSelectedTags = [];
    renderProductTags();

    progressGalleryImages = [];
    renderProgressGallery();
    renderProgressHistory(null);

    resetFormDependencies();
    togglePreorderTabsByStatus();
    switchProductTab("general");
    showProductForm();
}

async function saveProduct(event) {
    event.preventDefault();
    const token = getAdminToken();
    const productId = document.getElementById("edit-product-id").value;

    const data = {
        product_name: document.getElementById("product-name").value.trim(),
        price: Number(document.getElementById("product-price").value),
        description: document.getElementById("product-description").value.trim(),
        image: currentProductImageBase64 || "",
        status: document.getElementById("product-status").value,
        tag_ids: currentSelectedTags.map(t => Number(t.tag_id))
    };

    const editing = Boolean(productId);
    const url = editing ? `/api/products/admin/${productId}` : "/api/products/admin";
    const method = editing ? "PUT" : "POST";

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.message || "Không thể lưu sản phẩm");

        showProductToast(editing ? "Cập nhật sản phẩm thành công" : "Tạo sản phẩm thành công");
        await loadProducts(false);
        showProductList();
    } catch (error) {
        showProductToast(error.message);
    }
}

async function toggleProductStatus(productId, isRestoring) {
    const token = getAdminToken();
    const actionText = isRestoring ? "mở bán lại" : "ngừng kinh doanh";

    if (!confirm(`Bạn có chắc muốn ${actionText} sản phẩm này?`)) return;

    try {
        let response;
        if (!isRestoring) {
            response = await fetch(`/api/products/admin/${productId}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            });
        } else {
            response = await fetch(`/api/products/admin/${productId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ active: true })
            });
        }

        const result = await response.json();
        if (!response.ok) throw new Error(result.message || `Không thể ${actionText} sản phẩm`);

        showProductToast(`Đã ${actionText} sản phẩm`);
        await loadProducts(false);
    } catch (error) {
        showProductToast(error.message);
    }
}

async function loadCategories() {
    const select = document.getElementById("product-category");
    try {
        const response = await fetch("/api/products/categories");
        const result = await response.json();
        const categories = result.data?.categories || result.categories || [];

        select.innerHTML = `<option value="">Chọn danh mục</option>`;
        categories.forEach(category => {
            const option = document.createElement("option");
            option.value = category.category_id;
            option.textContent = category.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("LOAD CATEGORY ERROR:", error);
    }
}

async function handleCategoryChange() {
    const categoryId = this.value;
    resetSubCategory();
    if (!categoryId) return;
    await loadSubCategories(categoryId);
}

async function loadSubCategories(categoryId) {
    const select = document.getElementById("product-sub-category");
    try {
        const response = await fetch(`/api/products/categories/${categoryId}/sub-categories`);
        const result = await response.json();
        if (!response.ok) throw new Error(result.message || "Không thể tải danh mục phụ");

        const subCategories = result.data?.sub_categories || result.sub_categories || [];
        select.disabled = false;
        select.innerHTML = `<option value="">Chọn danh mục phụ</option>`;

        subCategories.forEach(item => {
            const option = document.createElement("option");
            option.value = item.sub_category_id;
            option.textContent = item.name;
            select.appendChild(option);
        });
    } catch (error) {
        showProductToast(error.message);
    }
}

function handleSubCategoryChange() { }

async function findCategoryBySubCategory(subCategoryId) {
    const categorySelect = document.getElementById("product-category");
    const categoryIds = [...categorySelect.options].map(option => Number(option.value)).filter(Boolean);

    for (const categoryId of categoryIds) {
        try {
            const response = await fetch(`/api/products/categories/${categoryId}/sub-categories`);
            if (!response.ok) continue;
            const result = await response.json();
            const subCategories = result.data?.sub_categories || result.sub_categories || [];

            if (subCategories.some(item => Number(item.sub_category_id) === Number(subCategoryId))) {
                return categoryId;
            }
        } catch (e) {
            continue;
        }
    }
    return null;
}

function resetFormDependencies() {
    document.getElementById("product-category").value = "";
    resetSubCategory();
}

function resetSubCategory() {
    const select = document.getElementById("product-sub-category");
    select.disabled = true;
    select.innerHTML = `<option value="">Chọn danh mục phụ</option>`;
}

function switchProductTab(tab) {
    document.querySelectorAll(".product-tab").forEach(button => {
        button.classList.toggle("active", button.dataset.productTab === tab);
    });
    document.querySelectorAll(".product-tab-content").forEach(content => {
        content.classList.toggle("active", content.dataset.productContent === tab);
    });
}

function showProductToast(message) {
    const toast = document.getElementById("admin-product-toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toast.hideTimer);
    toast.hideTimer = setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
}