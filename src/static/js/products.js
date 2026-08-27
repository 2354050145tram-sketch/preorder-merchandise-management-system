const productGrid =
    document.getElementById("product-grid");

const loadingState =
    document.getElementById("loading-state");

const emptyState =
    document.getElementById("empty-state");

const productCount =
    document.getElementById("product-count");

const resultInfo =
    document.getElementById("result-info");

const keywordInput =
    document.getElementById("keyword");

const searchBtn =
    document.getElementById("search-btn");

const minPriceInput =
    document.getElementById("min-price");

const maxPriceInput =
    document.getElementById("max-price");

const categorySelect =
    document.getElementById("category-select");

const subCategorySelect =
    document.getElementById(
        "sub-category-select"
    );

const subCategoryGroup =
    document.getElementById(
        "sub-category-group"
    );

const tagGroup =
    document.getElementById("tag-group");

const tagFilter =
    document.getElementById("tag-filter");

const applyFilterBtn =
    document.getElementById("apply-filter");

const clearFilterBtn =
    document.getElementById("clear-filter");

const sortSelect =
    document.getElementById("sort-select");

const filterOverlay =
    document.getElementById("filter-overlay");

const openFilterBtn =
    document.getElementById("open-filter");

const closeFilterBtn =
    document.getElementById("close-filter");


let currentProducts = [];

let hasSearchOrFilter = false;

async function restoreOAuthLogin() {
    if (
        localStorage.getItem(
            "access_token"
        )
    ) {
        return;
    }

    try {
        const response =
            await fetch(
                "/api/users/oauth/session"
            );

        if (!response.ok) {
            return;
        }

        const result =
            await response.json();

        localStorage.setItem(
            "access_token",
            result.data.access_token
        );

        localStorage.setItem(
            "refresh_token",
            result.data.refresh_token
        );

    } catch (error) {
        console.error(
            "OAUTH SESSION ERROR:",
            error
        );
    }
}
 
openFilterBtn.addEventListener(
    "click",
    () => {
        filterOverlay.classList.add(
            "active"
        );
    }
);


closeFilterBtn.addEventListener(
    "click",
    () => {
        filterOverlay.classList.remove(
            "active"
        );
    }
);


filterOverlay.addEventListener(
    "click",
    event => {
        if (
            event.target
            === filterOverlay
        ) {
            filterOverlay.classList.remove(
                "active"
            );
        }
    }
);
 
function formatPrice(price) {
    return Number(price)
        .toLocaleString("vi-VN") + "đ";
}
 
function getStatus(product) {
    if (
        product.status
        === "PREORDER"
    ) {
        return `
            <span class="product-status preorder">
                Pre-order
            </span>
        `;
    }

    return `
        <span class="product-status in-stock">
            Có sẵn
        </span>
    `;
}
 
function getProductTags(product) {

    if (
        !product.tags
        ||
        product.tags.length === 0
    ) {
        return "";
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
 
function getProductImage(product) {
    if (product.image) {
        return `
            <img
                src="${product.image}"
                alt="${product.product_name}"

                onerror="
                    this.style.display='none';
                    this.nextElementSibling.style.display='flex';
                "
            >

            <div
                class="product-image-placeholder"
                style="display: none;"
            >
                <i class='bx bx-image'></i>
            </div>
        `;
    }

    return `
        <div class="product-image-placeholder">
            <i class='bx bx-image'></i>
        </div>
    `;
}
 
function renderProducts(products) {
    productGrid.innerHTML = "";

    loadingState.style.display =
        "none";

    productCount.textContent =
        products.length;


    if (hasSearchOrFilter) {
        resultInfo.style.display =
            "block";
    } else {
        resultInfo.style.display =
            "none";
    }


    if (products.length === 0) {
        emptyState.style.display =
            "block";

        return;
    }


    emptyState.style.display =
        "none";


    products.forEach(product => {
        const card =
            document.createElement(
                "div"
            );

        card.className =
            "product-card";


        card.innerHTML = `
            <div class="product-image">

                ${getStatus(product)}

                ${getProductImage(product)}

            </div>


            <div class="product-info">

                <div class="product-tags">
                    ${getProductTags(product)}
                </div>

                <div class="product-name">
                    ${product.product_name}
                </div>

                <div class="product-price-row">

                    <div class="product-price">
                        ${formatPrice(product.price)}
                    </div>

                <button
                    class="add-cart
                        ${product.status === "PREORDER"
                                && !product.preorder_available
                                ? "disabled"
                                : ""
                            }
                    "
                    type="button"

                    ${product.status === "PREORDER"
                                && !product.preorder_available
                                ? "disabled"
                                : ""
                            }
                >
                    <i class='bx bx-cart-add'></i>
                </button>

                </div>

            </div>
        `;


        card.addEventListener(
            "click",
            event => {
                if (
                    event.target.closest(
                        ".add-cart"
                    )
                ) {
                    return;
                }

                window.location.href =
                    `/products/${product.product_id}`;
            }
        );

        function animateToCart(productCard) {
            const productImage =
                productCard.querySelector(
                    ".product-image img"
                );

            const cartIcon =
                document.querySelector(
                    '.header-icon[href="/cart"]'
                );

            if (
                !productImage
                ||
                !cartIcon
            ) {
                return;
            }

            const imageRect =
                productImage.getBoundingClientRect();

            const cartRect =
                cartIcon.getBoundingClientRect();


            const flyingImage =
                productImage.cloneNode(true);

            flyingImage.classList.add(
                "flying-to-cart"
            );


            flyingImage.style.left =
                `${imageRect.left}px`;

            flyingImage.style.top =
                `${imageRect.top}px`;

            flyingImage.style.width =
                `${imageRect.width}px`;

            flyingImage.style.height =
                `${imageRect.height}px`;


            document.body.appendChild(
                flyingImage
            );


            requestAnimationFrame(() => {

                flyingImage.style.left =
                    `${cartRect.left
                    + cartRect.width / 2
                    - 20
                    }px`;

                flyingImage.style.top =
                    `${cartRect.top
                    + cartRect.height / 2
                    - 20
                    }px`;

                flyingImage.style.width =
                    "40px";

                flyingImage.style.height =
                    "40px";

                flyingImage.style.opacity =
                    "0.3";

                flyingImage.style.transform =
                    "rotate(12deg)";
            });


            setTimeout(() => {
                flyingImage.remove();

                cartIcon.classList.add(
                    "cart-bounce"
                );

                setTimeout(() => {
                    cartIcon.classList.remove(
                        "cart-bounce"
                    );
                }, 450);

            }, 700);
        }


        // =========================================
        // ADD TO CART
        // =========================================

        const addCartBtn =
    card.querySelector(".add-cart");


addCartBtn.addEventListener(
    "click",
    async event => {

        event.stopPropagation();


        // =========================================
        // PREORDER ĐÃ HẾT / CHƯA MỞ
        // =========================================

        if (
            product.status === "PREORDER"
            && !product.preorder_available
        ) {
            return;
        }


        const token =
            localStorage.getItem(
                "access_token"
            );


        // =========================================
        // CHƯA ĐĂNG NHẬP
        // =========================================

        if (!token) {

            localStorage.setItem(
                "redirect_after_login",
                window.location.pathname
                + window.location.search
                + window.location.hash
            );

            window.location.href =
                "/login";

            return;
        }


        // =========================================
        // KIỂM TRA PREORDER ID
        // =========================================

        if (
            product.status === "PREORDER"
            && !product.preorder_id
        ) {
            console.error(
                "Sản phẩm preorder không có preorder_id:",
                product
            );

            return;
        }


        // =========================================
        // LẤY CART
        // =========================================

        let cart =
            JSON.parse(
                localStorage.getItem(
                    "verdia_cart"
                )
            ) || [];


        const existingItem =
            cart.find(
                item =>
                    Number(item.product_id)
                    === Number(product.product_id)
            );


        // =========================================
        // SẢN PHẨM ĐÃ CÓ
        // =========================================

        if (existingItem) {

            existingItem.quantity += 1;

            // Đồng bộ preorder_id mới nhất
            if (
                product.status === "PREORDER"
            ) {
                existingItem.preorder_id =
                    product.preorder_id;
            }

        } else {

            // =====================================
            // THÊM SẢN PHẨM MỚI
            // =====================================

            cart.push({

                cart_item_id:
                    Date.now(),

                product_id:
                    product.product_id,

                product_name:
                    product.product_name,

                price:
                    Number(product.price),

                quantity:
                    1,

                status:
                    product.status,

                preorder_id:
                    product.status === "PREORDER"
                        ? product.preorder_id
                        : null,

                tags:
                    product.tags
                        ? product.tags.map(
                            tag => tag.name
                        )
                        : [],

                image:
                    product.image || ""
            });
        }


        // =========================================
        // SAVE CART
        // =========================================

        localStorage.setItem(
            "verdia_cart",
            JSON.stringify(cart)
        );


        // =========================================
        // ANIMATION
        // =========================================

        animateToCart(card);
    }
);


        productGrid.appendChild(
            card
        );
    });
}
 
async function loadProducts() {
    loadingState.style.display =
        "block";

    emptyState.style.display =
        "none";

    productGrid.innerHTML = "";


    const params =
        new URLSearchParams();


    const keyword =
        keywordInput.value.trim();

    if (keyword) {
        params.append(
            "keyword",
            keyword
        );
    }


    const status =
        document.querySelector(
            'input[name="status"]:checked'
        ).value;

    if (status) {
        params.append(
            "status",
            status
        );
    }


    const minPrice =
        minPriceInput.value;

    if (minPrice !== "") {
        params.append(
            "min_price",
            minPrice
        );
    }


    const maxPrice =
        maxPriceInput.value;

    if (maxPrice !== "") {
        params.append(
            "max_price",
            maxPrice
        );
    }


    const categoryId =
        categorySelect.value;

    if (categoryId) {
        params.append(
            "category_id",
            categoryId
        );
    }


    const subCategoryId =
        subCategorySelect.value;

    if (subCategoryId) {
        params.append(
            "sub_category_id",
            subCategoryId
        );
    }


    document.querySelectorAll(
        ".tag-checkbox:checked"
    ).forEach(tag => {
        params.append(
            "tag_ids",
            tag.value
        );
    });


    try {
        const response =
            await fetch(
                `/api/products?${params.toString()}`
            );

        const result =
            await response.json();


        if (!response.ok) {
            throw new Error(
                result.message
                ||
                result.error
                ||
                "Không thể lấy sản phẩm"
            );
        }


        currentProducts =
            result.data?.products
            ||
            result.products
            ||
            [];


        applySort();

    } catch (error) {
        console.error(error);

        currentProducts = [];

        loadingState.style.display =
            "none";

        emptyState.style.display =
            "block";

        productCount.textContent =
            "0";
    }
}
 
async function loadCategories() {
    try {
        const response =
            await fetch(
                "/api/products/categories"
            );

        const result =
            await response.json();


        if (!response.ok) {
            throw new Error(
                result.message
                ||
                "Không thể tải danh mục"
            );
        }


        const categories =
            result.data?.categories
            ||
            result.categories
            ||
            [];


        categorySelect.innerHTML = `
            <option value="">
                Tất cả danh mục
            </option>
        `;


        categories.forEach(
            category => {
                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    category.category_id;

                option.textContent =
                    getCategoryLabel(
                        category.name
                    );

                categorySelect.appendChild(
                    option
                );
            }
        );

    } catch (error) {
        console.error(error);

        categorySelect.innerHTML = `
            <option value="">
                Không thể tải danh mục
            </option>
        `;
    }
}
 
function getCategoryLabel(name) {
    const labels = {
        GAME: "Game",
        ANIMATION: "Animation",
        COMIC: "Comic"
    };

    return labels[name] || name;
}
 
function getSubCategoryLabel(name) {
    const labels = {
        ANIME: "Anime",
        DONGHUA: "Donghua",
        AENI: "Aeni",

        MANGA: "Manga",
        MANHUA: "Manhua",
        MANHWA: "Manhwa",

        GAME: "Game"
    };

    return labels[name] || name;
}
 
async function loadSubCategories(
    categoryId
) {
    resetSubCategory();
    resetTags();


    if (!categoryId) {
        return;
    }


    subCategoryGroup.style.display =
        "block";


    subCategorySelect.innerHTML = `
        <option value="">
            Đang tải...
        </option>
    `;


    try {
        const response =
            await fetch(
                `/api/products/categories/${categoryId}/sub-categories`
            );

        const result =
            await response.json();


        if (!response.ok) {
            throw new Error(
                result.message
                ||
                "Không thể tải danh mục phụ"
            );
        }


        const subCategories =
            result.data?.sub_categories
            ||
            result.sub_categories
            ||
            [];


        subCategorySelect.innerHTML = `
            <option value="">
                Tất cả
            </option>
        `;


        subCategories.forEach(
            subCategory => {
                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    subCategory.sub_category_id;

                option.textContent =
                    getSubCategoryLabel(
                        subCategory.name
                    );

                subCategorySelect.appendChild(
                    option
                );
            }
        );
         if (
            subCategories.length === 1
        ) {
            subCategorySelect.value =
                subCategories[0]
                    .sub_category_id;

            await loadTags(
                subCategories[0]
                    .sub_category_id
            );
        }

    } catch (error) {
        console.error(error);

        subCategorySelect.innerHTML = `
            <option value="">
                Không thể tải danh mục phụ
            </option>
        `;
    }
}
 
function resetSubCategory() {
    subCategorySelect.innerHTML = `
        <option value="">
            Tất cả
        </option>
    `;

    subCategoryGroup.style.display =
        "none";
}
 
function resetTags() {
    tagGroup.style.display =
        "none";

    tagFilter.innerHTML = `
        <p class="filter-loading">
            Hãy chọn danh mục phụ
        </p>
    `;
}
 
async function loadTags(
    subCategoryId
) {
    resetTags();


    if (!subCategoryId) {
        return;
    }


    tagGroup.style.display =
        "block";


    tagFilter.innerHTML = `
        <p class="filter-loading">
            Đang tải thẻ...
        </p>
    `;


    try {
        const response =
            await fetch(
                `/api/products/sub-categories/${subCategoryId}/tags`
            );

        const result =
            await response.json();


        if (!response.ok) {
            throw new Error(
                result.message
                ||
                "Không thể tải thẻ"
            );
        }


        const tags =
            result.data?.tags
            ||
            result.tags
            ||
            [];


        tagFilter.innerHTML = "";


        if (tags.length === 0) {
            tagFilter.innerHTML = `
                <p class="filter-loading">
                    Chưa có thẻ trong danh mục này
                </p>
            `;

            return;
        }


        tags.forEach(tag => {
            const label =
                document.createElement(
                    "label"
                );

            label.innerHTML = `
                <input
                    type="checkbox"
                    class="tag-checkbox"
                    value="${tag.tag_id}"
                >

                <span>
                    ${tag.name}
                </span>
            `;

            tagFilter.appendChild(
                label
            );
        });

    } catch (error) {
        console.error(error);

        tagFilter.innerHTML = `
            <p class="filter-loading">
                Không thể tải thẻ
            </p>
        `;
    }
}
 
categorySelect.addEventListener(
    "change",
    async () => {
        const categoryId =
            categorySelect.value;

        await loadSubCategories(
            categoryId
        );
    }
);
 
subCategorySelect.addEventListener(
    "change",
    async () => {
        const subCategoryId =
            subCategorySelect.value;

        await loadTags(
            subCategoryId
        );
    }
);
 
function applySort() {
    const sort =
        sortSelect.value;

    const products =
        [...currentProducts];


    // =========================================
    // SORT THEO LỰA CHỌN
    // =========================================

    if (sort === "price-asc") {
        products.sort(
            (a, b) =>
                Number(a.price)
                -
                Number(b.price)
        );
    }


    if (sort === "price-desc") {
        products.sort(
            (a, b) =>
                Number(b.price)
                -
                Number(a.price)
        );
    }


    if (sort === "name-asc") {
        products.sort(
            (a, b) =>
                a.product_name.localeCompare(
                    b.product_name,
                    "vi"
                )
        );
    }


    if (sort === "name-desc") {
        products.sort(
            (a, b) =>
                b.product_name.localeCompare(
                    a.product_name,
                    "vi"
                )
        );
    }


    // =========================================
    // PREORDER HẾT ĐỢT LUÔN XUỐNG CUỐI
    // =========================================

    products.sort(
        (a, b) => {

            const aUnavailable =
                a.status === "PREORDER"
                && !a.preorder_available;

            const bUnavailable =
                b.status === "PREORDER"
                && !b.preorder_available;


            if (
                aUnavailable
                ===
                bUnavailable
            ) {
                return 0;
            }


            return aUnavailable
                ? 1
                : -1;
        }
    );


    renderProducts(
        products
    );
}
 
searchBtn.addEventListener(
    "click",
    () => {
        hasSearchOrFilter = true;

        loadProducts();
    }
);


keywordInput.addEventListener(
    "keydown",
    event => {
        if (event.key === "Enter") {
            hasSearchOrFilter = true;

            loadProducts();
        }
    }
);
 
applyFilterBtn.addEventListener(
    "click",
    () => {
        hasSearchOrFilter = true;

        filterOverlay.classList.remove(
            "active"
        );

        loadProducts();
    }
);
 
clearFilterBtn.addEventListener(
    "click",
    () => {
        minPriceInput.value = "";

        maxPriceInput.value = "";


        document.querySelector(
            'input[name="status"][value=""]'
        ).checked = true;


        categorySelect.value = "";


        resetSubCategory();

        resetTags();


        hasSearchOrFilter =
            keywordInput.value.trim()
            !== "";


        filterOverlay.classList.remove(
            "active"
        );


        loadProducts();
    }
);
 
sortSelect.addEventListener(
    "change",
    () => {
        applySort();
    }
);
 
const urlParams =
    new URLSearchParams(
        window.location.search
    );


const urlStatus =
    urlParams.get("status");


if (
    urlStatus === "PREORDER"
    ||
    urlStatus === "IN_STOCK"
) {
    const statusRadio =
        document.querySelector(
            `input[name="status"][value="${urlStatus}"]`
        );


    if (statusRadio) {
        statusRadio.checked = true;

        hasSearchOrFilter = true;
    }
}
 
async function initProducts() {
    await restoreOAuthLogin();

    loadCategories();
    loadProducts();
}

initProducts();