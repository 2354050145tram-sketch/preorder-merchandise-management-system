const productsContainer =
    document.getElementById(
        "checkout-products"
    );

const addressLoading =
    document.getElementById(
        "address-loading"
    );

const addressContent =
    document.getElementById(
        "address-content"
    );

const receiverName =
    document.getElementById(
        "receiver-name"
    );

const receiverPhone =
    document.getElementById(
        "receiver-phone"
    );

const receiverAddress =
    document.getElementById(
        "receiver-address"
    );


const subtotalElement =
    document.getElementById(
        "subtotal"
    );

const preorderTotalElement =
    document.getElementById(
        "preorder-total"
    );

const inStockTotalElement =
    document.getElementById(
        "instock-total"
    );

const preorderRow =
    document.getElementById(
        "preorder-row"
    );

const inStockRow =
    document.getElementById(
        "instock-row"
    );


const depositBox =
    document.getElementById(
        "deposit-box"
    );

const depositOption =
    document.getElementById(
        "deposit-option"
    );


const fullPaymentAmount =
    document.getElementById(
        "full-payment-amount"
    );

const depositPaymentAmount =
    document.getElementById(
        "deposit-payment-amount"
    );


const remainingRow =
    document.getElementById(
        "remaining-row"
    );

const remainingAmount =
    document.getElementById(
        "remaining-amount"
    );

const payNowTotal =
    document.getElementById(
        "pay-now-total"
    );


const placeOrderBtn =
    document.getElementById(
        "place-order-btn"
    );


const token =
    localStorage.getItem(
        "access_token"
    );


let checkoutItems =
    JSON.parse(
        localStorage.getItem(
            "checkout_items"
        )
    ) || [];


let canDeposit = false;

let totals = {
    subtotal: 0,
    preorder: 0,
    inStock: 0,
};


function formatPrice(price) {
    return Number(price)
        .toLocaleString(
            "vi-VN"
        ) + "đ";
}



function requireLogin() {

    if (token) {
        return true;
    }


    localStorage.setItem(
        "redirect_after_login",
        window.location.pathname
    );

    window.location.href =
        "/login";

    return false;
}



async function loadUser() {

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


    if (
        response.status === 401
        ||
        response.status === 422
    ) {

        localStorage.removeItem(
            "access_token"
        );

        localStorage.removeItem(
            "refresh_token"
        );

        localStorage.removeItem(
            "user"
        );


        localStorage.setItem(
            "redirect_after_login",
            "/checkout"
        );


        window.location.href =
            "/login";

        return;
    }


    const result =
        await response.json();


    if (!response.ok) {
        throw new Error(
            result.message
            ||
            "Không thể lấy thông tin người dùng"
        );
    }


    const user =
        result.data;


    receiverName.textContent =
        user.profile.full_name
        || user.username;


    receiverPhone.textContent =
        user.profile.phone_num
        || "Chưa có số điện thoại";


    receiverAddress.textContent =
        user.profile.address
        || "Chưa có địa chỉ";


    addressLoading.style.display =
        "none";

    addressContent.style.display =
        "grid";
}


function renderProducts() {

    productsContainer.innerHTML =
        "";


    totals = {
        subtotal: 0,
        preorder: 0,
        inStock: 0,
    };


    checkoutItems.forEach(
        item => {

            const itemTotal =
                Number(item.price)
                *
                Number(item.quantity);


            totals.subtotal +=
                itemTotal;


            if (
                item.status
                === "PREORDER"
            ) {

                totals.preorder +=
                    itemTotal;

            } else {

                totals.inStock +=
                    itemTotal;
            }


            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "checkout-product";


            row.innerHTML = `
                <div class="checkout-product-main">

                    <img
                        src="${item.image || ""}"
                        alt="${item.product_name}"
                    >

                    <div>

                        <div class="checkout-product-name">
                            ${item.product_name}
                        </div>

                        <span
                            class="
                                checkout-product-status
                                ${item.status
                    === "PREORDER"
                    ? "preorder"
                    : "in-stock"
                }
                            "
                        >
                            ${item.status
                    === "PREORDER"
                    ? "Pre-order"
                    : "Có sẵn"
                }
                        </span>

                    </div>

                </div>

                <div class="checkout-price">
                    ${formatPrice(item.price)}
                </div>

                <div class="checkout-quantity">
                    x${item.quantity}
                </div>

                <div class="checkout-product-total">
                    ${formatPrice(itemTotal)}
                </div>
            `;


            productsContainer.appendChild(
                row
            );
        }
    );


    updateSummary();

    updateDepositVisibility();
}


function updateDepositVisibility() {

    const hasPreorder =
        totals.preorder > 0;



    if (!hasPreorder) {

        depositBox.style.display =
            "none";

        return;
    }


    depositBox.style.display =
        "block";



    if (!canDeposit) {

        depositOption.style.display =
            "none";


        const fullRadio =
            document.querySelector(
                'input[name="payment_type"][value="FULL"]'
            );

        fullRadio.checked =
            true;

    } else {

        depositOption.style.display =
            "grid";
    }


    updatePaymentAmount();
}



function updateSummary() {

    subtotalElement.textContent =
        formatPrice(
            totals.subtotal
        );


    preorderTotalElement.textContent =
        formatPrice(
            totals.preorder
        );


    inStockTotalElement.textContent =
        formatPrice(
            totals.inStock
        );


    preorderRow.style.display =
        totals.preorder > 0
            ? "flex"
            : "none";


    inStockRow.style.display =
        totals.inStock > 0
            ? "flex"
            : "none";


    fullPaymentAmount.textContent =
        formatPrice(
            totals.subtotal
        );


    const depositPayNow =
        totals.inStock
        +
        totals.preorder
        * 0.7;


    depositPaymentAmount.textContent =
        formatPrice(
            depositPayNow
        );


    updatePaymentAmount();
}



function updatePaymentAmount() {

    const paymentType =
        document.querySelector(
            'input[name="payment_type"]:checked'
        )?.value
        || "FULL";


    if (
        paymentType === "DEPOSIT"
        &&
        canDeposit
        &&
        totals.preorder > 0
    ) {

        const payNow =
            totals.inStock
            +
            totals.preorder
            * 0.7;


        const remaining =
            totals.preorder
            * 0.3;


        payNowTotal.textContent =
            formatPrice(payNow);


        remainingAmount.textContent =
            formatPrice(remaining);


        remainingRow.style.display =
            "flex";

    } else {

        payNowTotal.textContent =
            formatPrice(
                totals.subtotal
            );


        remainingRow.style.display =
            "none";
    }
}


document
    .querySelectorAll(
        'input[name="payment_type"]'
    )
    .forEach(
        input => {

            input.addEventListener(
                "change",
                updatePaymentAmount
            );
        }
    );


async function loadPaymentSummary(orderId) {

    const response = await fetch(
        `/api/orders/${orderId}/payment-summary`,
        {
            headers: {
                Authorization: `Bearer ${token}`,
            }
        }
    );

    const result = await response.json();

    if (!response.ok) {
        throw new Error(
            result.message ||
            "Không thể lấy thông tin thanh toán"
        );
    }

    const summary = result.data;

    canDeposit =
        summary.eligible_for_deposit === true;

    totals.subtotal =
        Number(summary.total_amount);

    totals.preorder =
        Number(summary.preorder_amount);

    totals.inStock =
        Number(summary.in_stock_amount);

    updateSummary();

    if (totals.preorder > 0) {

        depositBox.style.display = "block";

        if (canDeposit) {

            depositOption.style.display = "grid";

        } else {


            depositOption.style.display = "none";

            const fullRadio =
                document.querySelector(
                    'input[name="payment_type"][value="FULL"]'
                );

            fullRadio.checked = true;
        }

    } else {
        depositBox.style.display = "none";
    }

    updatePaymentAmount();

    placeOrderBtn.disabled = false;
    placeOrderBtn.textContent = "Thanh toán";
 
    placeOrderBtn.onclick = null;

    placeOrderBtn.addEventListener(
        "click",
        () => processPayment(orderId),
        { once: true }
    );
}


placeOrderBtn.addEventListener(
    "click",
    async () => {

        if (checkoutItems.length === 0) {
            alert(
                "Không có sản phẩm để thanh toán"
            );

            return;
        }

        const paymentMethod =
            document.querySelector(
                'input[name="payment_method"]:checked'
            ).value;

        let selectedPaymentType =
            document.querySelector(
                'input[name="payment_type"]:checked'
            )?.value || "FULL";
         if (
            selectedPaymentType === "DEPOSIT"
            &&
            !canDeposit
        ) {
            selectedPaymentType = "FULL";
        }


        const paymentType =
            selectedPaymentType === "DEPOSIT"
                ? "ĐẶT CỌC"
                : "THANH TOÁN FULL";


        placeOrderBtn.disabled = true;

        placeOrderBtn.textContent =
            "Đang xử lý...";


        try {
            const orderResponse =
                await fetch(
                    "/api/orders",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            Authorization:
                                `Bearer ${token}`,
                        },

                        body: JSON.stringify({
                            items:
                                checkoutItems.map(
                                    item => ({
                                        product_id:
                                            item.product_id,

                                        preorder_id:
                                            item.preorder_id
                                            || null,

                                        quantity:
                                            item.quantity,
                                    })
                                )
                        }),
                    }
                );


            const orderResult =
                await orderResponse.json();


            if (!orderResponse.ok) {
                throw new Error(
                    orderResult.message ||
                    "Không thể tạo đơn hàng"
                );
            }


            const order =
                orderResult.data.order;


            const orderId =
                order.order_id;


            if (
                paymentMethod === "MOMO"
            ) {
                const transactionId =
                    "MOMO_TEST_"
                    +
                    orderId
                    +
                    "_"
                    +
                    Date.now();


                const paymentResponse =
                    await fetch(
                        `/api/orders/${orderId}/payments`,
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json",

                                Authorization:
                                    `Bearer ${token}`,
                            },

                            body:
                                JSON.stringify({
                                    payment_method:
                                        "MOMO",

                                    payment_type:
                                        paymentType,

                                    transaction_id:
                                        transactionId,
                                }),
                        }
                    );


                const paymentResult =
                    await paymentResponse.json();


                if (!paymentResponse.ok) {
                    throw new Error(
                        paymentResult.message ||
                        "Không thể tạo thanh toán"
                    );
                }


                localStorage.setItem(
                    "current_order_id",
                    orderId
                );


                localStorage.removeItem(
                    "checkout_items"
                );


                window.location.href =
                    `/payment/${orderId}`;

                return;
            }

            if (
                paymentMethod === "VÍ VERD"
            ) {


                localStorage.setItem(
                    "current_order_id",
                    orderId
                );


                window.location.href =
                    `/wallet-payment/${orderId}`;

                return;
            }


        } catch (error) {

            console.error(
                "CHECKOUT ERROR:",
                error
            );

            alert(
                error.message ||
                "Không thể đặt hàng"
            );


            placeOrderBtn.disabled =
                false;

            placeOrderBtn.textContent =
                "Đặt hàng";
        }
    }
);

async function loadDepositEligibility() {

    const response = await fetch(
        "/api/orders/deposit-eligibility",
        {
            headers: {
                Authorization: `Bearer ${token}`,
            }
        }
    );

    const result = await response.json();

    if (!response.ok) {
        throw new Error(
            result.message ||
            "Không thể kiểm tra quyền đặt cọc"
        );
    }

    canDeposit =
        result.data
            .eligible_for_deposit === true;

    updateDepositVisibility();
}

async function initCheckout() {

    if (!requireLogin()) {
        return;
    }

    if (checkoutItems.length === 0) {
        window.location.href = "/cart";
        return;
    }

    try {

        renderProducts();

        await Promise.all([
            loadUser(),
            loadDepositEligibility(),
        ]);

    } catch (error) {

        console.error(
            "CHECKOUT ERROR:",
            error
        );

        alert(
            error.message ||
            "Không thể tải trang thanh toán"
        );
    }
}

initCheckout();