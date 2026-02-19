const pupils = document.querySelectorAll(".pupil");
const chars = document.querySelectorAll(".char");
const charactersArea = document.querySelector(".characters");

const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const confirmPasswordInput = document.getElementById("confirmPassword");
const togglePassword = document.getElementById("togglePassword");

/* =============================== STATE FLAG =============================== */
let passwordMode = false;

/* ================== EYES — FOLLOW MOUSE ONLY FREEZE DURING PASSWORD MODE ===================== */
document.addEventListener("mousemove", (e) => {
  if (passwordMode) return; // freeze eyes

  pupils.forEach(p => {
    const eye = p.parentElement;
    const r = eye.getBoundingClientRect();

    const dx = e.clientX - (r.left + r.width / 2);
    const dy = e.clientY - (r.top + r.height / 2);
    const angle = Math.atan2(dy, dx);

    const dist = 8;
    const x = Math.cos(angle) * dist;
    const y = Math.sin(angle) * dist;

    p.style.transform = `translate(${x}px, ${y}px)`;
  });
});

/* =============================== BODY — PARALLAX (ALWAYS ACTIVE) =============================== */
document.addEventListener("mousemove", (e) => {
  if (!charactersArea) return;

  const b = charactersArea.getBoundingClientRect();
  const cx = b.left + b.width / 2;
  const cy = b.top + b.height / 2;

  const relX = (e.clientX - cx) / (b.width / 2);
  const relY = (e.clientY - cy) / (b.height / 2);

  chars.forEach((c, i) => {
    const depth = 6 + i * 2;
    c.style.transform =
      `translate(${relX * depth}px, ${-relY * depth}px)
       rotateZ(${relX * (i - 1.5) * 4}deg)`;
  });
});

/* =============================== EXPRESSIONS =============================== */
function shockCharacters() {
  passwordMode = true;
  chars.forEach(c => {
    c.classList.remove("happy");
    c.classList.add("shocked");
  });

  // freeze eyes at center
  pupils.forEach(p => {
    p.style.transform = "translate(0,0)";
  });
}

function relaxCharacters() {
  passwordMode = false;
  chars.forEach(c => c.classList.remove("happy", "shocked"));
}

/* =============================== FIELD EVENTS =============================== */

/* Email → happy */
emailInput?.addEventListener("focus", () => {
  relaxCharacters();
  chars.forEach(c => c.classList.add("happy"));
});

/* Password-related → shocked + freeze eyes */
passwordInput?.addEventListener("focus", shockCharacters);
confirmPasswordInput?.addEventListener("focus", shockCharacters);

/* Leaving password fields → normal */
[passwordInput, confirmPasswordInput].forEach(el =>
  el?.addEventListener("blur", relaxCharacters)
);

/* Show password checkbox */
togglePassword?.addEventListener("change", shockCharacters);
