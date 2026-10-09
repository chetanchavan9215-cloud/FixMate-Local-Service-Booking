// =====================================================
// FIXMATE JAVASCRIPT
// FINAL VERSION
// =====================================================


// =====================================================
// PAGE LOADED
// =====================================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("FixMate JavaScript loaded successfully 🚀");


    // =================================================
    // AUTO HIDE FLASH MESSAGES
    // =================================================

    const flashMessages =
        document.querySelectorAll(".flash-message");

    flashMessages.forEach(function (message) {

        setTimeout(function () {

            message.style.transition =
                "opacity 0.5s ease";

            message.style.opacity = "0";


            setTimeout(function () {

                message.remove();

            }, 500);

        }, 4000);

    });


    // =================================================
    // SEARCH - ENTER KEY
    // =================================================

    const searchInputs =
        document.querySelectorAll('input[name="search"]');


    searchInputs.forEach(function (searchInput) {

        searchInput.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {

                    event.preventDefault();

                    const form =
                        searchInput.closest("form");

                    if (form) {

                        form.submit();

                    }

                }

            }
        );

    });

});



// =====================================================
// REGISTER FORM VALIDATION
// =====================================================

function validateRegisterForm() {

    const name =
        document.getElementById("name");

    const password =
        document.getElementById("password");

    const confirmPassword =
        document.getElementById("confirm_password");

    const errorMessage =
        document.getElementById("error-message");


    // If register elements are not present

    if (!name || !password || !confirmPassword) {

        return true;

    }


    const nameValue =
        name.value.trim();

    const passwordValue =
        password.value;

    const confirmPasswordValue =
        confirmPassword.value;


    // Clear previous error

    if (errorMessage) {

        errorMessage.style.display = "none";

        errorMessage.innerText = "";

    }


    // =================================================
    // NAME VALIDATION
    // =================================================

    if (nameValue.length < 3) {

        if (errorMessage) {

            errorMessage.innerText =
                "❌ Name must contain at least 3 characters.";

            errorMessage.style.display =
                "block";

        } else {

            alert(
                "Name must contain at least 3 characters."
            );

        }

        name.focus();

        return false;

    }


    // =================================================
    // PASSWORD LENGTH
    // =================================================

    if (passwordValue.length < 6) {

        if (errorMessage) {

            errorMessage.innerText =
                "❌ Password must contain at least 6 characters.";

            errorMessage.style.display =
                "block";

        } else {

            alert(
                "Password must contain at least 6 characters."
            );

        }

        password.focus();

        return false;

    }


    // =================================================
    // PASSWORD MATCH
    // =================================================

    if (passwordValue !== confirmPasswordValue) {

        if (errorMessage) {

            errorMessage.innerText =
                "❌ Password and Confirm Password do not match.";

            errorMessage.style.display =
                "block";

        } else {

            alert(
                "Password and Confirm Password do not match."
            );

        }

        confirmPassword.focus();

        return false;

    }


    return true;

}



// =====================================================
// PHONE NUMBER VALIDATION
// =====================================================

function validatePhone(input) {

    if (!input) {

        return;

    }


    // Allow only numbers

    input.value =
        input.value.replace(/[^0-9]/g, "");


    // Maximum 10 digits

    if (input.value.length > 10) {

        input.value =
            input.value.substring(0, 10);

    }

}



// =====================================================
// BOOKING FORM VALIDATION
// =====================================================

function validateBookingForm() {

    const phone =
        document.getElementById("phone");


    if (!phone) {

        return true;

    }


    const phoneValue =
        phone.value.trim();


    if (!/^[0-9]{10}$/.test(phoneValue)) {

        alert(
            "❌ Please enter a valid 10-digit mobile number."
        );

        phone.focus();

        return false;

    }


    return true;

}



// =====================================================
// CANCEL BOOKING CONFIRMATION
// =====================================================

function confirmCancelBooking() {

    return confirm(
        "⚠️ Are you sure you want to cancel this booking?"
    );

}



// =====================================================
// DELETE BOOKING CONFIRMATION
// =====================================================

function confirmDeleteBooking() {

    return confirm(
        "⚠️ Are you sure you want to permanently delete this booking?"
    );

}



// =====================================================
// ADMIN STATUS CHANGE CONFIRMATION
// =====================================================

function confirmStatusChange() {

    return confirm(
        "🔄 Are you sure you want to change the booking status?"
    );

}



// =====================================================
// PASSWORD SHOW / HIDE
// =====================================================

function togglePassword(inputId) {

    const input =
        document.getElementById(inputId);


    if (!input) {

        return;

    }


    if (input.type === "password") {

        input.type = "text";

    } else {

        input.type = "password";

    }

}



// =====================================================
// CONFIRM LOGOUT
// =====================================================

function confirmLogout() {

    return confirm(
        "🚪 Are you sure you want to logout?"
    );

}



// =====================================================
// PREVENT DOUBLE FORM SUBMISSION
// =====================================================

document.addEventListener(
    "submit",
    function (event) {

        const form =
            event.target;


        // Do not affect GET/search forms

        if (
            form.method &&
            form.method.toUpperCase() === "GET"
        ) {

            return;

        }


        // Prevent multiple clicks

        const submitButtons =
            form.querySelectorAll(
                'button[type="submit"]'
            );


        submitButtons.forEach(function (button) {

            // Don't disable status select related forms
            // before confirmation is completed

            if (
                button.dataset.processing === "true"
            ) {

                return;

            }


            button.dataset.processing = "true";

            button.disabled = true;

            button.style.opacity = "0.7";

        });

    }
);



// =====================================================
// FIXMATE END
// =====================================================