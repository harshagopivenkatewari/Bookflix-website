document.addEventListener("DOMContentLoaded", () => {

  console.log("Register JS loaded");

  // INIT EMAILJS
  emailjs.init("eeax2S6Pz7Xq25i28");

  // DOM ELEMENTS
  const nameInput = document.getElementById("name");
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const confirmPassword = document.getElementById("confirmPassword");
  const otpInput = document.getElementById("otp");
  const otpSection = document.getElementById("otpSection");
  const sendOtpBtn = document.getElementById("sendOtpBtn");
  const formMessage = document.getElementById("formMessage");
  const togglePassword = document.getElementById("togglePassword");

  let generatedOTP = "";

  // MESSAGE HELPER
  function showMessage(msg, type = "info") {
    formMessage.textContent = msg;
    formMessage.style.color =
      type === "error" ? "red" :
      type === "success" ? "green" : "#333";
  }

  // SEND OTP
  sendOtpBtn.addEventListener("click", () => {

    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const confirm = confirmPassword.value;

    if (!name || !email || !password || password !== confirm) {
      showMessage("Please enter valid details", "error");
      return;
    }

    generatedOTP = Math.floor(100000 + Math.random() * 900000).toString();

    emailjs.send("service_6o44tec", "template_ob3qrqz", {
      email: email,
      passcode: generatedOTP,
      time: new Date(Date.now() + 15 * 60000).toLocaleTimeString()
    })
    .then(() => {
      otpSection.style.display = "block";
      sendOtpBtn.disabled = true;
      showMessage("OTP sent successfully", "success");
    })
    .catch(() => {
      showMessage("Failed to send OTP. Try again.", "error");
    });
  });

  // VERIFY OTP & REGISTER
  window.verifyOTP = function () {

    if (otpInput.value.trim() !== generatedOTP) {
      showMessage("Invalid OTP", "error");
      return;
    }

    fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: nameInput.value.trim(),
        email: emailInput.value.trim(),
        password: passwordInput.value
      })
    })
    .then(async res => {
      const data = await res.json();
      return { ok: res.ok, data };
    })
    .then(({ ok, data }) => {
      if (!ok) {
        showMessage(data.message, "error");
        return;
      }

      showMessage("Registration successful. Redirecting to login...", "success");

      setTimeout(() => {
        window.location.href = "/login";
      }, 1200);
    })
    .catch(() => {
      showMessage("Server error. Please try again.", "error");
    });
  };

  // SHOW / HIDE PASSWORD
  if (togglePassword) {
    togglePassword.addEventListener("change", () => {
      const show = togglePassword.checked;
      passwordInput.type = show ? "text" : "password";
      confirmPassword.type = show ? "text" : "password";
    });
  }

});
