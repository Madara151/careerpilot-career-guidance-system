// CareerPilot — register.js
// Save to: static/js/register.js

// ─── Toggle password visibility ───────────────────────────────
function togglePwd(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon  = document.getElementById(iconId);
  if (!input || !icon) return;

  const isHidden = input.type === 'password';
  input.type = isHidden ? 'text' : 'password';

  icon.innerHTML = isHidden
    ? `<path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/>
       <line x1="1" y1="1" x2="23" y2="23"/>`
    : `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>`;
}

// ─── Password strength meter ───────────────────────────────────
function getStrength(pwd) {
  let score = 0;
  if (pwd.length >= 6)  score++;
  if (pwd.length >= 10) score++;
  if (/[A-Z]/.test(pwd)) score++;
  if (/[0-9]/.test(pwd)) score++;
  if (/[^A-Za-z0-9]/.test(pwd)) score++;
  return score;
}

const strengthColors = ['', '#F87171', '#FBBF24', '#FBBF24', '#34D399', '#6EE7B7'];
const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong', 'Very strong'];
const strengthWidths  = ['0%', '20%', '40%', '60%', '80%', '100%'];

document.addEventListener('DOMContentLoaded', () => {
  const pwdInput     = document.getElementById('password');
  const strengthWrap = document.getElementById('strengthWrap');
  const strengthBar  = document.getElementById('strengthBar');
  const strengthLbl  = document.getElementById('strengthLabel');

  if (pwdInput) {
    pwdInput.addEventListener('input', () => {
      const val = pwdInput.value;
      if (!val) {
        strengthWrap.classList.remove('visible');
        strengthLbl.textContent = '';
        return;
      }
      strengthWrap.classList.add('visible');
      const score = getStrength(val);
      strengthBar.style.width      = strengthWidths[score];
      strengthBar.style.background = strengthColors[score];
      strengthLbl.textContent      = strengthLabels[score];
      strengthLbl.style.color      = strengthColors[score];
    });
  }

  // ─── Live field validation ─────────────────────────────────
  const form = document.getElementById('registerForm');

  function setError(inputEl, errorId, msg) {
    const err = document.getElementById(errorId);
    if (err) err.textContent = msg;
    if (inputEl) {
      inputEl.closest('.input-wrap')?.querySelector('input, select')?.classList.toggle('invalid', !!msg);
      inputEl.closest('.input-wrap')?.querySelector('input, select')?.classList.toggle('valid', !msg && inputEl.value.trim() !== '');
    }
  }

  function validateName() {
    const el  = document.getElementById('full_name');
    const val = el.value.trim();
    if (!val) return setError(el, 'nameError', 'Full name is required.');
    if (val.length < 2) return setError(el, 'nameError', 'Name must be at least 2 characters.');
    setError(el, 'nameError', '');
    return true;
  }

  function validateEmail() {
    const el  = document.getElementById('email');
    const val = el.value.trim();
    if (!val) return setError(el, 'emailError', 'Email address is required.');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) return setError(el, 'emailError', 'Enter a valid email address.');
    setError(el, 'emailError', '');
    return true;
  }

  function validatePassword() {
    const el  = document.getElementById('password');
    const val = el.value;
    if (!val) return setError(el, 'pwdError', 'Password is required.');
    if (val.length < 6) return setError(el, 'pwdError', 'Password must be at least 6 characters.');
    setError(el, 'pwdError', '');
    return true;
  }

  function validateConfirm() {
    const el  = document.getElementById('confirm_password');
    const pwd = document.getElementById('password').value;
    const val = el.value;
    if (!val) return setError(el, 'confirmPwdError', 'Please confirm your password.');
    if (val !== pwd) return setError(el, 'confirmPwdError', 'Passwords do not match.');
    setError(el, 'confirmPwdError', '');
    return true;
  }

  function validateTerms() {
    const el  = document.getElementById('terms');
    const err = document.getElementById('termsError');
    if (!el.checked) {
      if (err) err.textContent = 'You must agree to the Terms of Service.';
      return false;
    }
    if (err) err.textContent = '';
    return true;
  }

  // Attach live events
  document.getElementById('full_name')?.addEventListener('blur', validateName);
  document.getElementById('email')?.addEventListener('blur', validateEmail);
  document.getElementById('password')?.addEventListener('blur', validatePassword);
  document.getElementById('confirm_password')?.addEventListener('blur', validateConfirm);
  document.getElementById('confirm_password')?.addEventListener('input', validateConfirm);

  // ─── Form submit validation ───────────────────────────────
  form?.addEventListener('submit', (e) => {
    const n  = validateName();
    const em = validateEmail();
    const p  = validatePassword();
    const c  = validateConfirm();
    const t  = validateTerms();

    if (!n || !em || !p || !c || !t) {
      e.preventDefault();
      // Scroll to first error
      const firstError = form.querySelector('.invalid, .field-error:not(:empty)');
      firstError?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });

  // ─── Button loading state ──────────────────────────────────
  form?.addEventListener('submit', () => {
    const btn = document.getElementById('submitBtn');
    const txt = btn?.querySelector('.btn-text');
    if (btn && txt) {
      txt.textContent = 'Creating account…';
      btn.disabled = true;
    }
  });
});