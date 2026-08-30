const loadingState =
    document.getElementById(
        "product-detail-loading"
    );

const errorState =
    document.getElementById(
        "product-detail-error"
    );

const detailContainer =
    document.getElementById(
        "product-detail"
    );

const informationContainer =
    document.getElementById(
        "product-information"
    );


const breadcrumbProduct =
    document.getElementById(
        "breadcrumb-product"
    );

const detailImage =
    document.getElementById(
        "detail-image"
    );

const imagePlaceholder =
    document.getElementById(
        "detail-image-placeholder"
    );

const detailStatus =
    document.getElementById(
        "detail-status"
    );

const detailTags =
    document.getElementById(
        "detail-tags"
    );

const detailName =
    document.getElementById(
        "detail-name"
    );

const detailPrice =
    document.getElementById(
        "detail-price"
    );

const detailDescription =
    document.getElementById(
        "detail-description"
    );


const preorderInfoBox =
    document.getElementById(
        "preorder-info-box"
    );

const preorderState =
    document.getElementById(
        "preorder-state"
    );

const preorderDate =
    document.getElementById(
        "preorder-date"
    );


const quantityInput =
    document.getElementById(
        "product-quantity"
    );

const decreaseQuantityBtn =
    document.getElementById(
        "decrease-quantity"
    );

const increaseQuantityBtn =
    document.getElementById(
        "increase-quantity"
    );


const addCartBtn =
    document.getElementById(
        "add-cart-detail"
    );

const buyNowBtn =
    document.getElementById(
        "buy-now-detail"
    );


const informationStatus =
    document.getElementById(
        "information-status"
    );

const informationTags =
    document.getElementById(
        "information-tags"
    );

const informationDescription =
    document.getElementById(
        "information-description"
    );


const toast =
    document.getElementById(
        "product-detail-toast"
    );


let currentProduct = null;

let currentPreorder = null;
 
function getProductId() {

    const parts =
        window.location.pathname
            .split("/")
            .filter(Boolean);


    return Number(
        parts[parts.length - 1]
    );

}
 
function formatPrice(price) {

    return Number(
        price || 0
    ).toLocaleString(
        "vi-VN"
    ) + "đ";

}
 
function formatDate(value) {

    if (!value) {
        return "";
    }


    const date =
        new Date(
            `${value}T00:00:00`
        );


    return date.toLocaleDateString(
        "vi-VN"
    );

}
 
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

    }, 2200);

}
 
function getTags(product) {

    if (
        !product.tags
        ||
        !product.tags.length
    ) {

        return "Verdia Merchandise";

    }


    const uniqueTags =
        [
            ...new Set(
                product.tags.map(
                    tag => tag.name
                )
            )
        ];


    return uniqueTags.join(
        " · "
    );

}
 
async function loadProduct() {

    const productId =
        getProductId();


    if (!productId) {

        showError();

        return;

    }


    try {

        const response =
            await fetch(
                `/api/products/${productId}`
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.message
                ||
                "Không thể tải sản phẩm"
            );

        }


        currentProduct =
            result.data?.product
            ||
            result.product;


        if (!currentProduct) {

            throw new Error(
                "Không tìm thấy sản phẩm"
            );

        }


        if (
            currentProduct.status
            === "PREORDER"
            &&
            currentProduct.preorder_id
        ) {

            await loadPreorder(
                currentProduct.preorder_id
            );

        }


        renderProduct();


    } catch (error) {

        console.error(
            "LOAD PRODUCT DETAIL ERROR:",
            error
        );


        showError();

    }

}
 
async function loadPreorder(
    preorderId
) {

    try {

        const response =
            await fetch(
                `/api/preorders/${preorderId}`
            );


        const result =
            await response.json();


        if (!response.ok) {

            return;

        }


        currentPreorder =
            result.data?.preorder
            ||
            result.preorder
            ||
            null;


    } catch (error) {

        console.error(
            "LOAD PREORDER DETAIL ERROR:",
            error
        );

    }

}
 
function renderProduct() {

    const product =
        currentProduct;


    loadingState.style.display =
        "none";


    detailContainer.style.display =
        "grid";


    informationContainer.style.display =
        "block";
 
    document.title =
        `${product.product_name} - Verdia Merchandise`;


    breadcrumbProduct.textContent =
        product.product_name;


    detailName.textContent =
        product.product_name;
 
    if (product.image) {

        detailImage.src =
            product.image;


        detailImage.style.display =
            "block";


        detailImage.onerror =
            () => {

                detailImage.style.display =
                    "none";


                imagePlaceholder.style.display =
                    "flex";

            };

    } else {

        detailImage.style.display =
            "none";


        imagePlaceholder.style.display =
            "flex";

    }
 
    const tags =
        getTags(product);


    detailTags.textContent =
        tags;


    informationTags.textContent =
        tags;
 
    detailDescription.textContent =
        product.description;


    informationDescription.textContent =
        product.description;
 
    detailPrice.textContent =
        formatPrice(
            product.price
        );
 
    renderStatus();
 
    updateActionState();

}
 
function renderStatus() {

    const product =
        currentProduct;


    if (
        product.status
        === "IN_STOCK"
    ) {

        detailStatus.innerHTML = `
            <span class="in-stock">
                Có sẵn
            </span>
        `;


        informationStatus.textContent =
            "Có sẵn";


        preorderInfoBox.style.display =
            "none";


        return;

    }


    preorderInfoBox.style.display =
        "flex";


    if (
        product.preorder_available
    ) {

        detailStatus.innerHTML = `
            <span class="preorder">
                Pre-order
            </span>
        `;


        informationStatus.textContent =
            "Pre-order đang mở";


        preorderState.textContent =
            "Đang nhận đặt hàng";


        if (currentPreorder) {

            preorderDate.textContent =
                `Từ ${formatDate(
                    currentPreorder.start_date
                )} đến ${formatDate(
                    currentPreorder.end_date
                )}`;

        } else {

            preorderDate.textContent =
                "Đợt pre-order đang mở.";

        }


        return;

    }


    detailStatus.innerHTML = `
        <span class="closed">
            Pre-order đã kết thúc
        </span>
    `;


    informationStatus.textContent =
        "Pre-order hiện không mở";


    preorderState.textContent =
        "Đợt pre-order đã kết thúc";


    preorderDate.textContent =
        "Sản phẩm hiện chưa thể đặt hàng.";

}
 
function updateActionState() {

    const unavailable =
        currentProduct.status
        === "PREORDER"
        &&
        !currentProduct.preorder_available;


    addCartBtn.disabled =
        unavailable;


    buyNowBtn.disabled =
        unavailable;


    quantityInput.disabled =
        unavailable;


    decreaseQuantityBtn.disabled =
        unavailable;


    increaseQuantityBtn.disabled =
        unavailable;


    if (unavailable) {

        addCartBtn.innerHTML = `
            <i class='bx bx-time-five'></i>
            Đã kết thúc
        `;


        buyNowBtn.textContent =
            "Không thể đặt hàng";

    }

}
 
decreaseQuantityBtn.addEventListener(
    "click",
    () => {

        const quantity =
            Number(
                quantityInput.value
            );


        if (quantity > 1) {

            quantityInput.value =
                quantity - 1;

        }

    }
);


increaseQuantityBtn.addEventListener(
    "click",
    () => {

        const quantity =
            Number(
                quantityInput.value
            );


        quantityInput.value =
            quantity + 1;

    }
);
 
function addCurrentProductToCart() {

    if (!currentProduct) {

        return false;

    }


    if (
        currentProduct.status
        === "PREORDER"
        &&
        !currentProduct.preorder_available
    ) {

        return false;

    }


    const token =
        localStorage.getItem(
            "access_token"
        );


    if (!token) {

        localStorage.setItem(
            "redirect_after_login",
            window.location.pathname
        );


        window.location.href =
            "/login";


        return false;

    }


    const quantity =
        Number(
            quantityInput.value
        );


    let cart =
        JSON.parse(
            localStorage.getItem(
                "verdia_cart"
            )
        ) || [];


    const existingItem =
        cart.find(
            item =>
                Number(
                    item.product_id
                )
                ===
                Number(
                    currentProduct.product_id
                )
        );


    if (existingItem) {

        existingItem.quantity +=
            quantity;


        if (
            currentProduct.status
            === "PREORDER"
        ) {

            existingItem.preorder_id =
                currentProduct.preorder_id;

        }

    } else {

        cart.push({

            cart_item_id:
                Date.now(),

            product_id:
                currentProduct.product_id,

            product_name:
                currentProduct.product_name,

            price:
                Number(
                    currentProduct.price
                ),

            quantity:
                quantity,

            status:
                currentProduct.status,

            preorder_id:
                currentProduct.status
                === "PREORDER"
                    ? currentProduct.preorder_id
                    : null,

            tags:
                currentProduct.tags
                    ? currentProduct.tags.map(
                        tag => tag.name
                    )
                    : [],

            image:
                currentProduct.image
                || ""

        });

    }


    localStorage.setItem(
        "verdia_cart",
        JSON.stringify(
            cart
        )
    );


    return true;

}
 
addCartBtn.addEventListener(
    "click",
    () => {

        const added =
            addCurrentProductToCart();


        if (added) {

            showToast(
                "Đã thêm sản phẩm vào giỏ hàng"
            );

        }

    }
);
 
buyNowBtn.addEventListener(
    "click",
    () => {

        const added =
            addCurrentProductToCart();


        if (!added) {
            return;
        }


        window.location.href =
            "/cart";

    }
);
 
function showError() {

    loadingState.style.display =
        "none";


    detailContainer.style.display =
        "none";


    informationContainer.style.display =
        "none";


    errorState.style.display =
        "flex";

}
 
loadProduct();