# -*- coding: utf-8 -*-
"""
Admin Management Blueprint for LXP Sale Monitor.
Handles /admin/branches, /admin/branches/add, /admin/branches/delete, /admin/clear-data,
and /admin/weekly-customers (จำนวนลูกค้าประจำสัปดาห์).
"""

import os
import re
import json
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify

from db import get_db_connection, clear_all_report_data
from werkzeug.security import generate_password_hash
from audit_config import BRANCH_LIST
from utils import (
    admin_required, get_all_branches, invalidate_branch_cache,
    get_retention_cutoff_date, run_data_retention_cleanup,
    get_daily_submission_status, validate_username, DEFAULT_INITIAL_PASSWORD,
    generate_random_password
)

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/submission-monitor', methods=['GET'])
@admin_required
def admin_submission_monitor():
    """Daily submission monitoring dashboard for morning (cutoff 09:15) and evening (cutoff 17:00)."""
    target_date = request.args.get('date', '').strip()
    branch_filter = request.args.get('branch', 'ALL').strip()

    summary, branches_status, current_date = get_daily_submission_status(target_date)

    if branch_filter and branch_filter != 'ALL':
        branches_status = [b for b in branches_status if b['branch'] == branch_filter or branch_filter in b['branch']]

    return render_template(
        'submission_monitor.html',
        summary=summary,
        branches_status=branches_status,
        all_branches=get_all_branches(),
        current_date=current_date,
        current_branch=branch_filter
    )


@admin_bp.route('/admin/submission-monitor/data', methods=['GET'])
@admin_required
def admin_submission_monitor_data():
    """AJAX JSON endpoint for live submission status polling and dynamic date changes."""
    target_date = request.args.get('date', '').strip()
    branch_filter = request.args.get('branch', 'ALL').strip()

    try:
        summary, branches_status, current_date = get_daily_submission_status(target_date)
        if branch_filter and branch_filter != 'ALL':
            branches_status = [b for b in branches_status if b['branch'] == branch_filter or branch_filter in b['branch']]

        return jsonify({
            'success': True,
            'summary': summary,
            'branches_status': branches_status,
            'current_date': current_date,
            'current_branch': branch_filter
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


THAI_DAYS = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
THAI_MONTHS_SHORT = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
THAI_MONTHS_FULL = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]


def format_thai_date_label(d):
    """Formats date to '24 ส.ค. 2026'."""
    return f"{d.day} {THAI_MONTHS_SHORT[d.month]} {d.year}"


def format_thai_date_full(d):
    """Formats date to '24 สิงหาคม 2569'."""
    return f"{d.day} {THAI_MONTHS_FULL[d.month]} {d.year + 543}"


def parse_safe_int(val):
    """Safely parse integer value from report stats."""
    if not val:
        return 0
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return 0


def get_weekly_customer_summary(branch_filter='ALL', requested_weeks=4):
    """
    Fetches daily reports from daily_operation_reports, aggregates customer stats per day,
    and groups them into standard 7-day Monday-Sunday weeks.
    Returns: (weeks_list, branches, current_branch)
    """
    conn = get_db_connection()
    reports_by_date = {}
    earliest_date = None

    with conn.cursor() as cursor:
        query = """
            SELECT id, branch, team, report_date, submitted_by, 
                   morning_brief, daily_summary, additional_tasks, 
                   customer_stats, created_at 
            FROM daily_operation_reports 
            WHERE 1=1
        """
        params = []
        if branch_filter and branch_filter != 'ALL':
            branch_keyword = branch_filter.replace("สาขา", "").split("(")[0].strip()
            query += " AND (branch = %s OR branch LIKE %s OR %s LIKE CONCAT('%%', branch, '%%'))"
            params.extend([branch_filter, f"%{branch_keyword}%", branch_filter])

        query += " ORDER BY report_date ASC, id ASC"
        cursor.execute(query, tuple(params))
        all_reports = cursor.fetchall()

        for r in all_reports:
            r_date = r['report_date']
            if isinstance(r_date, (datetime, date)):
                r_date_str = r_date.strftime('%Y-%m-%d')
                r_date_obj = r_date if isinstance(r_date, date) else r_date.date()
            else:
                r_date_str = str(r_date).strip()
                try:
                    r_date_obj = datetime.strptime(r_date_str, '%Y-%m-%d').date()
                except Exception:
                    continue

            if earliest_date is None or r_date_obj < earliest_date:
                earliest_date = r_date_obj

            stats_dict = {}
            if r.get('customer_stats'):
                try:
                    stats_dict = json.loads(r['customer_stats']) if isinstance(r['customer_stats'], str) else r['customer_stats']
                except Exception:
                    stats_dict = {}

            breakdown = {
                'call_center': parse_safe_int(stats_dict.get('call_center')),
                'walk_in': parse_safe_int(stats_dict.get('walk_in')),
                'appointment': parse_safe_int(stats_dict.get('appointment')),
                'booking': parse_safe_int(stats_dict.get('booking')),
                'call_manager': parse_safe_int(stats_dict.get('call_manager')),
                'call_senior': parse_safe_int(stats_dict.get('call_senior'))
            }
            report_total = sum(breakdown.values())

            report_item = {
                'id': r['id'],
                'branch': r.get('branch', ''),
                'team': r.get('team', ''),
                'submitted_by': r.get('submitted_by', ''),
                'report_date': r_date_str,
                'daily_summary': r.get('daily_summary', '') or '',
                'additional_tasks': r.get('additional_tasks', '') or '',
                'stats': stats_dict,
                'breakdown': breakdown,
                'total_customers': report_total
            }

            if r_date_str not in reports_by_date:
                reports_by_date[r_date_str] = []
            reports_by_date[r_date_str].append(report_item)

    conn.close()

    # Automatically purge data older than 4 calendar months
    try:
        run_data_retention_cleanup(4)
    except Exception:
        pass

    # Determine reference date (current Monday) and 4-month calendar cutoff
    today = date.today()
    current_monday = today - timedelta(days=today.weekday())
    cutoff_date = get_retention_cutoff_date(4)
    cutoff_monday = cutoff_date - timedelta(days=cutoff_date.weekday())

    # Calculate exact total weeks spanning 4 calendar months
    total_weeks = max(4, ((current_monday - cutoff_monday).days // 7) + 1)
    if requested_weeks and requested_weeks > total_weeks:
        total_weeks = requested_weeks

    weeks_list = []
    for w_idx in range(total_weeks):
        w_monday = current_monday - timedelta(days=w_idx * 7)
        w_sunday = w_monday + timedelta(days=6)

        week_label = f"{format_thai_date_label(w_monday)} - {format_thai_date_label(w_sunday)}"
        week_label_th = f"{w_monday.day} {THAI_MONTHS_SHORT[w_monday.month]} - {w_sunday.day} {THAI_MONTHS_SHORT[w_sunday.month]} {w_sunday.year + 543}"

        days = []
        week_total_customers = 0

        for d_idx in range(7):
            cur_date = w_monday + timedelta(days=d_idx)
            cur_date_str = cur_date.strftime('%Y-%m-%d')
            day_reports = reports_by_date.get(cur_date_str, [])

            day_breakdown = {
                'call_center': sum(rep['breakdown']['call_center'] for rep in day_reports),
                'walk_in': sum(rep['breakdown']['walk_in'] for rep in day_reports),
                'appointment': sum(rep['breakdown']['appointment'] for rep in day_reports),
                'booking': sum(rep['breakdown']['booking'] for rep in day_reports),
                'call_manager': sum(rep['breakdown']['call_manager'] for rep in day_reports),
                'call_senior': sum(rep['breakdown']['call_senior'] for rep in day_reports),
            }
            day_breakdown['total_calls'] = day_breakdown['call_manager'] + day_breakdown['call_senior']
            day_customer_count = sum(rep['total_customers'] for rep in day_reports) if day_reports else sum(day_breakdown.values()) - day_breakdown['total_calls'] + day_breakdown['total_calls']
            day_customer_count = sum([
                day_breakdown['call_center'],
                day_breakdown['walk_in'],
                day_breakdown['appointment'],
                day_breakdown['booking'],
                day_breakdown['call_manager'],
                day_breakdown['call_senior']
            ])
            week_total_customers += day_customer_count

            days.append({
                'day_name': THAI_DAYS[d_idx],
                'day_short': THAI_DAYS[d_idx][:3],
                'date': cur_date_str,
                'day_date_short': f"{cur_date.day} {THAI_MONTHS_SHORT[cur_date.month]}",
                'formatted_date': format_thai_date_label(cur_date),
                'formatted_date_th': format_thai_date_full(cur_date),
                'count': day_customer_count,
                'has_data': len(day_reports) > 0,
                'reports_count': len(day_reports),
                'breakdown': day_breakdown,
                'reports': day_reports
            })

        weeks_list.append({
            'week_index': w_idx + 1,
            'total_weeks': total_weeks,
            'week_label': week_label,
            'week_label_th': week_label_th,
            'start_date': w_monday.strftime('%Y-%m-%d'),
            'end_date': w_sunday.strftime('%Y-%m-%d'),
            'days': days,
            'total_customers': week_total_customers,
            'is_empty': (week_total_customers == 0 and not any(d['has_data'] for d in days))
        })

    return weeks_list, get_all_branches(), branch_filter


@admin_bp.route('/admin/weekly-customers', methods=['GET'])
@admin_required
def admin_weekly_customers():
    """Weekly customer count dashboard for Admin."""
    branch_filter = request.args.get('branch', 'ALL').strip()
    try:
        weeks, branches, current_branch = get_weekly_customer_summary(branch_filter=branch_filter)
        return render_template(
            'weekly_customers.html',
            weeks=weeks,
            branches=branches,
            current_branch=current_branch
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการโหลดข้อมูลจำนวนลูกค้าประจำสัปดาห์: {e}", "error")
        return render_template(
            'weekly_customers.html',
            weeks=[],
            branches=get_all_branches(),
            current_branch=branch_filter
        )


@admin_bp.route('/admin/weekly-customers/data', methods=['GET'])
@admin_required
def admin_weekly_customers_data():
    """AJAX JSON endpoint for dynamic week navigation without page refresh."""
    branch_filter = request.args.get('branch', 'ALL').strip()
    try:
        weeks, branches, current_branch = get_weekly_customer_summary(branch_filter=branch_filter)
        return jsonify({
            'success': True,
            'weeks': weeks,
            'current_branch': current_branch
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/admin/branches', methods=['GET'])
@admin_required
def admin_branches():
    """Dedicated management page for system branches."""
    branches = get_all_branches()
    return render_template('manage_branches.html', branches=branches)


@admin_bp.route('/admin/branches/add', methods=['POST'])
@admin_required
def admin_add_branch():
    branch_name = request.form.get('branch_name', '').strip()
    if not branch_name:
        flash("กรุณากรอกชื่อสาขา", "error")
        return redirect(url_for('admin.admin_branches'))
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, is_active FROM branches WHERE name = %s", (branch_name,))
            existing = cursor.fetchone()
            if existing:
                if existing['is_active'] == 0:
                    cursor.execute("UPDATE branches SET is_active = 1 WHERE id = %s", (existing['id'],))
                    flash(f"เปิดใช้งานสาขา '{branch_name}' อีกครั้งเรียบร้อยแล้ว", "success")
                else:
                    flash(f"สาขา '{branch_name}' มีอยู่ในระบบแล้ว", "warning")
            else:
                cursor.execute("INSERT INTO branches (name, is_active) VALUES (%s, 1)", (branch_name,))
                flash(f"เพิ่มสาขา '{branch_name}' เข้าสู่ระบบเรียบร้อยแล้ว", "success")
                if branch_name not in BRANCH_LIST:
                    BRANCH_LIST.append(branch_name)
        conn.close()
        invalidate_branch_cache()
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการเพิ่มสาขา: {e}", "error")

    return redirect(url_for('admin.admin_branches'))


@admin_bp.route('/admin/branches/delete', methods=['POST'])
@admin_required
def admin_delete_branch():
    branch_name = request.form.get('branch_name', '').strip()
    if not branch_name:
        flash("กรุณาระบุชื่อสาขาที่ต้องการลบ", "error")
        return redirect(url_for('admin.admin_branches'))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM branches WHERE name = %s", (branch_name,))
        conn.close()

        if branch_name in BRANCH_LIST:
            BRANCH_LIST.remove(branch_name)

        invalidate_branch_cache()
        flash(f"ลบสาขา '{branch_name}' ออกจากระบบเรียบร้อยแล้ว", "success")
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการลบสาขา: {e}", "error")

    return redirect(url_for('admin.admin_branches'))


@admin_bp.route('/admin/clear-data', methods=['POST'])
@admin_required
def admin_clear_data():
    success, msg = clear_all_report_data()
    if success:
        flash("ล้างข้อมูลรายงาน Morning Audit, Daily Report และไฟล์รูปภาพทั้งหมดเรียบร้อยแล้ว พร้อมสำหรับการทดสอบใหม่อีกครั้ง", "success")
    else:
        flash(f"เกิดข้อผิดพลาด: {msg}", "error")
    return redirect(url_for('dashboard.dashboard'))


# ================= USER MANAGEMENT & KORAT BRANCH ASSIGNMENT =================

@admin_bp.route('/admin/users', methods=['GET'])
@admin_required
def admin_users():
    """Admin User Management & Korat branch assignment page."""
    search_q = request.args.get('q', '').strip().upper()
    role_filter = request.args.get('role', 'ALL').strip()
    branch_filter = request.args.get('branch', 'ALL').strip()

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            try:
                cursor.execute("ALTER TABLE `users` ADD COLUMN `branch` VARCHAR(100) NULL DEFAULT NULL AFTER `role`;")
            except Exception:
                pass

            # Ensure ADMIN always has NULL branch because admin controls all branches
            cursor.execute("UPDATE users SET branch = NULL WHERE role = 'ADMIN' OR username = 'ADMIN'")

            cursor.execute("""
                SELECT id, username, role, branch, password_changed_at, is_first_login, created_at 
                FROM users 
                WHERE role != 'ADMIN' AND username != 'ADMIN'
                ORDER BY username ASC
            """)
            all_users = cursor.fetchall()
        conn.close()

        # Double check to ensure ADMIN account is never shown in the management list
        all_users = [u for u in all_users if u.get('role') != 'ADMIN' and u.get('username') != 'ADMIN']


        filtered_users = []
        for u in all_users:
            if search_q and search_q not in u['username']:
                continue
            if branch_filter != 'ALL':
                if u.get('branch') != branch_filter:
                    continue
            filtered_users.append(u)

        branches = get_all_branches()

        return render_template(
            'manage_users.html',
            users=filtered_users,
            branches=branches,
            search_q=search_q,
            branch_filter=branch_filter
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการโหลดข้อมูลผู้ใช้: {e}", "error")
        return redirect(url_for('dashboard.dashboard'))


@admin_bp.route('/admin/users/add', methods=['POST'])
@admin_required
def admin_add_user():
    """Add a new user account (Strictly USER role; ADMIN is a single central account)."""
    username = request.form.get('username', '').strip().upper()
    role = 'USER'
    branch = request.form.get('branch', '').strip() or None
    password = request.form.get('password', '').strip() or DEFAULT_INITIAL_PASSWORD

    is_valid, err_msg = validate_username(username)
    if not is_valid:
        flash(err_msg, "error")
        return redirect(url_for('admin.admin_users'))

    if username == 'ADMIN':
        flash("บัญชีผู้ดูแลระบบ ADMIN มีอยู่แล้วในระบบ และอนุญาตให้มีเพียง 1 บัญชีเท่านั้น", "warning")
        return redirect(url_for('admin.admin_users'))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash(f"มีชื่อผู้ใช้งาน '{username}' อยู่ในระบบแล้ว", "warning")
                conn.close()
                return redirect(url_for('admin.admin_users'))

            from werkzeug.security import generate_password_hash
            pw_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, branch, password_changed_at, is_first_login)
                VALUES (%s, %s, %s, %s, NOW(), 1)
            """, (username, pw_hash, role, branch))
        conn.close()

        flash(f"เพิ่มผู้ใช้งาน '{username}' เรียบร้อยแล้ว (รหัสผ่านเริ่มต้น: {password})", "success")
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการเพิ่มผู้ใช้งาน: {e}", "error")

    return redirect(url_for('admin.admin_users'))


@admin_bp.route('/admin/users/delete', methods=['POST'])
@admin_required
def admin_delete_user():
    """Delete a user account."""
    user_id = request.form.get('user_id', '').strip()
    if not user_id:
        flash("ไม่พบรหัสผู้ใช้งานที่ต้องการลบ", "error")
        return redirect(url_for('admin.admin_users'))

    try:
        user_id_int = int(user_id)
        if user_id_int == session.get('user_id'):
            flash("ไม่สามารถลบบัญชีผู้ใช้ที่กำลังเข้าสู่ระบบอยู่ได้", "error")
            return redirect(url_for('admin.admin_users'))

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, role FROM users WHERE id = %s", (user_id_int,))
            target = cursor.fetchone()
            if not target:
                flash("ไม่พบข้อมูลผู้ใช้งานที่ระบุ", "error")
                conn.close()
                return redirect(url_for('admin.admin_users'))

            if target['username'] == 'ADMIN' or target.get('role') == 'ADMIN':
                flash("ไม่อนุญาตให้ลบบัญชี ADMIN หลักของระบบ", "error")
                conn.close()
                return redirect(url_for('admin.admin_users'))

            cursor.execute("DELETE FROM users WHERE id = %s", (user_id_int,))
        conn.close()
        flash(f"ลบผู้ใช้งาน '{target['username']}' ออกจากระบบเรียบร้อยแล้ว (ข้อมูลรายงานและประวัติงานเดิมของผู้ใช้ยังคงอยู่ในระบบครบถ้วน)", "success")
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการลบผู้ใช้งาน: {e}", "error")

    return redirect(url_for('admin.admin_users'))


@admin_bp.route('/admin/users/reset-password', methods=['POST'])
@admin_required
def admin_reset_user_password():
    """Generates a random temporary password for a user and sets is_first_login = 1."""
    user_id = request.form.get('user_id', '').strip()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json

    if not user_id:
        if is_ajax:
            return jsonify({'success': False, 'error': 'ไม่พบรหัสผู้ใช้งานที่ต้องการรีเซ็ต'}), 400
        flash("ไม่พบรหัสผู้ใช้งานที่ต้องการรีเซ็ต", "error")
        return redirect(url_for('admin.admin_users'))

    try:
        user_id_int = int(user_id)
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, role FROM users WHERE id = %s", (user_id_int,))
            target = cursor.fetchone()
            if not target:
                conn.close()
                if is_ajax:
                    return jsonify({'success': False, 'error': 'ไม่พบข้อมูลผู้ใช้งานที่ระบุ'}), 404
                flash("ไม่พบข้อมูลผู้ใช้งานที่ระบุ", "error")
                return redirect(url_for('admin.admin_users'))

            if target['username'] == 'ADMIN' or target.get('role') == 'ADMIN':
                conn.close()
                if is_ajax:
                    return jsonify({'success': False, 'error': 'ไม่อนุญาตให้รีเซ็ทรหัสผ่านบัญชี ADMIN หลักผ่านเมนูนี้'}), 403
                flash("ไม่อนุญาตให้รีเซ็ทรหัสผ่านบัญชี ADMIN หลักผ่านเมนูนี้", "error")
                return redirect(url_for('admin.admin_users'))

            temp_password = generate_random_password(8)
            pw_hash = generate_password_hash(temp_password)

            cursor.execute(
                "UPDATE users SET password_hash = %s, is_first_login = 1, password_changed_at = NOW() WHERE id = %s",
                (pw_hash, user_id_int)
            )
        conn.close()

        if is_ajax:
            return jsonify({
                'success': True,
                'username': target['username'],
                'temp_password': temp_password,
                'message': f"รีเซ็ทรหัสผ่านสำหรับ {target['username']} เรียบร้อยแล้ว"
            })

        flash(f"รีเซ็ทรหัสผ่านสำหรับ '{target['username']}' สำเร็จ (รหัสผ่านสุ่มใหม่: {temp_password}) ผู้ใช้ต้องตั้งรหัสใหม่เมื่อเข้าสู่ระบบ", "success")
        return redirect(url_for('admin.admin_users'))

    except Exception as e:
        if is_ajax:
            return jsonify({'success': False, 'error': f"เกิดข้อผิดพลาด: {str(e)}"}), 500
        flash(f"เกิดข้อผิดพลาดในการรีเซ็ทรหัสผ่าน: {e}", "error")
        return redirect(url_for('admin.admin_users'))


@admin_bp.route('/admin/users/set-branch', methods=['POST'])
@admin_required
def admin_set_user_branch():
    """Update user branch or toggle Korat branch status."""
    user_id = request.form.get('user_id', '').strip()
    action = request.form.get('action', 'set_branch').strip()
    branch = request.form.get('branch', '').strip()

    if not user_id:
        flash("ไม่พบรหัสผู้ใช้งาน", "error")
        return redirect(url_for('admin.admin_users'))

    try:
        user_id_int = int(user_id)
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, role, branch FROM users WHERE id = %s", (user_id_int,))
            target = cursor.fetchone()
            if not target:
                flash("ไม่พบข้อมูลผู้ใช้งาน", "error")
                conn.close()
                return redirect(url_for('admin.admin_users'))

            if target['username'] == 'ADMIN' or target.get('role') == 'ADMIN':
                flash("ผู้ดูแลระบบ (ADMIN) ควบคุมและดูแลทุกสาขา ไม่จำเป็นต้องกำหนดสาขาประจำตัว", "warning")
                conn.close()
                return redirect(url_for('admin.admin_users'))

            new_branch = None
            new_branch = branch if branch else None
            if new_branch:
                msg = f"กำหนดสาขา '{new_branch}' ให้กับ '{target['username']}' เรียบร้อยแล้ว"
            else:
                msg = f"ยกเลิกการผูกสาขาสำหรับ '{target['username']}' เรียบร้อยแล้ว"

            cursor.execute("UPDATE users SET branch = %s WHERE id = %s", (new_branch, user_id_int))
        conn.close()

        if user_id_int == session.get('user_id'):
            session['branch'] = new_branch or ''

        flash(msg, "success")
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการกำหนดสาขา: {e}", "error")

    return redirect(url_for('admin.admin_users'))
