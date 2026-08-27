const menuItems =
    document.querySelectorAll(
        ".profile-menu-item:not(.logout-btn)"
    );

const tabs =
    document.querySelectorAll(
        ".profile-tab"
    );


const editProfileBtn =
    document.getElementById(
        "edit-profile-btn"
    );

const cancelEditBtn =
    document.getElementById(
        "cancel-edit-btn"
    );

const profileForm =
    document.getElementById(
        "profile-form"
    );

const profileFormActions =
    document.getElementById(
        "profile-form-actions"
    );


const usernameInput =
    document.getElementById(
        "profile-username"
    );

const emailInput =
    document.getElementById(
        "profile-email"
    );

const fullNameInput =
    document.getElementById(
        "profile-full-name"
    );

const phoneInput =
    document.getElementById(
        "profile-phone"
    );

const addressInput =
    document.getElementById(
        "profile-address"
    );

const avatarInput =
    document.getElementById(
        "profile-avatar"
    );


const sidebarUsername =
    document.getElementById(
        "sidebar-username"
    );

const sidebarEmail =
    document.getElementById(
        "sidebar-email"
    );

const sidebarAvatar =
    document.getElementById(
        "sidebar-avatar"
    );

const overviewUsername =
    document.getElementById(
        "overview-username"
    );

const overviewOrders =
    document.getElementById(
        "overview-orders"
    );

const recentOrders =
    document.getElementById(
        "recent-orders"
    );

const orderList =
    document.getElementById(
        "order-list"
    );

const preorderOrderList =
    document.getElementById(
        "preorder-order-list"
    );


let allOrders = [];

const overviewWallet =
    document.getElementById(
        "overview-wallet"
    );

const walletBalance =
    document.getElementById(
        "wallet-balance"
    );

const walletHistory =
    document.getElementById(
        "wallet-history"
    );

const depositWalletBtn =
    document.getElementById(
        "deposit-wallet-btn"
    );

const withdrawWalletBtn =
    document.getElementById(
        "withdraw-wallet-btn"
    );


let currentWallet = null;

let walletTransactions = [];


const toast =
    document.getElementById(
        "profile-toast"
    );


const logoutBtn =
    document.getElementById(
        "logout-btn"
    );


if (logoutBtn) {

    logoutBtn.addEventListener(
        "click",
        () => {

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "refresh_token"
            );

            localStorage.removeItem(
                "user"
            );


            window.location.href =
                "/login";

        }
    );

}


let currentUser = null;

let originalProfile = null;
 
function getToken() {

    return localStorage.getItem(
        "access_token"
    );

}
 
function openTab(tabName) {

    tabs.forEach(tab => {

        tab.classList.remove(
            "active"
        );

    });


    menuItems.forEach(item => {

        item.classList.remove(
            "active"
        );

    });


    const tab =
        document.getElementById(
            tabName
        );


    if (tab) {

        tab.classList.add(
            "active"
        );

    }


    const menu =
        document.querySelector(
            `[data-tab="${tabName}"]`
        );


    if (menu) {

        menu.classList.add(
            "active"
        );

    }

}


menuItems.forEach(item => {

    item.addEventListener(
        "click",
        () => {

            openTab(
                item.dataset.tab
            );

        }
    );

});


document.querySelectorAll(
    "[data-open-tab]"
).forEach(button => {

    button.addEventListener(
        "click",
        () => {

            openTab(
                button.dataset.openTab
            );

        }
    );

});
 
function showToast(message) {

    toast.textContent =
        message;


    toast.classList.add(
        "show"
    );


    setTimeout(() => {

        toast.classList.remove(
            "show"
        );

    }, 2500);

}
 
async function loadProfile() {

    const token =
        getToken();


    if (!token) {

        localStorage.setItem(
            "redirect_after_login",
            "/profile"
        );


        window.location.href =
            "/login";

        return;

    }


    try {

        const response =
            await fetch(
                "/api/users/me",
                {
                    headers: {

                        Authorization:
                            `Bearer ${token}`

                    }
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.message ||
                "Không thể tải tài khoản"
            );

        }


        currentUser =
            result.data ||
            result;


        fillProfile(
            currentUser
        );


    } catch (error) {

        console.error(
            error
        );


        showToast(
            "Không thể tải thông tin tài khoản"
        );

    }

}
 
async function loadOrders() {

    const token =
        getToken();


    try {

        const response =
            await fetch(
                "/api/orders/my-orders",
                {
                    headers: {

                        Authorization:
                            `Bearer ${token}`

                    }
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.message ||
                "Không thể tải đơn hàng"
            );

        }


        allOrders =
            result.data?.orders || [];


        overviewOrders.textContent =
            allOrders.length;


        renderRecentOrders();


        renderOrders(
            getShippingOrders()
        );

        renderPreorderOrders(
            getPreorderItems()
        );


    } catch (error) {

        console.error(
            "LOAD ORDERS ERROR:",
            error
        );

    }

}

document.querySelectorAll(
    "[data-preorder-status]"
).forEach(button => {

    button.addEventListener(
        "click",
        () => {

            document
                .querySelectorAll(
                    "[data-preorder-status]"
                )
                .forEach(item => {

                    item.classList.remove(
                        "active"
                    );

                });


            button.classList.add(
                "active"
            );


            const status =
                button.dataset.preorderStatus;


            const items =
                getPreorderItems();


            if (
                status === "ALL"
            ) {

                renderPreorderOrders(
                    items
                );


                return;

            }


            const filtered =
                items.filter(
                    item =>
                        getPreorderStage(
                            item
                        )
                        === status
                );


            renderPreorderOrders(
                filtered
            );

        }
    );

});
 
async function loadWallet() {

    const token =
        getToken();


    try {

        const response =
            await fetch(
                "/api/wallets/me",
                {
                    headers: {

                        Authorization:
                            `Bearer ${token}`

                    }
                }
            );


        const result =
            await response.json();


        console.log(
            "WALLET API:",
            result
        );


        if (!response.ok) {

            throw new Error(
                result.message ||
                "Không thể tải Ví Verd"
            );

        }


        const wallet =
            result.data?.wallet
            || result.wallet
            || null;


        if (!wallet) {

            throw new Error(
                "Không tìm thấy dữ liệu Ví Verd"
            );

        }


        currentWallet =
            wallet;


        const balance =
            Number(
                wallet.balance || 0
            );


        console.log(
            "WALLET BALANCE:",
            balance
        );


        overviewWallet.textContent =
            formatPrice(balance);


        walletBalance.textContent =
            formatPrice(balance);


    } catch (error) {

        console.error(
            "LOAD WALLET ERROR:",
            error
        );


        showToast(
            error.message ||
            "Không thể tải Ví Verd"
        );

    }

}

async function loadWalletTransactions() {

    const token =
        getToken();


    try {

        const response =
            await fetch(
                "/api/wallets/me/transactions",
                {
                    headers: {

                        Authorization:
                            `Bearer ${token}`

                    }
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.message ||
                "Không thể tải lịch sử giao dịch"
            );

        }


        walletTransactions =
            result.data?.transactions || [];


        renderWalletTransactions();


    } catch (error) {

        console.error(
            "LOAD WALLET TRANSACTIONS ERROR:",
            error
        );

    }

}

function formatDateTime(value) {

    if (!value) {
        return "";
    }


    const date =
        new Date(value);


    return date.toLocaleString(
        "vi-VN"
    );

}


function getTransactionSign(type) {

    if (
        type === "NẠP TIỀN"
        ||
        type === "HOÀN TIỀN"
    ) {

        return "+";

    }


    return "-";

}


function getTransactionClass(type) {

    if (
        type === "NẠP TIỀN"
        ||
        type === "HOÀN TIỀN"
    ) {

        return "wallet-in";

    }


    return "wallet-out";

}


function renderWalletTransactions() {

    if (!walletTransactions.length) {

        walletHistory.innerHTML = `
            <div class="profile-empty">

                <i class='bx bx-receipt'></i>

                <p>
                    Chưa có giao dịch
                </p>

            </div>
        `;

        return;

    }


    walletHistory.innerHTML =
        walletTransactions
            .map(transaction => {

                return `
                    <div class="wallet-transaction">

                        <div class="wallet-transaction-icon">

                            <i class='bx bx-transfer'></i>

                        </div>


                        <div class="wallet-transaction-info">

                            <strong>
                                ${transaction.transaction_type}
                            </strong>

                            <span>
                                ${transaction.description || ""}
                            </span>

                            <small>
                                ${formatDateTime(transaction.created_at)}
                            </small>

                        </div>


                        <div class="wallet-transaction-right">

                            <strong
                                class="${getTransactionClass(
                    transaction.transaction_type
                )}"
                            >
                                ${getTransactionSign(
                    transaction.transaction_type
                )}
                                ${formatPrice(transaction.amount)}
                            </strong>

                            <span>
                                ${transaction.transaction_status}
                            </span>

                        </div>

                    </div>
                `;

            })
            .join("");

}

if (depositWalletBtn) {

    depositWalletBtn.addEventListener(
        "click",
        async () => {

            const amount =
                prompt(
                    "Nhập số tiền muốn nạp:"
                );


            if (!amount) {
                return;
            }


            const token =
                getToken();


            try {

                const response =
                    await fetch(
                        "/api/wallets/deposit",
                        {
                            method:
                                "POST",

                            headers: {

                                "Content-Type":
                                    "application/json",

                                Authorization:
                                    `Bearer ${token}`

                            },

                            body:
                                JSON.stringify({
                                    amount:
                                        amount,

                                    description:
                                        "Yêu cầu nạp Ví Verd"
                                })

                        }
                    );


                const result =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        result.message ||
                        "Không thể tạo yêu cầu nạp"
                    );

                }


                showToast(
                    "Đã gửi yêu cầu nạp tiền"
                );


                await loadWalletTransactions();


            } catch (error) {

                showToast(
                    error.message
                );

            }

        }
    );

}

if (withdrawWalletBtn) {

    withdrawWalletBtn.addEventListener(
        "click",
        async () => {

            const amount =
                prompt(
                    "Nhập số tiền muốn rút:"
                );


            if (!amount) {
                return;
            }


            const token =
                getToken();


            try {

                const response =
                    await fetch(
                        "/api/wallets/withdraw",
                        {
                            method:
                                "POST",

                            headers: {

                                "Content-Type":
                                    "application/json",

                                Authorization:
                                    `Bearer ${token}`

                            },

                            body:
                                JSON.stringify({
                                    amount:
                                        amount,

                                    description:
                                        "Yêu cầu rút Ví Verd"
                                })

                        }
                    );


                const result =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        result.message ||
                        "Không thể tạo yêu cầu rút"
                    );

                }


                showToast(
                    "Đã gửi yêu cầu rút tiền"
                );


                await loadWalletTransactions();


            } catch (error) {

                showToast(
                    error.message
                );

            }

        }
    );

}
 
function fillProfile(user) {

    const profile =
        user.profile || {};


    usernameInput.value =
        user.username || "";


    emailInput.value =
        user.email || "";


    fullNameInput.value =
        profile.full_name || "";


    phoneInput.value =
        profile.phone_num || "";


    addressInput.value =
        profile.address || "";


    avatarInput.value =
        profile.avatar || "";


    sidebarUsername.textContent =
        user.username || "Khách hàng";


    sidebarEmail.textContent =
        user.email || "";


    overviewUsername.textContent =
        user.username || "—";


    if (profile.avatar) {

        sidebarAvatar.src =
            profile.avatar;

    }


    originalProfile = {

        full_name:
            profile.full_name || "",

        phone_num:
            profile.phone_num || "",

        address:
            profile.address || "",

        avatar:
            profile.avatar || ""

    };

}
 
function setEditMode(enabled) {

    fullNameInput.disabled =
        !enabled;

    phoneInput.disabled =
        !enabled;

    addressInput.disabled =
        !enabled;

    avatarInput.disabled =
        !enabled;


    profileFormActions.style.display =
        enabled
            ? "flex"
            : "none";


    editProfileBtn.style.display =
        enabled
            ? "none"
            : "inline-flex";

}


editProfileBtn.addEventListener(
    "click",
    () => {

        setEditMode(true);

    }
);
 
cancelEditBtn.addEventListener(
    "click",
    () => {

        if (originalProfile) {

            fullNameInput.value =
                originalProfile.full_name;

            phoneInput.value =
                originalProfile.phone_num;

            addressInput.value =
                originalProfile.address;

            avatarInput.value =
                originalProfile.avatar;

        }


        setEditMode(false);

    }
);
 
profileForm.addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        if (!currentUser) {
            return;
        }


        const token =
            getToken();


        const data = {

            full_name:
                fullNameInput
                    .value
                    .trim(),

            phone_num:
                phoneInput
                    .value
                    .trim(),

            address:
                addressInput
                    .value
                    .trim(),

            avatar:
                avatarInput
                    .value
                    .trim()

        };


        try {

            const response =
                await fetch(
                    `/api/users/${currentUser.user_id}/profile`,
                    {

                        method:
                            "PUT",

                        headers: {

                            "Content-Type":
                                "application/json",

                            Authorization:
                                `Bearer ${token}`

                        },

                        body:
                            JSON.stringify(
                                data
                            )

                    }
                );


            const result =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    result.message ||
                    "Cập nhật thất bại"
                );

            }


            showToast(
                "Cập nhật thông tin thành công"
            );


            setEditMode(false);


            await loadProfile();


        } catch (error) {

            console.error(
                error
            );


            showToast(
                error.message ||
                "Không thể cập nhật thông tin"
            );

        }

    }
);
 
document.querySelectorAll(
    "[data-order-filter]"
).forEach(button => {

    button.addEventListener(
        "click",
        () => {

            document
                .querySelectorAll(
                    "[data-order-filter]"
                )
                .forEach(item => {

                    item.classList.remove(
                        "active"
                    );

                });


            button.classList.add(
                "active"
            );


            const status =
                button.dataset.orderFilter;


            if (
                status === "ALL"
            ) {

                renderOrders(
                    getShippingOrders()
                );

                return;

            }



            if (
                status === "CHỜ XÁC NHẬN"
                ||
                status === "ĐANG XỬ LÝ"
            ) {

                const filtered =
                    getShippingOrders()
                        .filter(
                            order =>
                                order.order_status
                                === status
                        );


                renderOrders(
                    filtered
                );

                return;

            }



            const shippingOrders =
                getShippingOrders()
                    .filter(
                        order =>
                            getOrderShippingStatus(
                                order
                            )
                            === status
                    );


            renderOrders(
                shippingOrders
            );

        }
    );

});

function getPreorderItems() {

    const preorderItems =
        [];


    allOrders.forEach(order => {

        const items =
            getOrderItems(
                order
            );


        items.forEach(item => {

            if (
                item.preorder_id
                ||
                item.preorder
            ) {

                preorderItems.push({

                    ...item,

                    order_id:
                        order.order_id,

                    order_date:
                        order.order_date,

                    order_status:
                        order.order_status

                });

            }

        });

    });


    return preorderItems;
}
 
function getShippingOrders() {

    return allOrders.filter(
        order => {

            const items =
                getOrderItems(
                    order
                );
 
            if (
                !items.length
            ) {
                return true;
            }


            const preorderItems =
                items.filter(
                    item =>
                        item.preorder_id
                        ||
                        item.preorder
                );
 
            if (
                preorderItems.length === 0
            ) {
                return true;
            }
 
            return preorderItems.every(
                item =>
                    getPreorderProgress(
                        item
                    )
                    === "HOÀN THÀNH"
            );

        }
    );

}

function getPreorderProgress(
    item
) {

    return (
        item.preorder?.progress_status
        ||
        item.preorder_progress_status
        ||
        "ĐANG CẬP NHẬT"
    );

}

function getPreorderProgress(
    item
) {

    return (
        item.preorder?.progress_status
        ||
        item.preorder_progress_status
        ||
        "ĐANG CẬP NHẬT"
    );

}
 
function getPreorderStage(item) {

    const progress =
        getPreorderProgress(
            item
        );
     if (
        progress === "MỞ PREORDER"
        ||
        progress === "ĐÃ ĐẶT HÀNG"
    ) {

        return "PREORDER";

    }
     if (
        progress === "ĐANG SẢN XUẤT"
    ) {

        return "PRODUCTION";

    }
     if (
        progress === "ĐÃ VỀ KHO TRUNG QUỐC"
        ||
        progress === "ĐÃ VỀ KHO VIỆT NAM"
    ) {

        return "IN_TRANSIT";

    }
     if (
        progress === "ĐANG GÓI HÀNG"
        ||
        progress === "ĐÃ VẬN CHUYỂN"
        ||
        progress === "HOÀN THÀNH"
    ) {

        return "COMPLETED";

    }


    return "";

}
 
function getPreorderDisplayStatus(item) {

    const stage =
        getPreorderStage(
            item
        );


    if (
        stage === "PREORDER"
    ) {

        return "PRE-ORDER";

    }


    if (
        stage === "PRODUCTION"
    ) {

        return "SẢN XUẤT";

    }


    if (
        stage === "IN_TRANSIT"
    ) {

        return "ĐANG VỀ";

    }


    if (
        stage === "COMPLETED"
    ) {

        return "HOÀN THÀNH";

    }


    return "ĐANG CẬP NHẬT";

}

function createPreorderOrderHTML(
    item
) {

    const image =
        getOrderItemImage(
            item
        );


    const productName =
        getOrderItemName(
            item
        );


    const progress =
        getPreorderDisplayStatus(
            item
        );


    return `
        <article class="preorder-order-card">

            <div class="preorder-order-top">

                <div>

                    <strong>
                        Đơn #${item.order_id}
                    </strong>

                    <span>
                        ${item.order_date || ""}
                    </span>

                </div>


                <span class="preorder-progress-badge">
                    ${progress}
                </span>

            </div>


            <div class="preorder-order-product">

                <div class="preorder-order-image">

                    ${image
            ? `
                                <img
                                    src="${image}"
                                    alt="${productName}"
                                >
                            `
            : `
                                <div class="order-product-placeholder">

                                    <i class='bx bx-image'></i>

                                </div>
                            `
        }

                </div>


                <div class="preorder-order-info">

                    <strong>
                        ${productName}
                    </strong>


                    <span>
                        Số lượng:
                        ${item.quantity || 1}
                    </span>


                    <span>
                        Giá:
                        ${formatPrice(
            item.price
        )}
                    </span>

                </div>

            </div>


            <div class="preorder-progress-row">

                <i class='bx bx-time-five'></i>

                <div>

                    <span>
                        Tiến độ hiện tại
                    </span>

                    <strong>
                        ${progress}
                    </strong>

                </div>

            </div>


            <div class="preorder-order-bottom">

                <a
                    href="/orders/${item.order_id}"
                    class="order-detail-btn"
                >
                    Xem chi tiết
                </a>

            </div>

        </article>
    `;
}

function renderPreorderOrders(
    items
) {

    if (
        !preorderOrderList
    ) {
        return;
    }


    if (
        !items.length
    ) {

        preorderOrderList.innerHTML = `
            <div class="profile-empty">

                <i class='bx bx-time-five'></i>

                <p>
                    Không có đơn hàng Pre-order
                </p>

            </div>
        `;


        return;

    }


    preorderOrderList.innerHTML =
        items
            .map(
                createPreorderOrderHTML
            )
            .join("");

}
 
function formatPrice(price) {

    return Number(
        price || 0
    ).toLocaleString(
        "vi-VN"
    ) + "đ";

}
 
function getOrderStatusClass(status) {

    if (
        status === "HOÀN THÀNH"
    ) {
        return "completed";
    }


    if (
        status === "CHỜ XÁC NHẬN"
    ) {
        return "waiting";
    }


    if (
        status === "ĐÃ ĐẶT CỌC"
    ) {
        return "deposit";
    }


    return "processing";

}
 
function getOrderItems(order) {

    return (
        order.order_items
        ||
        order.items
        ||
        []
    );

}
 
function getOrderShippingStatus(order) {

    const items =
        getOrderItems(
            order
        );


    if (
        !items.length
    ) {

        if (
            order.order_status
            === "HOÀN THÀNH"
        ) {
            return "ĐÃ GIAO";
        }


        return "CHƯA GIAO";
    }


    const statuses =
        items
            .map(
                item =>
                    item.shipping_status
            )
            .filter(Boolean);


    if (
        !statuses.length
    ) {

        if (
            order.order_status
            === "HOÀN THÀNH"
        ) {
            return "ĐÃ GIAO";
        }


        return "CHƯA GIAO";
    }


    if (
        statuses.includes(
            "ĐANG GIAO HÀNG"
        )
    ) {
        return "ĐANG GIAO HÀNG";
    }


    if (
        statuses.includes(
            "ĐANG LẤY HÀNG"
        )
    ) {
        return "ĐANG LẤY HÀNG";
    }


    if (
        statuses.every(
            status =>
                status === "ĐÃ GIAO"
        )
    ) {
        return "ĐÃ GIAO";
    }


    return statuses[0];

}
 
function getShippingStatusClass(status) {

    if (
        status === "ĐÃ GIAO"
    ) {
        return "shipping-completed";
    }


    if (
        status === "ĐANG GIAO HÀNG"
    ) {
        return "shipping-delivering";
    }


    if (
        status === "ĐANG LẤY HÀNG"
    ) {
        return "shipping-pickup";
    }


    return "shipping-waiting";

}
 
function getTrackingCode(order) {

    const items =
        getOrderItems(
            order
        );


    const item =
        items.find(
            item =>
                item.tracking_code
        );


    return item?.tracking_code
        || order.tracking_code
        || "";

}
 
function getOrderItemImage(item) {

    return (
        item.product?.image
        ||
        item.image
        ||
        ""
    );

}
 
function getOrderItemName(item) {

    return (
        item.product?.product_name
        ||
        item.product_name
        ||
        "Sản phẩm"
    );

}
 
function getOrderItemType(item) {

    const status =
        item.product?.status
        ||
        item.product_status
        ||
        "";


    if (
        status === "PREORDER"
        ||
        item.preorder_id
    ) {
        return "Pre-order";
    }


    if (
        status === "IN_STOCK"
    ) {
        return "Có sẵn";
    }


    return "";

}
 
function createOrderProductHTML(item) {

    const image =
        getOrderItemImage(
            item
        );


    const productName =
        getOrderItemName(
            item
        );


    const productType =
        getOrderItemType(
            item
        );


    const quantity =
        Number(
            item.quantity || 1
        );


    const price =
        Number(
            item.price || 0
        );


    return `
        <div class="shopee-order-product">

            <div class="shopee-order-product-image">

                ${image
            ? `
                            <img
                                src="${image}"
                                alt="${productName}"
                            >
                        `
            : `
                            <div class="order-product-placeholder">
                                <i class='bx bx-image'></i>
                            </div>
                        `
        }

            </div>


            <div class="shopee-order-product-info">

                <strong>
                    ${productName}
                </strong>


                ${productType
            ? `
                            <span>
                                Phân loại:
                                ${productType}
                            </span>
                        `
            : ""
        }


                <span>
                    x${quantity}
                </span>

            </div>


            <div class="shopee-order-product-price">

                ${formatPrice(
            price
        )}

            </div>

        </div>
    `;

}
 
function createOrderHTML(order) {

    const shippingStatus =
        getOrderShippingStatus(
            order
        );


    const trackingCode =
        getTrackingCode(
            order
        );


    const items =
        getOrderItems(
            order
        );


    const productsHTML =
        items.length
            ? items
                .map(
                    createOrderProductHTML
                )
                .join("")
            : `
                <div class="order-no-product">

                    <i class='bx bx-package'></i>

                    <span>
                        Xem chi tiết để xem sản phẩm trong đơn
                    </span>

                </div>
            `;


    return `
        <article class="shopee-order-card">
 
            <div class="shopee-order-top">

                <div class="shopee-order-code">

                    <i class='bx bx-receipt'></i>

                    <strong>
                        VERDIA
                    </strong>

                    <span>
                        Đơn #${order.order_id}
                    </span>

                </div>


                <div class="shopee-order-status-area">

                    <span
                        class="
                            shipping-status
                            ${getShippingStatusClass(
        shippingStatus
    )}
                        "
                    >

                        <i class='bx bx-truck'></i>

                        ${shippingStatus}

                    </span>


                    <span class="status-divider">
                        |
                    </span>


                    <span
                        class="
                            order-status-text
                            ${getOrderStatusClass(
        order.order_status
    )}
                        "
                    >
                        ${order.order_status}
                    </span>

                </div>

            </div>
 
            <div class="shopee-order-products">

                ${productsHTML}

            </div>
 
            ${(
            shippingStatus
            !== "CHƯA GIAO"
            ||
            trackingCode
        )
            ? `
                        <div class="order-shipping-info">

                            <div>

                                <i class='bx bx-map'></i>

                                <span>
                                    Tình trạng giao hàng:
                                </span>

                                <strong>
                                    ${shippingStatus}
                                </strong>

                            </div>


                            ${trackingCode
                ? `
                                        <div>

                                            <i class='bx bx-barcode'></i>

                                            <span>
                                                Mã vận đơn:
                                            </span>

                                            <strong>
                                                ${trackingCode}
                                            </strong>

                                        </div>
                                    `
                : ""
            }

                        </div>
                    `
            : ""
        }
 
            <div class="shopee-order-bottom">

                <div class="order-date">

                    Ngày đặt:
                    ${order.order_date || "—"}

                </div>


                <div class="shopee-order-summary">

                    <div class="order-total">

                        <span>
                            Thành tiền:
                        </span>

                        <strong>
                            ${formatPrice(
            order.total_amount
        )}
                        </strong>

                    </div>


                    <a
                        href="/orders/${order.order_id}"
                        class="order-detail-btn"
                    >
                        Xem chi tiết
                    </a>

                </div>

            </div>

        </article>
    `;

}
 
function renderRecentOrders() {

    if (
        !allOrders.length
    ) {

        recentOrders.innerHTML = `
            <div class="profile-empty">

                <i class='bx bx-package'></i>

                <p>
                    Chưa có đơn hàng
                </p>

            </div>
        `;


        return;

    }


    const recent =
        [...allOrders]
            .slice(
                0,
                3
            );


    recentOrders.innerHTML =
        recent
            .map(
                createOrderHTML
            )
            .join("");

}
 
function renderOrders(orders) {

    if (
        !orders.length
    ) {

        orderList.innerHTML = `
            <div class="profile-empty">

                <i class='bx bx-package'></i>

                <p>
                    Không có đơn hàng
                </p>

            </div>
        `;


        return;

    }


    orderList.innerHTML =
        orders
            .map(
                createOrderHTML
            )
            .join("");

}
 
async function initProfile() {

    await loadProfile();

    await loadOrders();

    await loadWallet();

    await loadWalletTransactions();

}


initProfile();