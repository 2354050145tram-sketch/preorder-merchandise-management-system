document.addEventListener("DOMContentLoaded", () => {
    // 1. Formatters & Helpers
    const formatCurrency = (val) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);
    const formatNumber = (val) => new Intl.NumberFormat('vi-VN').format(val || 0);
    const escapeHTML = (str) => {
        if (!str) return "";
        return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    };

    // 2. Fetch Wrapper có JWT Token
    async function apiFetch(url) {
        const token = localStorage.getItem("token")
            || localStorage.getItem("access_token")
            || localStorage.getItem("jwt_token")
            || sessionStorage.getItem("token")
            || sessionStorage.getItem("access_token");

        const headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        try {
            const res = await fetch(url, { headers });
            if (res.status === 401 || res.status === 403) return null;
            const json = await res.json();
            return json.data ? json.data : json;
        } catch (error) {
            console.error(`Fetch lỗi: ${url}`, error);
            return null;
        }
    }

    let revenueChartInstance = null;
    let orderChartInstance = null;

    // 3. Load Summary (5 thẻ trên cùng)
    async function loadSummary() {
        const res = await apiFetch("/api/analytics/dashboard");
        if (res && res.dashboard) {
            const d = res.dashboard;
            document.getElementById("metric-revenue").innerText = formatCurrency(d.total_revenue);
            document.getElementById("metric-orders").innerText = formatNumber(d.total_orders);
            document.getElementById("metric-customers").innerText = formatNumber(d.total_customers);
            document.getElementById("metric-products").innerText = formatNumber(d.total_products);
            document.getElementById("metric-low-stock").innerText = formatNumber(d.low_stock_count);
        }
    }

    // 4. Biến động Doanh thu & Dòng tiền (Nhóm theo Tháng / Ngày / Năm)
    async function loadRevenueReport(startDate, endDate, groupMode = "month") {
        let url = "/api/analytics/revenue";
        const params = new URLSearchParams();
        if (startDate) params.append("start_date", startDate);
        if (endDate) params.append("end_date", endDate);
        if (params.toString()) url += `?${params.toString()}`;

        const res = await apiFetch(url);
        if (!res || !res.revenue) return;

        let rawList = res.revenue;
        let groupedData = {};

        rawList.forEach(item => {
            if (!item.date) return;
            const d = new Date(item.date);
            let label = "";

            if (groupMode === "day") {
                label = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
            } else if (groupMode === "year") {
                label = `${d.getFullYear()}`;
            } else {
                label = `Thg ${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
            }

            if (!groupedData[label]) {
                groupedData[label] = { revenue: 0, paid: 0, refunded: 0 };
            }

            groupedData[label].revenue += item.revenue || 0;
            groupedData[label].paid += item.paid || 0;
            groupedData[label].refunded += item.refunded || 0;
        });

        const labels = Object.keys(groupedData);
        const revenues = labels.map(k => groupedData[k].revenue);
        const paids = labels.map(k => groupedData[k].paid);
        const refunds = labels.map(k => groupedData[k].refunded);

        const ctx = document.getElementById("revenueChart").getContext("2d");
        if (revenueChartInstance) revenueChartInstance.destroy();

        revenueChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels,
                datasets: [
                    {
                        label: "Doanh thu thực",
                        data: revenues,
                        borderColor: "#b88a45",
                        backgroundColor: "rgba(184, 138, 69, 0.08)",
                        fill: true,
                        tension: 0.3,
                        borderWidth: 2.5,
                        pointRadius: labels.length > 25 ? 0 : 3,
                        pointHoverRadius: 5
                    },
                    {
                        label: "Đã thanh toán",
                        data: paids,
                        borderColor: "#4f7558",
                        backgroundColor: "transparent",
                        borderDash: [4, 4],
                        tension: 0.3,
                        borderWidth: 1.5,
                        pointRadius: labels.length > 25 ? 0 : 2,
                        pointHoverRadius: 4
                    },
                    {
                        label: "Hoàn tiền",
                        data: refunds,
                        borderColor: "#bb5656",
                        backgroundColor: "transparent",
                        tension: 0.3,
                        borderWidth: 1.5,
                        pointRadius: labels.length > 25 ? 0 : 2,
                        pointHoverRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { position: "top", labels: { boxWidth: 12, font: { family: "Poppins", size: 9.5 } } },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
                        }
                    }
                },
                scales: {
                    y: {
                        ticks: {
                            callback: (v) => v >= 1000000 ? `${(v / 1000000).toFixed(1)}M` : (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v),
                            font: { family: "Poppins", size: 8.5 }
                        },
                        grid: { color: "rgba(0,0,0,0.04)" }
                    },
                    x: {
                        ticks: { font: { family: "Poppins", size: 8.5 }, autoSkip: true, maxTicksLimit: 12 },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // 5. Biểu đồ Trạng thái Đơn hàng (4 trạng thái)
    async function loadOrderStats() {
        const res = await apiFetch("/api/analytics/orders");
        if (!res || !res.orders) return;

        const targetStatuses = ["HOÀN THÀNH", "ĐÃ XÁC NHẬN", "ĐÃ ĐẶT CỌC", "ĐÃ HỦY"];
        const statusColors = {
            "HOÀN THÀNH": "#4f7558",
            "ĐÃ XÁC NHẬN": "#b88a45",
            "ĐÃ ĐẶT CỌC": "#39515e",
            "ĐÃ HỦY": "#bb5656"
        };

        const filteredStats = targetStatuses.map(status => {
            const found = res.orders.find(o => (o.order_status || "").trim().toUpperCase() === status);
            return {
                status: status,
                total: found ? found.total : 0
            };
        }).filter(item => item.total > 0);

        const labels = filteredStats.map(o => o.status);
        const data = filteredStats.map(o => o.total);
        const backgroundColors = filteredStats.map(o => statusColors[o.status] || "#7e898f");

        const ctx = document.getElementById("orderStatusChart").getContext("2d");
        if (orderChartInstance) orderChartInstance.destroy();

        orderChartInstance = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels,
                datasets: [{
                    data,
                    backgroundColor: backgroundColors,
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom", labels: { boxWidth: 10, font: { family: "Poppins", size: 8.5 } } }
                },
                cutout: "68%"
            }
        });
    }

    // 6. Top sản phẩm bán chạy
    async function loadBestSellers() {
        const res = await apiFetch("/api/analytics/products/best-selling?limit=10");
        const tbody = document.getElementById("table-best-sellers");
        if (!tbody) return;

        const list = res?.products || (Array.isArray(res) ? res : []);
        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--admin-muted); padding: 12px;">Không có dữ liệu</td></tr>`;
            return;
        }

        tbody.innerHTML = list.map(p => `
            <tr>
                <td>#${p.product_id}</td>
                <td><strong>${escapeHTML(p.product_name)}</strong></td>
                <td style="text-align: right; font-weight: 600; color: var(--admin-gold);">${formatNumber(p.quantity_sold)}</td>
            </tr>
        `).join("");
    }

    // 7. Cảnh báo kho hàng (KẾT NỐI VỚI HÀM get_low_stock_products BACKEND)
    async function loadLowStock() {
        const res = await apiFetch("/api/analytics/inventory/low-stock");
        const tbody = document.getElementById("table-low-stock");
        if (!tbody) return;

        // Bắt linh hoạt các dạng key trả về từ backend: res.products hoặc res.low_stock_products hoặc mảng trực tiếp
        const list = res?.products || res?.low_stock_products || (Array.isArray(res) ? res : []);
        
        if (!list || list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--admin-muted); padding: 12px;">Kho hàng an toàn</td></tr>`;
            return;
        }

        tbody.innerHTML = list.map(p => {
            const qty = Number(p.quantity || 0);
            const isOut = qty === 0 || p.status === 'HẾT HÀNG';
            const statusClass = isOut ? 'badge-danger' : 'badge-warning';
            const statusText = isOut ? 'HẾT HÀNG' : 'SẮP HẾT HÀNG';

            return `
                <tr>
                    <td>#${p.product_id}</td>
                    <td><strong>${escapeHTML(p.product_name)}</strong></td>
                    <td><strong style="color: var(--admin-danger);">${formatNumber(qty)}</strong></td>
                    <td>
                        <span class="badge-status ${statusClass}">
                            ${statusText}
                        </span>
                    </td>
                </tr>
            `;
        }).join("");
    }

    // 8. Top Khách hàng VIP
    async function loadTopCustomers() {
        const res = await apiFetch("/api/analytics/customers?limit=10");
        const tbody = document.getElementById("table-top-customers");
        if (!tbody) return;

        const list = res?.customers?.top_customers || res?.top_customers || (Array.isArray(res) ? res : []);
        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--admin-muted); padding: 12px;">Không có dữ liệu</td></tr>`;
            return;
        }

        tbody.innerHTML = list.map(c => `
            <tr>
                <td>#${c.user_id}</td>
                <td><strong>${escapeHTML(c.username)}</strong></td>
                <td>${formatNumber(c.total_orders)} đơn</td>
                <td>${formatCurrency(c.total_paid)}</td>
                <td style="color: var(--admin-danger);">${formatCurrency(c.total_refunded)}</td>
                <td style="text-align: right; font-weight: 600; color: var(--admin-success);">${formatCurrency(c.total_spent)}</td>
            </tr>
        `).join("");
    }

    // 9. Xử lý Bộ lọc Ngày / Tháng / Năm
    const filterMode = document.getElementById("filter-mode");
    const wrapMonth = document.getElementById("wrapper-month");
    const wrapDay = document.getElementById("wrapper-day");
    const wrapYear = document.getElementById("wrapper-year");

    if (filterMode) {
        filterMode.addEventListener("change", (e) => {
            const mode = e.target.value;
            if (wrapMonth) wrapMonth.style.display = mode === "month" ? "block" : "none";
            if (wrapDay) wrapDay.style.display = mode === "day" ? "flex" : "none";
            if (wrapYear) wrapYear.style.display = mode === "year" ? "block" : "none";
        });
    }

    function applyCurrentFilter() {
        if (!filterMode) return;
        const mode = filterMode.value;
        let startDate = "";
        let endDate = "";

        if (mode === "month") {
            const monthVal = document.getElementById("input-month")?.value;
            if (monthVal) {
                const [y, m] = monthVal.split("-");
                startDate = `${y}-${m}-01T00:00:00`;
                const lastDay = new Date(y, m, 0).getDate();
                endDate = `${y}-${m}-${lastDay}T23:59:59`;
            }
            loadRevenueReport(startDate, endDate, "day");
        } else if (mode === "day") {
            const s = document.getElementById("date-range-start")?.value;
            const e = document.getElementById("date-range-end")?.value;
            if (s) startDate = `${s}T00:00:00`;
            if (e) endDate = `${e}T23:59:59`;
            loadRevenueReport(startDate, endDate, "day");
        } else if (mode === "year") {
            const yearVal = document.getElementById("input-year")?.value || "2026";
            startDate = `${yearVal}-01-01T00:00:00`;
            endDate = `${yearVal}-12-31T23:59:59`;
            loadRevenueReport(startDate, endDate, "month");
        }
    }

    document.getElementById("btn-apply-filter")?.addEventListener("click", applyCurrentFilter);
    document.getElementById("btn-refresh-all")?.addEventListener("click", () => {
        loadSummary();
        applyCurrentFilter();
        loadOrderStats();
        loadBestSellers();
        loadLowStock();
        loadTopCustomers();
    });

    // 10. Khởi chạy khi load trang
    loadSummary();
    applyCurrentFilter();
    loadOrderStats();
    loadBestSellers();
    loadLowStock();
    loadTopCustomers();
});