const authArea =
    document.getElementById("auth-area");


function getSavedUserName() {

    const savedUser =
        localStorage.getItem("user");

    if (!savedUser) {
        return "Tài khoản";
    }

    try {

        const user =
            JSON.parse(savedUser);

        return (
            user.username
            || user.email
            || "Tài khoản"
        );

    } catch (error) {

        return "Tài khoản";
    }
}


function showLoginLink() {

    if (!authArea) {
        return;
    }

    authArea.innerHTML = `
        <a
            href="/login"
            class="auth-link"
        >
            Verdia Store
        </a>
    `;
}


function showProfileIcon() {

    if (!authArea) {
        return;
    }

    const username =
        getSavedUserName();

    authArea.innerHTML = `
        <a
            href="/profile"
            class="profile-header-icon"
            aria-label="Tài khoản"
            title="${username}"
        >
            <i class='bx bx-user'></i>
        </a>
    `;
}


async function restoreOAuthSession() {

    if (
        localStorage.getItem(
            "access_token"
        )
    ) {
        return true;
    }

    try {

        const response =
            await fetch(
                "/api/users/oauth/session"
            );

        if (!response.ok) {
            return false;
        }

        const result =
            await response.json();

        if (
            !result.data
            || !result.data.access_token
        ) {
            return false;
        }

        localStorage.setItem(
            "access_token",
            result.data.access_token
        );

        if (
            result.data.refresh_token
        ) {
            localStorage.setItem(
                "refresh_token",
                result.data.refresh_token
            );
        }

        if (result.data.user) {
            localStorage.setItem(
                "user",
                JSON.stringify(
                    result.data.user
                )
            );
        }

        return true;

    } catch (error) {

        return false;
    }
}


async function renderAuthHeader() {

    if (!authArea) {
        return;
    }

    let token =
        localStorage.getItem(
            "access_token"
        );

    if (!token) {

        const restored =
            await restoreOAuthSession();

        if (restored) {
            token =
                localStorage.getItem(
                    "access_token"
                );
        }
    }

    if (token) {
        showProfileIcon();
        return;
    }

    showLoginLink();
}


renderAuthHeader();
