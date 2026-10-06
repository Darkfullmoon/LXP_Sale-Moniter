# -*- coding: utf-8 -*-
"""
LXP Sale Monitor - Main Flask Application.
Modularized architecture using Flask Blueprints.
"""

import os
from datetime import timedelta, datetime
from flask import Flask, session, request, abort, flash, redirect, url_for as flask_url_for
from dotenv import load_dotenv

from db import get_db_connection, init_db
from routes import register_blueprints
from utils import (
    get_all_branches,
    format_branch_filter,
    format_date_dmy,
    generate_csrf_token,
    validate_csrf_token
)
from maid_config import format_month_year_th

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "lxp_sale_monitor_super_secret_key_2026")
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB max request size
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # 24 Hours auto-expiration
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

SESSION_TIMEOUT_SECONDS = 24 * 3600  # 24 hours in seconds

@app.before_request
def check_session_timeout():
    """Enforces 24-hour absolute session expiration for logged-in users."""
    if 'user_id' in session:
        login_time = session.get('login_time')
        if login_time:
            now = datetime.now().timestamp()
            if now - login_time > SESSION_TIMEOUT_SECONDS:
                session.clear()
                flash("เซสชันการเข้าสู่ระบบหมดอายุ (ครบกำหนด 24 ชั่วโมง) กรุณาเข้าสู่ระบบใหม่อีกครั้ง", "warning")
                return redirect(flask_url_for('auth.login'))
        else:
            # Set login_time for existing active sessions if not already present
            session['login_time'] = datetime.now().timestamp()

# Global CSRF Protection on all mutating HTTP methods
@app.before_request
def csrf_protect():
    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        # Extract CSRF token from Form data, JSON body, or Headers
        token = request.form.get('csrf_token')
        if not token and request.is_json:
            token = (request.get_json(silent=True) or {}).get('csrf_token')
        if not token:
            token = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken')

        if not validate_csrf_token(token):
            abort(403, description="CSRF Token ไม่ถูกต้องหรือไม่พบ (Invalid or missing CSRF Token)")

# Endpoint mapping to ensure 100% backward-compatibility for all Jinja templates and url_for calls
ENDPOINT_ALIASES = {
    'login': 'auth.login',
    'change_password': 'auth.change_password',
    'register': 'auth.register',
    'logout': 'auth.logout',
    'index': 'dashboard.index',
    'dashboard': 'dashboard.dashboard',
    'morning_audit': 'morning_audit.morning_audit',
    'morning_audit_history': 'morning_audit.morning_audit_history',
    'morning_audit_detail': 'morning_audit.morning_audit_detail',
    'morning_audit_pdf': 'morning_audit.morning_audit_pdf',
    'morning_audit_ai_analysis': 'morning_audit.morning_audit_ai_analysis',
    'ai_summarize': 'morning_audit.ai_summarize',
    'upload_audit_photo': 'morning_audit.upload_audit_photo',
    'upload_report_photo': 'daily_report.upload_report_photo',
    'daily_report': 'daily_report.daily_report',
    'daily_report_history': 'daily_report.daily_report_history',
    'daily_report_detail': 'daily_report.daily_report_detail',
    'daily_report_pdf': 'daily_report.daily_report_pdf',
    'add_item': 'inspection.add_item',
    'inspection': 'inspection.inspection',
    'inspection_action': 'inspection.inspection_action',
    'history': 'inspection.history',
    'admin_branches': 'admin.admin_branches',
    'admin_add_branch': 'admin.admin_add_branch',
    'admin_delete_branch': 'admin.admin_delete_branch',
    'admin_clear_data': 'admin.admin_clear_data',
    'admin_weekly_customers': 'admin.admin_weekly_customers',
    'weekly_customers': 'admin.admin_weekly_customers',
    'maid_schedule': 'maid.maid_schedule',
    'maid_schedule_history': 'maid.maid_schedule_history',
    'maid_schedule_detail': 'maid.maid_schedule_detail',
    'maid_schedule_pdf': 'maid.maid_schedule_pdf',
    'admin_users': 'admin.admin_users',
    'admin_reset_user_password': 'admin.admin_reset_user_password',
}


def smart_url_for(endpoint, **values):
    """
    Enhanced url_for resolver that maps shorthand endpoint names to their
    respective blueprint endpoints, while preserving standard blueprint calls.
    """
    resolved_endpoint = ENDPOINT_ALIASES.get(endpoint, endpoint)
    return flask_url_for(resolved_endpoint, **values)


# Register smart_url_for and csrf_token into Jinja environment
app.jinja_env.globals['url_for'] = smart_url_for
app.jinja_env.globals['csrf_token'] = generate_csrf_token

# Register template filters
app.add_template_filter(format_branch_filter, 'format_branch')
app.add_template_filter(format_date_dmy, 'format_date')
app.add_template_filter(format_date_dmy, 'format_date_th')
app.add_template_filter(format_month_year_th, 'format_month_year_th')
app.add_template_filter(format_month_year_th, 'format_month_th')


@app.context_processor
def inject_user_info():
    """Provides user session and notification badges globally to all templates."""
    pending_count = 0
    if 'user_id' in session:
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM inspections WHERE status = 'PENDING'")
                res = cursor.fetchone()
                if res:
                    pending_count = res['count']
            conn.close()
        except Exception:
            pass

    return {
        'current_user': {
            'username': session.get('username'),
            'role': session.get('role', 'USER'),
            'id': session.get('user_id'),
            'branch': session.get('branch', '') or '',
            'require_password_change': session.get('require_password_change', False),
            'is_first_login': session.get('is_first_login', False)
        },
        'pending_count': pending_count,
        'global_branches': get_all_branches()
    }


# Register all modular blueprints
register_blueprints(app)


def get_local_network_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


if __name__ == '__main__':
    init_db()
    
    target_host = '0.0.0.0'
    target_port = 5000
    
    try:
        app.run(host=target_host, port=target_port, debug=True)
    except OSError:
        app.run(host='127.0.0.1', port=target_port, debug=True)
