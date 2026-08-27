document.addEventListener(
    "DOMContentLoaded",
    () => {

        initAdmin();

    }
);



function initAdmin() {

    const token =
        localStorage.getItem(
            "access_token"
        );


    const user =
        JSON.parse(
            localStorage.getItem(
                "user"
            )
            ||
            "null"
        );

    if (!token) {

        localStorage.setItem(
            "redirect_after_login",
            window.location.pathname
        );


        window.location.href =
            "/login";

        return;

    }


    fillAdminInformation(
        user
    );


    bindAdminCommonEvents();


    restoreSidebarState();

}



function fillAdminInformation(
    user
) {

    const username =
        document.getElementById(
            "admin-username"
        );


    if (!username) {
        return;
    }


    username.textContent =
        user?.username
        ||
        "Admin";

}



function bindAdminCommonEvents() {

    const logoutBtn =
        document.getElementById(
            "admin-logout-btn"
        );


    const sidebarToggle =
        document.getElementById(
            "admin-sidebar-toggle"
        );


    if (logoutBtn) {

        logoutBtn.addEventListener(
            "click",
            logoutAdmin
        );

    }


    if (sidebarToggle) {

        sidebarToggle.addEventListener(
            "click",
            toggleAdminSidebar
        );

    }

}



function toggleAdminSidebar() {

    const shell =
        document.querySelector(
            ".admin-shell"
        );


    if (!shell) {
        return;
    }


    shell.classList.toggle(
        "sidebar-collapsed"
    );


    const collapsed =
        shell.classList.contains(
            "sidebar-collapsed"
        );


    localStorage.setItem(
        "admin_sidebar_collapsed",
        collapsed
            ? "1"
            : "0"
    );

}


function restoreSidebarState() {

    const shell =
        document.querySelector(
            ".admin-shell"
        );


    if (!shell) {
        return;
    }


    const collapsed =
        localStorage.getItem(
            "admin_sidebar_collapsed"
        );


    if (
        collapsed === "1"
    ) {

        shell.classList.add(
            "sidebar-collapsed"
        );

    }

}



function logoutAdmin() {

    localStorage.removeItem(
        "access_token"
    );


    localStorage.removeItem(
        "refresh_token"
    );


    localStorage.removeItem(
        "user"
    );


    localStorage.removeItem(
        "admin_sidebar_collapsed"
    );


    window.location.href =
        "/login";

}



function showAdminToast(
    message
) {

    const toast =
        document.getElementById(
            "admin-toast"
        );


    if (!toast) {
        return;
    }


    toast.textContent =
        message;


    toast.classList.add(
        "show"
    );


    window.clearTimeout(
        toast.hideTimer
    );


    toast.hideTimer =
        window.setTimeout(
            () => {

                toast.classList.remove(
                    "show"
                );

            },
            2500
        );

}



function formatAdminPrice(
    value
) {

    return Number(
        value || 0
    ).toLocaleString(
        "vi-VN"
    ) + "đ";

}


function escapeAdminHTML(
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