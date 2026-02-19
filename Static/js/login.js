document.addEventListener("DOMContentLoaded", () => {

  console.log("Login JS loaded");

  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const loginBtn = document.getElementById("loginBtn");
  const formMessage = document.getElementById("formMessage");

  /* ================= PREVENT FORM SUBMIT ================= */

  const loginForm = document.querySelector("form");
  if (loginForm) {
    loginForm.addEventListener("submit", (e) => {
      e.preventDefault(); // THIS WAS REQUIRED
    });
  }

  /* ================= LOGIN ================= */

  loginBtn.addEventListener("click", () => {

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!email || !password) {
      formMessage.textContent = "Please enter email and password";
      formMessage.style.color = "red";
      return;
    }

    fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {

      if (data.userId) {
        localStorage.setItem("userId", data.userId);
        localStorage.setItem("userName", data.name);

        formMessage.textContent = "Login successful";
        formMessage.style.color = "green";

        setTimeout(() => {
          window.location.href = "/home";
        }, 800);

      } else {
        formMessage.textContent = data.message || "Login failed";
        formMessage.style.color = "red";
      }
    })
    .catch(() => {
      formMessage.textContent = "Server error";
      formMessage.style.color = "red";
    });
  });

  /* ================= SHOW / HIDE PASSWORD ================= */

  const togglePassword = document.getElementById("togglePassword");
  if (togglePassword) {
    togglePassword.addEventListener("change", () => {
      passwordInput.type = togglePassword.checked ? "text" : "password";
    });
  }

  /* ================= FORGOT PASSWORD ================= */

  emailjs.init("eeax2S6Pz7Xq25i28");

  const forgotLink = document.getElementById("forgotLink");
  const forgotSection = document.getElementById("forgotSection");
  const forgotEmail = document.getElementById("forgotEmail");
  const sendForgotOtp = document.getElementById("sendForgotOtp");
  const forgotOtpSection = document.getElementById("forgotOtpSection");
  const forgotOtp = document.getElementById("forgotOtp");
  const newPassword = document.getElementById("newPassword");
  const resetPasswordBtn = document.getElementById("resetPasswordBtn");
  const forgotMsg = document.getElementById("forgotMsg");

  let generatedOtp = "";

  forgotLink.addEventListener("click", (e) => {
    e.preventDefault();
    forgotSection.style.display = "block";
    forgotMsg.textContent = "";
  });

  sendForgotOtp.addEventListener("click", () => {

    const email = forgotEmail.value.trim();
    if (!email) {
      forgotMsg.textContent = "Enter registered email";
      return;
    }

    generatedOtp = Math.floor(100000 + Math.random() * 900000).toString();

    emailjs.send("service_6o44tec", "template_2549wwa", {
      email: email,
      passcode: generatedOtp,
      time: new Date(Date.now() + 15 * 60000).toLocaleTimeString()
    })
    .then(() => {
      forgotOtpSection.style.display = "block";
      forgotMsg.textContent = "OTP sent to your email";
    })
    .catch(() => {
      forgotMsg.textContent = "Failed to send OTP";
    });
  });

  resetPasswordBtn.addEventListener("click", () => {

    if (forgotOtp.value.trim() !== generatedOtp) {
      forgotMsg.textContent = "Invalid OTP";
      return;
    }

    if (!newPassword.value) {
      forgotMsg.textContent = "Enter new password";
      return;
    }

    fetch("/api/forgot-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify({
        email: forgotEmail.value,
        newPassword: newPassword.value
      })
    })
    .then(res => res.json())
    .then(data => {
      forgotMsg.textContent = data.message;

      if (data.message === "Password updated successfully") {
        setTimeout(() => {
          window.location.href = "/login";
        }, 1200);
      }
    });
  });

});
