# -*- coding: utf-8 -*-
"""
Authentication Blueprint for LXP Sale Monitor.
Handles /login, /change-password, /register, /logout.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db_connection
from utils import (
    validate_username,
    validate_password_strength,
    is_password_expired,
    DEFAULT_INITIAL_PASSWORD
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session and not session.get('require_password_change'):
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip().upper()
        password = request.form.get('password', '').strip()

        is_valid, err_msg = validate_username(username)
        if not is_valid:
            flash(err_msg, "error")
            return render_template('login.html', username=username)

        if not password:
            flash("กรุณากรอกรหัสผ่าน", "error")
            return render_template('login.html', username=username)

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, password_hash, role, branch, password_changed_at, is_first_login, created_at FROM users WHERE username = %s",
                    (username,)
                )
                user = cursor.fetchone()

                # Auto-provision new 3-letter staff member on initial login with default password Landy*123
                if not user and password == DEFAULT_INITIAL_PASSWORD:
                    default_hash = generate_password_hash(DEFAULT_INITIAL_PASSWORD)
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, role, branch, password_changed_at, is_first_login) VALUES (%s, %s, 'USER', NULL, NOW(), 1)",
                        (username, default_hash)
                    )
                    new_user_id = cursor.lastrowid
                    user = {
                        'id': new_user_id,
                        'username': username,
                        'password_hash': default_hash,
                        'role': 'USER',
                        'branch': None,
                        'password_changed_at': datetime.now(),
                        'is_first_login': 1
                    }
            conn.close()

            if user and check_password_hash(user['password_hash'], password):
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user.get('role', 'USER')
                session['branch'] = user.get('branch', '') or ''
                session['login_time'] = datetime.now().timestamp()
                
                # ADMIN accounts do not require forced password change or expiration
                if session['role'] == 'ADMIN':
                    session['require_password_change'] = False
                    session['is_first_login'] = False
                    flash(f"ยินดีต้อนรับผู้ดูแลระบบ {user['username']} เข้าสู่ระบบสำเร็จ!", "success")
                    return redirect(url_for('dashboard.dashboard'))

                # Check 1: Initial Default Password (Landy*123) or is_first_login for regular users
                is_initial_pw = (
                    user.get('is_first_login') == 1 or 
                    check_password_hash(user['password_hash'], DEFAULT_INITIAL_PASSWORD) or 
                    password == DEFAULT_INITIAL_PASSWORD
                )

                if is_initial_pw:
                    session['require_password_change'] = True
                    session['is_first_login'] = True
                    return redirect(url_for('auth.change_password'))

                # Check 2: 3-month password expiration (90 days) for regular users
                last_changed = user.get('password_changed_at') or user.get('created_at')
                if is_password_expired(last_changed):
                    session['require_password_change'] = True
                    session['is_first_login'] = False
                    flash("รหัสผ่านของคุณมีอายุเกิน 3 เดือน (90 วัน) แล้ว เพื่อความปลอดภัย กรุณาตั้งรหัสผ่านใหม่", "warning")
                    return redirect(url_for('auth.change_password'))
                else:
                    session['require_password_change'] = False
                    session['is_first_login'] = False
                    flash(f"ยินดีต้อนรับคุณ {user['username']} ({session['role']}) เข้าสู่ระบบสำเร็จ!", "success")
                    return redirect(url_for('dashboard.dashboard'))
            else:
                flash("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", "error")

        except Exception as e:
            flash(f"เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล: {str(e)}", "error")

    return render_template('login.html')


@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        flash("กรุณาเข้าสู่ระบบก่อนดำเนินการ", "warning")
        return redirect(url_for('auth.login'))

    is_forced = session.get('require_password_change', False)
    is_first_login = session.get('is_first_login', False)

    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not new_password:
            flash("กรุณากรอกรหัสผ่านใหม่", "error")
            return render_template('change_password.html', is_forced=is_forced, is_first_login=is_first_login)

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, password_hash FROM users WHERE id = %s", (session['user_id'],))
                user = cursor.fetchone()

            if not user:
                conn.close()
                flash("ไม่พบข้อมูลผู้ใช้งาน", "error")
                return redirect(url_for('auth.login'))

            if check_password_hash(user['password_hash'], new_password):
                conn.close()
                flash("รหัสผ่านใหม่ต้องไม่ซ้ำกับรหัสผ่านเดิม", "error")
                return render_template('change_password.html', is_forced=is_forced, is_first_login=is_first_login)

            is_valid_pw, pw_err = validate_password_strength(new_password)
            if not is_valid_pw:
                conn.close()
                flash(pw_err, "error")
                return render_template('change_password.html', is_forced=is_forced, is_first_login=is_first_login)

            if new_password != confirm_password:
                conn.close()
                flash("การยืนยันรหัสผ่านใหม่ไม่ตรงกัน", "error")
                return render_template('change_password.html', is_forced=is_forced, is_first_login=is_first_login)

            # Update password, reset is_first_login, and update timestamp in MySQL
            new_hash = generate_password_hash(new_password)
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password_hash = %s, password_changed_at = NOW(), is_first_login = 0 WHERE id = %s",
                    (new_hash, session['user_id'])
                )
            conn.close()

            # Clear session and redirect back to login for re-authentication with new password
            session.clear()
            flash("ตั้งรหัสผ่านใหม่เรียบร้อยแล้ว กรุณาเข้าสู่ระบบอีกครั้งด้วยรหัสผ่านใหม่ของคุณ", "success")
            return redirect(url_for('auth.login'))

        except Exception as e:
            flash(f"เกิดข้อผิดพลาดในการเปลี่ยนรหัสผ่าน: {str(e)}", "error")
            return render_template('change_password.html', is_forced=is_forced, is_first_login=is_first_login)

    return render_template('change_password.html', is_forced=is_forced, is_first_login=is_first_login)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("ออกจากระบบเรียบร้อยแล้ว", "info")
    return redirect(url_for('auth.login'))
