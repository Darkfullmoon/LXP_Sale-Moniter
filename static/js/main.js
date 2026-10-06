/**
 * LXP Sale Monitor - Client-side validation & interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    setupSidebarScrollPersistence();
    setupInputFilters();
    setupFormValidation();
});

/**
 * Persist Sidebar Scroll Position Across Page Navigation
 */
function setupSidebarScrollPersistence() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    // Restore scroll position
    const saved = sessionStorage.getItem('sidebar_scroll_top');
    if (saved !== null) {
        sidebar.scrollTop = parseInt(saved, 10);
    }

    // Save scroll position on scroll
    sidebar.addEventListener('scroll', () => {
        sessionStorage.setItem('sidebar_scroll_top', sidebar.scrollTop);
    }, { passive: true });

    // Save scroll position when clicking any link in sidebar
    sidebar.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            sessionStorage.setItem('sidebar_scroll_top', sidebar.scrollTop);
        });
    });
}

/**
 * Mobile Sidebar Toggle Handler
 */
function toggleSidebar(forceState) {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    if (forceState !== undefined) {
        if (forceState) {
            sidebar.classList.add('open');
        } else {
            sidebar.classList.remove('open');
        }
    } else {
        sidebar.classList.toggle('open');
    }
}

// Close sidebar when clicking outside of it on mobile
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    if (sidebar && sidebar.classList.contains('open')) {
        if (!sidebar.contains(e.target) && (!toggleBtn || !toggleBtn.contains(e.target))) {
            sidebar.classList.remove('open');
        }
    }
});

/**
 * Real-time filter inputs and password complexity checker
 */
function setupInputFilters() {
    // 1. Filter Uppercase Letters Only (A-Z) - Max length 3
    const uppercaseInputs = document.querySelectorAll('.uppercase-only');
    uppercaseInputs.forEach(input => {
        input.setAttribute('maxlength', '3');
        input.addEventListener('input', (e) => {
            const start = input.selectionStart;
            const end = input.selectionEnd;
            const originalVal = input.value;
            
            // Convert to uppercase and strip non-A-Z, truncate to 3 chars
            const filteredVal = originalVal.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 3);
            
            if (originalVal !== filteredVal) {
                input.value = filteredVal;
                if (start !== null && end !== null) {
                    input.setSelectionRange(Math.min(start, 3), Math.min(end, 3));
                }
            }
        });

        // Sanitize on paste
        input.addEventListener('paste', (e) => {
            setTimeout(() => {
                input.value = input.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 3);
                input.dispatchEvent(new Event('input'));
            }, 0);
        });
    });

    // 2. Real-time Password Complexity Checker
    const strengthInputs = document.querySelectorAll('.password-strength-input');
    strengthInputs.forEach(input => {
        input.addEventListener('input', () => {
            updatePasswordChecklist(input.value);
        });
    });

    // 3. Confirm Password Matcher
    const confirmInput = document.getElementById('confirm_password');
    if (confirmInput) {
        confirmInput.addEventListener('input', () => {
            const pw = document.getElementById('password')?.value || '';
            const confirmVal = confirmInput.value;
            if (confirmVal.length > 0) {
                if (confirmVal === pw) {
                    showValidationMsg('confirmPasswordValidationMsg', '✓ รหัสผ่านตรงกัน', 'valid');
                } else {
                    showValidationMsg('confirmPasswordValidationMsg', 'รหัสผ่านยังไม่ตรงกัน', 'error');
                }
            } else {
                clearValidationMsg('confirmPasswordValidationMsg');
            }
        });
    }
}

/**
 * Update visual checklist indicators for password rules
 */
function updatePasswordChecklist(val) {
    const rules = {
        'req-length': val.length >= 8,
        'req-upper': /[A-Z]/.test(val),
        'req-lower': /[a-z]/.test(val),
        'req-number': /[0-9]/.test(val),
        'req-special': /[^A-Za-z0-9]/.test(val)
    };

    let allMet = true;
    for (const [id, isMet] of Object.entries(rules)) {
        const el = document.getElementById(id);
        if (el) {
            if (isMet) {
                el.style.color = '#10b981'; // Green
                el.style.fontWeight = '600';
                el.innerHTML = `<i data-lucide="check-circle-2" style="width: 12px; height: 12px; stroke: #10b981;"></i> ` + el.textContent.trim();
            } else {
                allMet = false;
                el.style.color = 'var(--text-muted)';
                el.style.fontWeight = 'normal';
                el.innerHTML = `<i data-lucide="circle" style="width: 12px; height: 12px;"></i> ` + el.textContent.trim();
            }
        } else {
            if (!isMet) allMet = false;
        }
    }

    if (window.lucide) {
        lucide.createIcons();
    }

    if (val.length > 0) {
        if (allMet) {
            showValidationMsg('passwordValidationMsg', '✓ ความปลอดภัยของรหัสผ่านผ่านเกณฑ์ครบถ้วน', 'valid');
        } else {
            showValidationMsg('passwordValidationMsg', 'รหัสผ่านต้องครบทั้ง 5 เงื่อนไขด้านล่าง', 'error');
        }
    } else {
        clearValidationMsg('passwordValidationMsg');
    }
}

function showValidationMsg(elementId, text, type) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = text;
    el.className = `input-validation-msg ${type}`;
}

function clearValidationMsg(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = '';
    el.className = 'input-validation-msg';
}

/**
 * Toggle Show/Hide password field
 */
function togglePasswordVisibility(inputId, button) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    const icon = button.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        if (icon) {
            icon.setAttribute('data-lucide', 'eye-off');
            if (window.lucide) lucide.createIcons();
        }
    } else {
        input.type = 'password';
        if (icon) {
            icon.setAttribute('data-lucide', 'eye');
            if (window.lucide) lucide.createIcons();
        }
    }
}

/**
 * Validate on form submit
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.auth-form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const usernameInput = form.querySelector('.uppercase-only');
            const passwordInput = form.querySelector('#password');
            const confirmInput = form.querySelector('#confirm_password');
            const isChangeOrRegister = form.id === 'registerForm' || form.id === 'changePasswordForm';

            // Username validation
            if (usernameInput) {
                const username = usernameInput.value.trim();
                if (!/^[A-Z]{3}$/.test(username)) {
                    e.preventDefault();
                    showValidationMsg('usernameValidationMsg', 'ชื่อผู้ใช้ต้องเป็นตัวอักษรพิมพ์ใหญ่ 3 ตัวเท่านั้น (เช่น ADM, USR)', 'error');
                    usernameInput.focus();
                    return;
                }
            }

            // Strong password validation for register/change password
            if (passwordInput && isChangeOrRegister) {
                const password = passwordInput.value;
                const isStrong = password.length >= 8 &&
                                 /[A-Z]/.test(password) &&
                                 /[a-z]/.test(password) &&
                                 /[0-9]/.test(password) &&
                                 /[^A-Za-z0-9]/.test(password);

                if (!isStrong) {
                    e.preventDefault();
                    showValidationMsg('passwordValidationMsg', 'รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร และมีตัวพิมพ์ใหญ่ พิมพ์เล็ก ตัวเลข และอักขระพิเศษ', 'error');
                    passwordInput.focus();
                    return;
                }

                if (confirmInput && confirmInput.value !== password) {
                    e.preventDefault();
                    showValidationMsg('confirmPasswordValidationMsg', 'การยืนยันรหัสผ่านไม่ตรงกัน', 'error');
                    confirmInput.focus();
                    return;
                }
            }
        });
    });
}

/**
 * Direct Print PDF without opening new tab / Adobe window.
 * Uses an invisible background iframe and native browser print dialog with THSarabun fonts.
 */
function printPdfDirect(pdfUrl, btnElement) {
    if (!pdfUrl) return;

    let originalHtml = '';
    if (btnElement) {
        originalHtml = btnElement.innerHTML;
        btnElement.innerHTML = '<i data-lucide="loader" class="animate-spin"></i> กำลังเตรียมเอกสาร...';
        btnElement.disabled = true;
        if (window.lucide) lucide.createIcons();
    }

    // Remove any previous print iframes
    const oldIframe = document.getElementById('hiddenPdfPrintFrame');
    if (oldIframe) {
        oldIframe.remove();
    }

    fetch(pdfUrl)
        .then(response => {
            if (!response.ok) throw new Error('PDF fetch failed: ' + response.statusText);
            return response.blob();
        })
        .then(blob => {
            const blobUrl = URL.createObjectURL(blob);
            const iframe = document.createElement('iframe');
            iframe.id = 'hiddenPdfPrintFrame';
            iframe.style.position = 'fixed';
            iframe.style.left = '-9999px';
            iframe.style.top = '-9999px';
            iframe.style.width = '0px';
            iframe.style.height = '0px';
            iframe.style.border = 'none';
            iframe.src = blobUrl;

            document.body.appendChild(iframe);

            iframe.onload = () => {
                setTimeout(() => {
                    try {
                        iframe.contentWindow.focus();
                        iframe.contentWindow.print();
                    } catch (err) {
                        console.error('Direct iframe print failed, fallback:', err);
                        window.open(blobUrl, '_blank');
                    }

                    if (btnElement) {
                        btnElement.innerHTML = originalHtml;
                        btnElement.disabled = false;
                        if (window.lucide) lucide.createIcons();
                    }
                }, 300);
            };
        })
        .catch(err => {
            console.error('Error fetching PDF for printing:', err);
            window.open(pdfUrl, '_blank');
            if (btnElement) {
                btnElement.innerHTML = originalHtml;
                btnElement.disabled = false;
                if (window.lucide) lucide.createIcons();
            }
        });
}

