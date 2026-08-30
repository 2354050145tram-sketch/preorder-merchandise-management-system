const container = document.querySelector('.container');

const registerBtn = document.querySelector('.register-btn');

const loginBtn = document.querySelector('.login-btn');


 
registerBtn.addEventListener('click', () => {

    container.classList.add('active');

});


loginBtn.addEventListener('click', () => {

    container.classList.remove('active');

});


 
const togglePasswords =
    document.querySelectorAll('.toggle-password');


togglePasswords.forEach(icon => {

    icon.addEventListener('click', () => {

        const input =
            document.getElementById(
                icon.dataset.target
            );

        if (input.type === 'password') {

            input.type = 'text';

            icon.classList.remove(
                'bxs-hide'
            );

            icon.classList.add(
                'bxs-show'
            );

        } else {

            input.type = 'password';

            icon.classList.remove(
                'bxs-show'
            );

            icon.classList.add(
                'bxs-hide'
            );
        }

    });

});


 
const rememberAccount =
    document.getElementById(
        'remember-account'
    );

const loginUsername =
    document.getElementById(
        'login-username'
    );


const savedUsername =
    localStorage.getItem(
        'remembered_username'
    );


if (savedUsername) {

    loginUsername.value =
        savedUsername;

    rememberAccount.checked =
        true;
}


rememberAccount.addEventListener(
    'change',
    () => {

        if (rememberAccount.checked) {

            localStorage.setItem(
                'remembered_username',
                loginUsername.value
            );

        } else {

            localStorage.removeItem(
                'remembered_username'
            );
        }

    }
);


loginUsername.addEventListener(
    'input',
    () => {

        if (rememberAccount.checked) {

            localStorage.setItem(
                'remembered_username',
                loginUsername.value
            );
        }

    }
);


 
function redirectAfterAuth(user) {

    localStorage.removeItem(
        'redirect_after_login'
    );
 
    if (
        Number(user?.role_id) === 0
    ) {

        window.location.href =
            '/admin/dashboard';

        return;
    }
 
    window.location.href =
        '/products';
}

 
const loginForm =
    document.getElementById(
        'login-form'
    );


loginForm.addEventListener(
    'submit',
    async event => {

        event.preventDefault();


        const login =
            loginUsername.value.trim();

        const password =
            document.getElementById(
                'login-password'
            ).value;


        try {

            const response =
                await fetch(
                    '/api/users/login',
                    {
                        method: 'POST',

                        headers: {
                            'Content-Type':
                                'application/json'
                        },

                        body:
                            JSON.stringify({
                                login: login,
                                password: password
                            })
                    }
                );


            const result =
                await response.json();


            if (!response.ok) {

                alert(
                    result.message
                    ||
                    'Đăng nhập thất bại'
                );

                return;
            }
 
            localStorage.setItem(
                'access_token',
                result.data.access_token
            );

            localStorage.setItem(
                'refresh_token',
                result.data.refresh_token
            );


            localStorage.setItem(
                'user',
                JSON.stringify(
                    result.data.user
                )
            );
 
            if (rememberAccount.checked) {

                localStorage.setItem(
                    'remembered_username',
                    login
                );

            } else {

                localStorage.removeItem(
                    'remembered_username'
                );
            }
 
            redirectAfterAuth(result.data.user);

        } catch (error) {

            console.error(
                'LOGIN ERROR:',
                error
            );

            alert(
                'Có lỗi xảy ra khi đăng nhập'
            );
        }

    }
);


 
const registerForm =
    document.getElementById(
        'register-form'
    );


registerForm.addEventListener(
    'submit',
    async event => {

        event.preventDefault();


        const data = {

            full_name:
                registerForm
                    .querySelector(
                        '[name="full_name"]'
                    )
                    .value
                    .trim(),

            username:
                registerForm
                    .querySelector(
                        '[name="username"]'
                    )
                    .value
                    .trim(),

            email:
                registerForm
                    .querySelector(
                        '[name="email"]'
                    )
                    .value
                    .trim(),

            phone_num:
                registerForm
                    .querySelector(
                        '[name="phone_num"]'
                    )
                    .value
                    .trim(),

            address:
                registerForm
                    .querySelector(
                        '[name="address"]'
                    )
                    .value
                    .trim(),

            password:
                registerForm
                    .querySelector(
                        '[name="password"]'
                    )
                    .value,

            confirm_password:
                registerForm
                    .querySelector(
                        '[name="confirm_password"]'
                    )
                    .value
        };


        try {

            const response =
                await fetch(
                    '/api/users/register',
                    {
                        method: 'POST',

                        headers: {
                            'Content-Type':
                                'application/json'
                        },

                        body:
                            JSON.stringify(data)
                    }
                );


            const result =
                await response.json();


            if (!response.ok) {

                alert(
                    result.message
                    ||
                    'Đăng ký thất bại'
                );

                return;
            }


            // Backend register của bà
            // trả token luôn

            localStorage.setItem(
                'access_token',
                result.data.access_token
            );

            localStorage.setItem(
                'refresh_token',
                result.data.refresh_token
            );


            localStorage.setItem(
                'user',
                JSON.stringify(
                    result.data.user
                )
            );


            alert(
                'Đăng ký thành công'
            );


            // Quay về đúng trang
            // user đang đứng trước đó

            redirectAfterAuth(result.data.user);

        } catch (error) {

            console.error(
                'REGISTER ERROR:',
                error
            );

            alert(
                'Có lỗi xảy ra khi đăng ký'
            );
        }

    }
);