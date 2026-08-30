document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadOrderDetail();

    }
);

function getToken() {

    return localStorage.getItem(
        "access_token"
    );

}

function getOrderId() {

    const parts =
        window.location.pathname
            .split("/")
            .filter(Boolean);


    return parts[
        parts.length - 1
    ];

}

async function loadOrderDetail() {

    const token =
        getToken();


    if (!token) {

        localStorage.setItem(
            "redirect_after_login",
            window.location.pathname
        );


        window.location.href =
            "/login";

        return;
    }


    const orderId =
        getOrderId();


    try {

        const [
            orderResponse,
            summaryResponse
        ] =
            await Promise.all([

                fetch(
                    `/api/orders/${orderId}`,
                    {
                        headers: {
                            Authorization:
                                `Bearer ${token}`
                        }
                    }
                ),

                fetch(
                    `/api/orders/${orderId}/payment-summary`,
                    {
                        headers: {
                            Authorization:
                                `Bearer ${token}`
                        }
                    }
                )

            ]);


        const orderResult =
            await orderResponse.json();


        const summaryResult =
            await summaryResponse.json();


        if (!orderResponse.ok) {

            throw new Error(
                orderResult.message
                ||
                "Không thể tải đơn hàng"
            );

        }


        const order =
            orderResult.data?.order
            ||
            orderResult.order;


        const summary =
            summaryResponse.ok
                ? (
                    summaryResult.data
                    ||
                    summaryResult
                )
                : null;


        if (!order) {

            throw new Error(
                "Không tìm thấy đơn hàng"
            );

        }


        renderOrderDetail(
            order,
            summary
        );


        document
            .getElementById(
                "order-detail-loading"
            )
            .style.display =
            "none";


        document
            .getElementById(
                "order-detail-content"
            )
            .style.display =
            "block";


    } catch (error) {

        console.error(
            "ORDER DETAIL ERROR:",
            error
        );


        document
            .getElementById(
                "order-detail-loading"
            )
            .style.display =
            "none";


        document
            .getElementById(
                "order-detail-error"
            )
            .style.display =
            "flex";

    }

}

function renderOrderDetail(
    order,
    summary
) {

    document.getElementById(
        "detail-order-id"
    ).textContent =
        order.order_id;


    document.getElementById(
        "detail-order-date"
    ).textContent =
        formatDate(
            order.order_date
        );


    document.getElementById(
        "detail-order-status"
    ).textContent =
        order.order_status;


    const items =
        order.order_items
        ||
        [];


    renderProducts(
        items
    );


    renderPreorders(
        items
    );


    renderShipping(
        order,
        items
    );


    renderShippingTimeline(
        order,
        items
    );


    renderPayments(
        order.payments
        ||
        []
    );


    renderPaymentSummary(
        order,
        summary
    );

    renderOrderActions(
        order,
        summary
    );

}

function renderProducts(items) {

    const container =
        document.getElementById(
            "detail-product-list"
        );

    container.innerHTML =
        items
            .map(item => {

                const product =
                    item.product || {};

                const image =
                    product.image || "";

                const name =
                    product.product_name
                    ||
                    item.product_name
                    ||
                    "Sản phẩm";

                const isPreorder =
                    Boolean(
                        item.preorder_id
                    );

                return `

                    <div class="detail-product">

                        <div class="detail-product-image">

                            ${image
                        ? `
                                    <img
                                        src="${image}"
                                        alt="${escapeHTML(name)}"
                                    >
                                `
                        : `
                                    <div class="detail-product-placeholder">
                                        <i class='bx bx-image'></i>
                                    </div>
                                `
                    }

                        </div>


                        <div class="detail-product-info">

                            <strong>
                                ${escapeHTML(name)}
                            </strong>

                            <span
                                class="
                                    detail-product-type
                                    ${isPreorder
                        ? "preorder"
                        : "instock"
                    }
                                "
                            >
                                ${isPreorder
                        ? "PRE-ORDER"
                        : "CÓ SẴN"
                    }
                            </span>

                            <small>
                                Số lượng:
                                ${item.quantity || 1}
                            </small>

                        </div>


                        <div class="detail-product-price">

                            <span>
                                ${formatPrice(item.price)}
                            </span>

                            <strong>
                                ${formatPrice(
                        Number(item.price || 0)
                        *
                        Number(item.quantity || 1)
                    )}
                            </strong>

                            ${item.item_status !== "ĐÃ HỦY"
                        ? `
                                        <button
                                            type="button"
                                            class="cancel-order-item-btn"
                                            data-order-item-id="${item.order_item_id}">
                                            Hủy sản phẩm
                                        </button>
                                    `
                        : `
                                        <span class="cancelled-item-label">
                                            ĐÃ HỦY
                                        </span>
                                    `
                    }

                        </div>

                    </div>

                `;

            })
            .join("");


    container
        .querySelectorAll(
            ".cancel-order-item-btn"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                async () => {

                    const orderItemId =
                        button.dataset.orderItemId;

                    const confirmed =
                        confirm(
                            "Bạn có chắc muốn hủy sản phẩm này?"
                        );

                    if (!confirmed) {
                        return;
                    }

                    const token =
                        getToken();

                    try {

                        button.disabled =
                            true;

                        button.textContent =
                            "Đang hủy...";

                        const response =
                            await fetch(
                                `/api/orders/items/${orderItemId}/cancel`,
                                {
                                    method: "PUT",
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
                                result.message
                                ||
                                "Không thể hủy sản phẩm"
                            );
                        }

                        alert(
                            "Đã hủy sản phẩm."
                        );

                        window.location.reload();

                    } catch (error) {

                        console.error(
                            "CANCEL ITEM ERROR:",
                            error
                        );

                        alert(
                            error.message
                            ||
                            "Không thể hủy sản phẩm"
                        );

                        button.disabled =
                            false;

                        button.textContent =
                            "Hủy sản phẩm";
                    }
                }
            );
        });

}

function renderPreorders(
    items
) {

    const preorderItems =
        items.filter(
            item =>
                item.preorder_id
        );


    const box =
        document.getElementById(
            "preorder-detail-box"
        );


    const container =
        document.getElementById(
            "preorder-detail-list"
        );


    if (
        !preorderItems.length
    ) {

        box.style.display =
            "none";

        return;

    }


    box.style.display =
        "block";


    container.innerHTML =
        preorderItems
            .map(item => {

                const preorder =
                    item.preorder
                    ||
                    {};


                const product =
                    item.product
                    ||
                    {};


                const progress =
                    preorder.progress_status
                    ||
                    "ĐANG CẬP NHẬT";


                const stages = [

                    {
                        key:
                            "PREORDER",

                        label:
                            "Pre-order"
                    },

                    {
                        key:
                            "PRODUCTION",

                        label:
                            "Sản xuất"
                    },

                    {
                        key:
                            "IN_TRANSIT",

                        label:
                            "Đang về"
                    },

                    {
                        key:
                            "COMPLETED",

                        label:
                            "Hoàn thành"
                    }

                ];


                const currentStage =
                    getPreorderStage(
                        progress
                    );


                const currentIndex =
                    stages.findIndex(
                        stage =>
                            stage.key
                            === currentStage
                    );


                return `

                    <div class="preorder-detail-item">

                        <div class="preorder-detail-heading">

                            <div>

                                <strong>
                                    ${escapeHTML(
                    product.product_name
                    ||
                    item.product_name
                    ||
                    "Sản phẩm Pre-order"
                )}
                                </strong>

                                <span>
                                    Pre-order #${item.preorder_id}
                                </span>

                            </div>


                            <span class="preorder-current-status">
                                ${progress}
                            </span>

                        </div>


                        <div class="preorder-timeline">

                            ${stages
                        .map(
                            (
                                stage,
                                index
                            ) => {

                                const active =
                                    index
                                    <= currentIndex;


                                return `

                                                <div
                                                    class="
                                                        preorder-step
                                                        ${active
                                        ? "active"
                                        : ""
                                    }
                                                    "
                                                >

                                                    <div class="preorder-step-dot">

                                                        <i
                                                            class='bx
                                                            ${active
                                        ? "bx-check"
                                        : "bx-circle"
                                    }'
                                                        ></i>

                                                    </div>

                                                    <span>
                                                        ${stage.label}
                                                    </span>

                                                </div>

                                            `;

                            }
                        )
                        .join("")
                    }

                        </div>


                        ${preorder.progress_note
                        ? `
                                    <p class="preorder-note">

                                        ${escapeHTML(
                            preorder.progress_note
                        )}

                                    </p>
                                `
                        : ""
                    }

                    </div>

                `;

            })
            .join("");

}

function getPreorderStage(
    progress
) {

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


    return "PREORDER";

}

function renderShipping(
    order,
    items
) {

    const container =
        document.getElementById(
            "shipping-info-list"
        );


    const shippingItems =
        items.filter(
            item =>
                item.shipping_method
                ||
                item.tracking_code
                ||
                item.shipping_status
        );


    if (!shippingItems.length) {

        container.innerHTML = `

            <div class="detail-empty-info">

                <i class='bx bx-package'></i>

                <span>
                    Đơn hàng chưa bắt đầu vận chuyển.
                </span>

            </div>

        `;

        return;

    }


    container.innerHTML =
        shippingItems
            .map(item => {

                return `

                    <div class="shipping-detail-row">

                        <div>

                            <span>
                                Phương thức
                            </span>

                            <strong>
                                ${item.shipping_method || "—"}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Mã vận đơn
                            </span>

                            <strong>
                                ${item.tracking_code || "—"}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Tình trạng
                            </span>

                            <strong>
                                ${item.shipping_status || "Chưa vận chuyển"}
                            </strong>

                        </div>

                    </div>

                `;

            })
            .join("");

}

function renderShippingTimeline(
    order,
    items
) {

    const container =
        document.getElementById(
            "shipping-timeline"
        );


    const status =
        getShippingStatus(
            order,
            items
        );


    const stages = [

        {
            key:
                "PROCESSING",

            label:
                "Đang xử lý",

            icon:
                "bx-package"
        },

        {
            key:
                "PICKUP",

            label:
                "Chờ lấy hàng",

            icon:
                "bx-box"
        },

        {
            key:
                "DELIVERING",

            label:
                "Đang giao",

            icon:
                "bx-truck"
        },

        {
            key:
                "COMPLETED",

            label:
                "Hoàn thành",

            icon:
                "bx-check-circle"
        }

    ];


    const currentIndex =
        stages.findIndex(
            stage =>
                stage.key === status
        );


    container.innerHTML =
        stages
            .map(
                (
                    stage,
                    index
                ) => {

                    const active =
                        index
                        <= currentIndex;


                    return `

                        <div
                            class="
                                shipping-step
                                ${active
                            ? "active"
                            : ""
                        }
                            "
                        >

                            <div class="shipping-step-icon">

                                <i
                                    class='bx ${stage.icon}'
                                ></i>

                            </div>


                            <span>
                                ${stage.label}
                            </span>

                        </div>

                    `;

                }
            )
            .join("");

}

function getShippingStatus(
    order,
    items
) {

    const statuses =
        items
            .map(
                item =>
                    item.shipping_status
            )
            .filter(Boolean);


    if (
        statuses.length
        &&
        statuses.every(
            status =>
                status === "ĐÃ GIAO"
        )
    ) {

        return "COMPLETED";

    }


    if (
        statuses.includes(
            "ĐANG GIAO HÀNG"
        )
    ) {

        return "DELIVERING";

    }


    if (
        statuses.includes(
            "ĐANG LẤY HÀNG"
        )
    ) {

        return "PICKUP";

    }


    if (
        order.order_status
        === "HOÀN THÀNH"
    ) {

        return "COMPLETED";

    }


    return "PROCESSING";

}

function renderPaymentSummary(
    order,
    summary
) {

    const data =
        summary
        ||
        {};


    document.getElementById(
        "detail-instock-total"
    ).textContent =
        formatPrice(
            data.in_stock_amount
            ||
            0
        );


    document.getElementById(
        "detail-preorder-total"
    ).textContent =
        formatPrice(
            data.preorder_amount
            ||
            0
        );


    document.getElementById(
        "detail-shipping-fee"
    ).textContent =
        formatPrice(
            data.shipping_fee
            ??
            order.shipping_fee
            ??
            0
        );


    document.getElementById(
        "detail-paid-total"
    ).textContent =
        formatPrice(
            data.total_paid
            ||
            0
        );


    document.getElementById(
        "detail-remaining-total"
    ).textContent =
        formatPrice(
            data.remaining_amount
            ||
            0
        );


    document.getElementById(
        "detail-grand-total"
    ).textContent =
        formatPrice(
            data.total_amount
            ??
            order.total_amount
            ??
            0
        );

}

function renderPayments(
    payments
) {

    const container =
        document.getElementById(
            "detail-payment-list"
        );


    if (!payments.length) {

        container.innerHTML = `

            <div class="detail-empty-info">

                Chưa có giao dịch thanh toán.

            </div>

        `;

        return;

    }


    container.innerHTML =
        payments
            .map(payment => `

                <div class="detail-payment-row">

                    <div>

                        <strong>
                            ${payment.payment_type}
                        </strong>

                        <span>
                            ${payment.payment_method}
                        </span>

                    </div>


                    <div>

                        <strong>
                            ${formatPrice(payment.amount)}
                        </strong>

                        <span>
                            ${payment.payment_status}
                        </span>

                    </div>

                </div>

            `)
            .join("");

}

function formatPrice(
    value
) {

    return Number(
        value || 0
    ).toLocaleString(
        "vi-VN"
    ) + "đ";

}


function formatDate(
    value
) {

    if (!value) {
        return "—";
    }


    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return value;

    }


    return date.toLocaleDateString(
        "vi-VN"
    );

}


function escapeHTML(
    value
) {

    return String(
        value || ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}

const orderActions =
    document.getElementById(
        "order-actions"
    );

const payOrderBtn =
    document.getElementById(
        "pay-order-btn"
    );

const cancelOrderBtn =
    document.getElementById(
        "cancel-order-btn"
    );


function renderOrderActions(
    order,
    summary
) {

    if (!orderActions) {
        return;
    }

    const status =
        String(
            order.order_status || ""
        )
            .trim()
            .toUpperCase();

    const remainingAmount =
        Number(
            summary?.remaining_amount
            ?? 0
        );

    const canPay =
        status === "CHỜ XÁC NHẬN"
        &&
        remainingAmount > 0;

    if (!canPay) {
        orderActions.style.display =
            "none";

        return;
    }

    orderActions.style.display =
        "flex";

    payOrderBtn.href =
        `/payment/${order.order_id}`;
}