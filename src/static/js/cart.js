const cartList =
    document.getElementById("cart-list");

const emptyCart =
    document.getElementById("empty-cart");

const selectAllTop =
    document.getElementById("select-all-top");

const selectAllBottom =
    document.getElementById("select-all-bottom");

const selectedCount =
    document.getElementById("selected-count");

const selectedTotal =
    document.getElementById("selected-total");

const checkoutBtn =
    document.getElementById("checkout-btn");

const deleteSelectedBtn =
    document.getElementById("delete-selected");

const recommendedGrid =
    document.getElementById("recommended-grid");


let cartItems = JSON.parse(
    localStorage.getItem("verdia_cart")
) || [];


let selectedIds = new Set();

function saveCart() {
    localStorage.setItem(
        "verdia_cart",
        JSON.stringify(cartItems)
    );
}

function formatPrice(price) {
    return Number(
        price
    ).toLocaleString("vi-VN")
        + "đ";
}


function getStatusBadge(status) {
    if (status === "PREORDER") {
        return `
            <span class="product-type preorder">
                Pre-order
            </span>
        `;
    }

    return `
        <span class="product-type in-stock">
            Có sẵn
        </span>
    `;
}


function renderCart() {
    cartList.innerHTML = "";

    if (cartItems.length === 0) {
        emptyCart.style.display =
            "flex";

        cartList.style.display =
            "none";
    } else {
        emptyCart.style.display =
            "none";

        cartList.style.display =
            "block";
    }


    cartItems.forEach(item => {
        const row =
            document.createElement(
                "article"
            );

        row.className =
            "cart-item";

        const checked =
            selectedIds.has(
                item.cart_item_id
            );


        row.innerHTML = `
            <div class="cart-item-select">

                <input
                    type="checkbox"
                    class="cart-item-checkbox"
                    data-id="${item.cart_item_id}"
                    ${checked ? "checked" : ""}
                >

            </div>


            <div class="cart-product">

                <img
                    class="cart-product-image"
                    src="${item.image}"
                    alt="${item.product_name}"
                >

                <div class="cart-product-info">

                    <div class="cart-product-name">
                        ${item.product_name}
                    </div>

                    <div class="cart-product-tags">
                        ${item.tags.join(" · ")}
                    </div>

                    ${getStatusBadge(
            item.status
        )}

                </div>

            </div>


            <div class="cart-price">

                ${formatPrice(
            item.price
        )}

            </div>


            <div>

                <div class="quantity-control">

                    <button
                        type="button"
                        class="decrease-btn"
                        data-id="${item.cart_item_id}"
                    >
                        −
                    </button>

                    <input
                        type="number"
                        value="${item.quantity}"
                        min="1"
                        class="quantity-input"
                        data-id="${item.cart_item_id}"
                    >

                    <button
                        type="button"
                        class="increase-btn"
                        data-id="${item.cart_item_id}"
                    >
                        +
                    </button>

                </div>

            </div>


            <div class="cart-subtotal">

                ${formatPrice(
            item.price
            * item.quantity
        )}

            </div>


            <div>

                <button
                    type="button"
                    class="remove-item"
                    data-id="${item.cart_item_id}"
                >
                    Xóa
                </button>

            </div>
        `;


        cartList.appendChild(
            row
        );
    });


    bindCartEvents();

    updateSummary();
}


function bindCartEvents() {

    document.querySelectorAll(
        ".cart-item-checkbox"
    ).forEach(input => {

        input.addEventListener(
            "change",
            () => {

                const id =
                    Number(
                        input.dataset.id
                    );

                if (input.checked) {
                    selectedIds.add(id);
                } else {
                    selectedIds.delete(id);
                }

                updateSummary();
            }
        );

    });


    document.querySelectorAll(
        ".increase-btn"
    ).forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const id =
                    Number(
                        button.dataset.id
                    );

                const item =
                    cartItems.find(
                        item =>
                            item.cart_item_id
                            === id
                    );

                item.quantity += 1;

                saveCart();
                renderCart();
            }
        );

    });


    document.querySelectorAll(
        ".decrease-btn"
    ).forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const id =
                    Number(
                        button.dataset.id
                    );

                const item =
                    cartItems.find(
                        item =>
                            item.cart_item_id
                            === id
                    );

                if (item.quantity > 1) {
                    item.quantity -= 1;

                    saveCart();
                }

                renderCart();
            }
        );

    });


    document.querySelectorAll(
        ".quantity-input"
    ).forEach(input => {

        input.addEventListener(
            "change",
            () => {

                const id =
                    Number(
                        input.dataset.id
                    );

                const item =
                    cartItems.find(
                        item =>
                            item.cart_item_id
                            === id
                    );

                const quantity =
                    Number(input.value);

                item.quantity =
                    quantity > 0
                        ? quantity
                        : 1;

                saveCart();
                renderCart();
            }
        );

    });


    document.querySelectorAll(
        ".remove-item"
    ).forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const id =
                    Number(
                        button.dataset.id
                    );

                cartItems =
                    cartItems.filter(
                        item =>
                            item.cart_item_id
                            !== id
                    );

                selectedIds.delete(id);

                saveCart();
                renderCart();
            }
        );

    });
}


function handleSelectAll(checked) {

    selectedIds.clear();

    if (checked) {
        cartItems.forEach(
            item => {
                selectedIds.add(
                    item.cart_item_id
                );
            }
        );
    }

    renderCart();
}


selectAllTop.addEventListener(
    "change",
    () => {
        handleSelectAll(
            selectAllTop.checked
        );
    }
);


selectAllBottom.addEventListener(
    "change",
    () => {
        handleSelectAll(
            selectAllBottom.checked
        );
    }
);


function updateSummary() {

    let total = 0;
    let quantity = 0;


    cartItems.forEach(item => {

        if (
            selectedIds.has(
                item.cart_item_id
            )
        ) {
            total +=
                item.price
                * item.quantity;

            quantity +=
                item.quantity;
        }

    });


    selectedCount.textContent =
        quantity;

    selectedTotal.textContent =
        formatPrice(total);


    const allSelected =
        cartItems.length > 0
        &&
        selectedIds.size
        === cartItems.length;


    selectAllTop.checked =
        allSelected;

    selectAllBottom.checked =
        allSelected;


    checkoutBtn.disabled =
        selectedIds.size === 0;
}


deleteSelectedBtn.addEventListener(
    "click",
    () => {

        if (selectedIds.size === 0) {
            return;
        }

        cartItems =
            cartItems.filter(
                item =>
                    !selectedIds.has(
                        item.cart_item_id
                    )
            );

        selectedIds.clear();

        saveCart();
        renderCart();
    }
);

checkoutBtn.addEventListener(
    "click",
    async () => {
        if (selectedIds.size === 0) {
            return;
        }

        const token = localStorage.getItem("access_token") || localStorage.getItem("token");

        if (!token) {
            localStorage.setItem("redirect_after_login", "/cart");
            window.location.href = "/login";
            return;
        }

        const selectedItems = cartItems.filter(
            item => selectedIds.has(item.cart_item_id)
        );

        if (selectedItems.length === 0) {
            return;
        }

        try {
            const res = await fetch("/api/orders", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    items: selectedItems.map(i => ({
                        product_id: i.product_id,
                        preorder_id: i.preorder_id || null,
                        quantity: i.quantity
                    }))
                })
            });

            const result = await res.json();
            if (!res.ok) throw new Error(result.message || "Không thể tạo đơn hàng");

            const realOrderId = result.data?.order?.order_id || result.order_id;

            cartItems = cartItems.filter(
                item => !selectedIds.has(item.cart_item_id)
            );
            selectedIds.clear();
            saveCart();
            window.location.href = `/payment/${realOrderId}`;

        } catch (e) {
            console.error("Lỗi checkout:", e);
            alert(e.message || "Đã xảy ra lỗi khi tạo đơn hàng.");
        }
    }
);

async function loadRecommended() {

    try {
        const response =
            await fetch(
                "/api/products"
            );

        const result =
            await response.json();


        if (!response.ok) {
            return;
        }


        const products =
            result.data?.products
            || [];


        const recommendations =
            products.slice(
                0,
                5
            );


        recommendedGrid.innerHTML =
            "";


        recommendations.forEach(
            product => {

                const card =
                    document.createElement(
                        "article"
                    );

                card.className =
                    "recommended-card";


                card.innerHTML = `
                    <img
                        src="${product.image}"
                        alt="${product.product_name}"
                    >

                    <div class="recommended-info">

                        <div class="recommended-name">
                            ${product.product_name}
                        </div>

                        <div class="recommended-price">
                            ${formatPrice(
                    product.price
                )}
                        </div>

                    </div>
                `;


                card.addEventListener(
                    "click",
                    () => {
                        window.location.href =
                            `/products/${product.product_id}`;
                    }
                );


                recommendedGrid.appendChild(
                    card
                );

            }
        );

    } catch (error) {
        console.error(error);
    }
}


renderCart();

loadRecommended();