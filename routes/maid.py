# -*- coding: utf-8 -*-
"""
Maid Work Schedule Blueprint for LXP Sale Monitor.
Handles /maid-schedule, /maid-schedule/history, /maid-schedule/<id>, and PDF generation.
"""

import os
import json
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    session, jsonify, send_file, current_app
)

from db import get_db_connection
from maid_config import (
    MAID_DAILY_TASKS, MAID_WEEKLY_TASKS,
    format_month_year_th, get_days_in_month,
    get_weekly_schedule_layout, get_active_week_info
)
from utils import login_required, admin_required, get_all_branches
from pdf_generator import generate_maid_schedule_pdf

maid_bp = Blueprint('maid', __name__)


def check_korat_or_admin_permission():
    """Checks if the current user is ADMIN or assigned to Korat branch."""
    if session.get('role') == 'ADMIN':
        return True
    user_branch = session.get('branch', '') or ''
    return 'โคราช' in user_branch


@maid_bp.route('/maid-schedule', methods=['GET', 'POST'])
@login_required
def maid_schedule():
    if not check_korat_or_admin_permission():
        return redirect(url_for('dashboard.dashboard'))

    branches = get_all_branches()
    today = datetime.now()
    default_month = today.strftime('%Y-%m')
    is_admin = (session.get('role') == 'ADMIN')

    if request.method == 'POST':
        # Non-admins are strictly locked to 4B โคราช
        if not is_admin:
            branch = '4B โคราช'
        else:
            branch = request.form.get('branch', '4B โคราช').strip()
        month_year = request.form.get('month_year', default_month).strip()
        sheet_data_raw = request.form.get('sheet_data_json', '{}')

        if not branch:
            flash("กรุณาเลือกสาขา", "error")
            return redirect(url_for('maid.maid_schedule', branch=branch, month=month_year))

        # Check if record already exists and user is not ADMIN
        if session.get('role') != 'ADMIN':
            try:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, submitted_by FROM maid_schedules 
                        WHERE branch = %s AND month_year = %s
                    """, (branch, month_year))
                    existing_sch = cursor.fetchone()
                conn.close()
                if existing_sch:
                    flash(f"ตารางการทำงานแม่บ้าน สาขา {branch} ประจำเดือน {format_month_year_th(month_year)} ได้รับการบันทึกแล้ว ฝั่งผู้ใช้งานไม่สามารถแก้ไขได้", "warning")
                    return redirect(url_for('maid.maid_schedule', branch=branch, month=month_year))
            except Exception as e:
                print(f"Error checking existing maid schedule: {e}")

        try:
            # Validate JSON
            parsed_data = json.loads(sheet_data_raw)
        except Exception:
            parsed_data = {}

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO maid_schedules (branch, month_year, submitted_by, data_json)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        data_json = VALUES(data_json),
                        submitted_by = VALUES(submitted_by),
                        updated_at = NOW()
                """, (
                    branch,
                    month_year,
                    session.get('username', 'USER'),
                    json.dumps(parsed_data, ensure_ascii=False)
                ))
            conn.close()

            flash(f"บันทึกตารางการทำงานแม่บ้าน สาขา {branch} ประจำเดือน {format_month_year_th(month_year)} เรียบร้อยแล้ว", "success")
            return redirect(url_for('maid.maid_schedule', branch=branch, month=month_year))
        except Exception as e:
            flash(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}", "error")
            return redirect(url_for('maid.maid_schedule', branch=branch, month=month_year))

    # GET Request
    if not is_admin:
        selected_branch = '4B โคราช'
    else:
        selected_branch = request.args.get('branch', '4B โคราช').strip()
        if not selected_branch and branches:
            selected_branch = '4B โคราช'

    selected_month = request.args.get('month', default_month).strip()
    if len(selected_month) != 7 or '-' not in selected_month:
        selected_month = default_month

    days_in_month = get_days_in_month(selected_month)
    is_curr_m = (selected_month == default_month)
    is_admin = (session.get('role') == 'ADMIN')
    weekly_layout = get_weekly_schedule_layout(
        selected_month,
        today_day=today.day,
        is_current_month=is_curr_m,
        is_admin=is_admin
    )
    active_week_info = get_active_week_info(
        selected_month,
        today_day=today.day,
        is_current_month=is_curr_m
    )

    # Load existing sheet data if in database
    existing_data = {}
    schedule_id = None
    submitted_by = None
    updated_at = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, data_json, updated_at, submitted_by 
                FROM maid_schedules 
                WHERE branch = %s AND month_year = %s
            """, (selected_branch, selected_month))
            row = cursor.fetchone()
            if row and row.get('data_json'):
                schedule_id = row['id']
                existing_data = json.loads(row['data_json'])
                submitted_by = row.get('submitted_by')
                updated_at = row.get('updated_at')
        conn.close()
    except Exception as e:
        print(f"Error fetching existing maid schedule: {e}")

    is_locked = bool(schedule_id and not is_admin)

    return render_template(
        'maid_schedule.html',
        branches=branches,
        selected_branch=selected_branch,
        selected_month=selected_month,
        selected_month_th=format_month_year_th(selected_month),
        days_in_month=days_in_month,
        daily_tasks=MAID_DAILY_TASKS,
        weekly_tasks=MAID_WEEKLY_TASKS,
        weekly_layout=weekly_layout,
        active_week_info=active_week_info,
        sheet_data=existing_data,
        schedule_id=schedule_id,
        today_day=today.day,
        is_current_month=is_curr_m,
        is_admin=is_admin,
        is_locked=is_locked,
        submitted_by=submitted_by,
        updated_at=updated_at
    )


@maid_bp.route('/maid-schedule/history')
@login_required
def maid_schedule_history():
    if not check_korat_or_admin_permission():
        return redirect(url_for('dashboard.dashboard'))

    is_admin = (session.get('role') == 'ADMIN')
    branch_filter = request.args.get('branch', '4B โคราช' if not is_admin else 'ALL')
    if not is_admin:
        branch_filter = '4B โคราช'
    month_filter = request.args.get('month', '').strip()
    search_query = request.args.get('q', '').strip()

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = "SELECT id, branch, month_year, submitted_by, created_at, updated_at, data_json FROM maid_schedules WHERE 1=1"
            params = []

            if branch_filter != 'ALL':
                query += " AND branch = %s"
                params.append(branch_filter)

            if month_filter:
                query += " AND month_year = %s"
                params.append(month_filter)

            if search_query:
                query += " AND (branch LIKE %s OR submitted_by LIKE %s)"
                term = f"%{search_query}%"
                params.extend([term, term])

            query += " ORDER BY month_year DESC, branch ASC"
            cursor.execute(query, tuple(params))
            schedules = cursor.fetchall()

            for s in schedules:
                s['month_th'] = format_month_year_th(s.get('month_year', ''))
                # Count total checks
                try:
                    data = json.loads(s.get('data_json', '{}'))
                    daily_checks = sum(1 for k, v in data.get('daily', {}).items() if v)
                    weekly_checks = sum(1 for k, v in data.get('weekly', {}).items() if v)
                    s['total_checks'] = daily_checks + weekly_checks
                except Exception:
                    s['total_checks'] = 0

        conn.close()
        return render_template(
            'maid_schedule_history.html',
            schedules=schedules,
            branches=get_all_branches(),
            current_branch=branch_filter,
            current_month=month_filter,
            search_query=search_query
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการโหลดประวัติ: {e}", "error")
        return render_template(
            'maid_schedule_history.html',
            schedules=[],
            branches=get_all_branches(),
            current_branch=branch_filter,
            current_month=month_filter,
            search_query=search_query
        )


@maid_bp.route('/maid-schedule/<int:schedule_id>')
@login_required
def maid_schedule_detail(schedule_id):
    if not check_korat_or_admin_permission():
        return redirect(url_for('dashboard.dashboard'))
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM maid_schedules WHERE id = %s", (schedule_id,))
            schedule = cursor.fetchone()
        conn.close()

        if not schedule:
            flash("ไม่พบข้อมูลตารางการทำงานแม่บ้านที่ระบุ", "error")
            return redirect(url_for('maid.maid_schedule_history'))

        sheet_data = json.loads(schedule.get('data_json', '{}'))
        month_year = schedule.get('month_year', '')
        days_in_month = get_days_in_month(month_year)
        weekly_layout = get_weekly_schedule_layout(month_year)

        return render_template(
            'maid_schedule_detail.html',
            schedule=schedule,
            sheet_data=sheet_data,
            month_th=format_month_year_th(month_year),
            days_in_month=days_in_month,
            daily_tasks=MAID_DAILY_TASKS,
            weekly_tasks=MAID_WEEKLY_TASKS,
            weekly_layout=weekly_layout
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการโหลดรายละเอียด: {e}", "error")
        return redirect(url_for('maid.maid_schedule_history'))


@maid_bp.route('/maid-schedule/<int:schedule_id>/pdf')
@login_required
def maid_schedule_pdf(schedule_id):
    if not check_korat_or_admin_permission():
        return redirect(url_for('dashboard.dashboard'))
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM maid_schedules WHERE id = %s", (schedule_id,))
            schedule = cursor.fetchone()
        conn.close()

        if not schedule:
            flash("ไม่พบข้อมูลตารางการทำงานแม่บ้านที่ระบุ", "error")
            return redirect(url_for('maid.maid_schedule_history'))

        sheet_data = json.loads(schedule.get('data_json', '{}'))
        pdf_buffer = generate_maid_schedule_pdf(schedule, sheet_data)

        clean_branch = schedule.get('branch', 'Maid').replace(' ', '_').replace('/', '_')
        month_year = str(schedule.get('month_year', ''))
        filename = f"Maid_Schedule_{schedule_id}_{clean_branch}_{month_year}.pdf"

        is_export = request.args.get('export') == '1' or request.args.get('download') == '1'
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=is_export,
            download_name=filename
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการสร้างไฟล์ PDF: {e}", "error")
        return redirect(url_for('maid.maid_schedule_detail', schedule_id=schedule_id))
