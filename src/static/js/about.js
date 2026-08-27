document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadAboutProducts();

    }
);


async function loadAboutProducts() {

    const grid =
        document.getElementById(
            "about-product-grid"
        );


    if (!grid) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/products"
            );


        if (!response.ok) {

            throw new Error(
                "Không thể tải sản phẩm"
            );

        }


        const result =
            await response.json();


        const products =
            result.data?.products
            ||
            result.products
            ||
            [];


        // =========================================
        // CHỈ LẤY SẢN PHẨM ĐANG CÓ THỂ MUA
        // =========================================

        const availableProducts =
            products.filter(
                product => {

                    // Hàng có sẵn
                    if (
                        product.status
                        === "IN_STOCK"
                    ) {

                        return true;

                    }


                    // Pre-order phải còn đợt đang mở
                    if (
                        product.status
                        === "PREORDER"
                        &&
                        product.preorder_available
                        === true
                    ) {

                        return true;

                    }


                    return false;

                }
            );


        // =========================================
        // LẤY TỐI ĐA 4 SẢN PHẨM
        // =========================================

        const displayProducts =
            availableProducts.slice(
                0,
                4
            );


        if (
            displayProducts.length
            === 0
        ) {

            grid.innerHTML = `
                <div class="about-product-loading">
                    Hiện chưa có sản phẩm đang mở bán.
                </div>
            `;


            return;

        }


        grid.innerHTML =
            displayProducts
                .map(
                    product =>
                        createAboutProductCard(
                            product
                        )
                )
                .join("");


    } catch (error) {

        console.error(
            "Lỗi tải sản phẩm About:",
            error
        );


        grid.innerHTML = `
            <div class="about-product-loading">
                Không thể tải sản phẩm.
            </div>
        `;

    }

}


 
function createAboutProductCard(
    product
) {

    const isPreorder =
        product.status
        === "PREORDER";


    const statusText =
        isPreorder
            ? "PRE-ORDER"
            : "CÓ SẴN";


    const statusClass =
        isPreorder
            ? "preorder"
            : "instock";


    const price =
        Number(
            product.price || 0
        ).toLocaleString(
            "vi-VN"
        ) + "đ";


    const image =
        product.image || "";


    return `
        <a
            href="/products/${product.product_id}"
            class="about-product-card"
        >

            <div class="about-product-image">

                ${
                    image
                        ? `
                            <img
                                src="${image}"
                                alt="${escapeHtml(
                                    product.product_name
                                )}"
                                loading="lazy"

                                onerror="
                                    this.style.display='none';
                                    this.nextElementSibling.style.display='flex';
                                "
                            >

                            <div
                                class="about-product-placeholder"
                                style="display: none;"
                            >
                                <i class='bx bx-image'></i>
                            </div>
                        `
                        : `
                            <div
                                class="about-product-placeholder"
                            >
                                <i class='bx bx-image'></i>
                            </div>
                        `
                }


                <span
                    class="
                        about-product-status
                        ${statusClass}
                    "
                >
                    ${statusText}
                </span>

            </div>


            <div class="about-product-info">

                <h3>
                    ${escapeHtml(
                        product.product_name
                    )}
                </h3>


                <strong>
                    ${price}
                </strong>

            </div>

        </a>
    `;

}


 
function escapeHtml(value) {

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