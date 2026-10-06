# -*- coding: utf-8 -*-
"""
Daily Operation Report Blueprint for LXP Sale Monitor (FM-MS-224 Rev.00).
Handles /daily-report, /daily-report/history, /daily-report/<id>, PDF generation, and photo uploads.
"""

import os
import re
import json
import base64
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    session, jsonify, send_file, current_app
)

from db import get_db_connection
from pdf_generator import generate_daily_report_pdf
from utils import (
    login_required,
    admin_required,
    get_all_branches,
    save_base64_photo,
    enrich_daily_report_with_linked_audit,
    analyze_staff_photo_with_gemini
)

daily_report_bp = Blueprint('daily_report', __name__)



@daily_report_bp.route('/daily-report/upload-photo', methods=['POST'])
@login_required
def upload_report_photo():
    """Accepts a single base64 photo via AJAX, optimizes and saves it as WebP, returns the file path."""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or 'photo' not in data:
            return jsonify({'success': False, 'error': 'No photo data'}), 400

        photo_b64 = data['photo']
        file_url = save_base64_photo(photo_b64, session.get('username', 'user'), prefix='report')
        if file_url:
            return jsonify({'success': True, 'path': file_url})
        return jsonify({'success': False, 'error': 'Failed to process image'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@daily_report_bp.route('/daily-report/check-exists')
@login_required
def check_daily_report_exists():
    """API to check if a report already exists for a branch and date."""
    branch = request.args.get('branch', '').strip()
    date_str = request.args.get('date', '').strip()
    if not branch or not date_str:
        return jsonify({'exists': False})

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, submitted_by, created_at FROM daily_operation_reports
                WHERE branch = %s AND report_date = %s
                ORDER BY id DESC LIMIT 1
            """, (branch, date_str))
            row = cursor.fetchone()
        conn.close()
        if row:
            return jsonify({
                'exists': True,
                'id': row['id'],
                'submitted_by': row.get('submitted_by', ''),
                'created_at': row['created_at'].strftime('%d/%m/%Y %H:%M') if row.get('created_at') else ''
            })
        return jsonify({'exists': False})
    except Exception as e:
        return jsonify({'exists': False, 'error': str(e)}), 500


@daily_report_bp.route('/daily-report', methods=['GET', 'POST'])
@login_required
def daily_report():
    today_str = datetime.now().strftime('%Y-%m-%d')
    is_admin = (session.get('role') == 'ADMIN')

    if request.method == 'POST':
        branch = request.form.get('branch', '').strip()
        team = request.form.get('team', '').strip()
        report_date = request.form.get('report_date', today_str).strip()

        if not branch:
            flash("กรุณาเลือกสาขา", "error")
            return render_template('daily_report.html', branches=get_all_branches(), today=today_str)

        # Check if already submitted for non-admin
        if not is_admin:
            try:
                conn_check = get_db_connection()
                with conn_check.cursor() as c_chk:
                    c_chk.execute("""
                        SELECT id, submitted_by FROM daily_operation_reports
                        WHERE branch = %s AND report_date = %s
                        ORDER BY id DESC LIMIT 1
                    """, (branch, report_date))
                    existing = c_chk.fetchone()
                conn_check.close()
                if existing:
                    flash(f"สาขา {branch} ได้ส่งรายงานการปฏิบัติงานประจำวันที่ {report_date} เรียบร้อยแล้ว", "warning")
                    return redirect(url_for('daily_report.daily_report_detail', report_id=existing['id']))
            except Exception as chk_err:
                print(f"Error checking existing daily report: {chk_err}")

        morning_brief = request.form.get('morning_brief', '').strip()
        if not morning_brief:
            mb_staff_list = request.form.getlist('mb_staff_initial[]')
            mb_detail_list = request.form.getlist('mb_detail[]')
            if mb_staff_list and mb_detail_list:
                brief_lines = []
                for s, d in zip(mb_staff_list, mb_detail_list):
                    s_clean = s.strip().upper()
                    d_clean = d.strip()
                    if s_clean and d_clean:
                        brief_lines.append(f"{s_clean}: {d_clean}")
                    elif s_clean:
                        brief_lines.append(f"{s_clean}:")
                    elif d_clean:
                        brief_lines.append(d_clean)
                morning_brief = "\n".join(brief_lines)

        daily_summary = request.form.get('daily_summary', '').strip()
        if not daily_summary:
            ds_staff_list = request.form.getlist('ds_staff_initial[]')
            ds_detail_list = request.form.getlist('ds_detail[]')
            if ds_staff_list and ds_detail_list:
                summary_lines = []
                for s, d in zip(ds_staff_list, ds_detail_list):
                    s_clean = s.strip().upper()
                    d_clean = d.strip()
                    if s_clean and d_clean:
                        summary_lines.append(f"{s_clean}: {d_clean}")
                    elif s_clean:
                        summary_lines.append(f"{s_clean}:")
                    elif d_clean:
                        summary_lines.append(d_clean)
                daily_summary = "\n".join(summary_lines)

        additional_tasks = request.form.get('additional_tasks', '').strip()

        manpower_data = {
            'total': {'qty': request.form.get('staff_total_qty', '0'), 'names': request.form.get('staff_total_names', '')},
            'offsite': {'qty': request.form.get('staff_offsite_qty', '0'), 'names': request.form.get('staff_offsite_names', '')},
            'booth': {'qty': request.form.get('staff_booth_qty', '0'), 'names': request.form.get('staff_booth_names', '')},
            'personal_leave': {'qty': request.form.get('staff_personal_leave_qty', '0'), 'names': request.form.get('staff_personal_leave_names', '')},
            'sick_leave': {'qty': request.form.get('staff_sick_leave_qty', '0'), 'names': request.form.get('staff_sick_leave_names', '')},
            'vacation_leave': {'qty': request.form.get('staff_vacation_leave_qty', '0'), 'names': request.form.get('staff_vacation_leave_names', '')},
            'dayoff': {'qty': request.form.get('staff_dayoff_qty', '0'), 'names': request.form.get('staff_dayoff_names', '')}
        }

        customer_stats = {
            'call_center': request.form.get('stat_call_center', '0'),
            'walk_in': request.form.get('stat_walk_in', '0'),
            'appointment': request.form.get('stat_appointment', '0'),
            'booking': request.form.get('stat_booking', '0'),
            'call_manager': request.form.get('stat_call_manager', '0'),
            'call_senior': request.form.get('stat_call_senior', '0')
        }

        team_staff = {
            'manager': request.form.get('staff_manager', ''),
            'manager_sig': request.form.get('staff_manager_sig', ''),
            'senior_sale': request.form.get('staff_senior_sale', ''),
            'senior_sale_sig': request.form.get('staff_senior_sale_sig', ''),
            'coordinator': request.form.get('staff_coordinator', ''),
            'coordinator_sig': request.form.get('staff_coordinator_sig', ''),
            'architect': request.form.get('staff_architect', ''),
            'architect_sig': request.form.get('staff_architect_sig', ''),
            'manager_sig_s1': request.form.get('manager_sig_s1', ''),
            'manager_name_s1': request.form.get('manager_name_s1', ''),
            'staff_manager_s2': request.form.get('staff_manager_s2', ''),
            'staff_manager_s2_sig': request.form.get('staff_manager_s2_sig', ''),
            'staff_senior_sale_s2': request.form.get('staff_senior_sale_s2', ''),
            'staff_senior_sale_s2_sig': request.form.get('staff_senior_sale_s2_sig', ''),
            'staff_coordinator_s2': request.form.get('staff_coordinator_s2', ''),
            'staff_coordinator_s2_sig': request.form.get('staff_coordinator_s2_sig', ''),
            'staff_architect_s2': request.form.get('staff_architect_s2', ''),
            'staff_architect_s2_sig': request.form.get('staff_architect_s2_sig', ''),
            'manager_sig_s2': request.form.get('manager_sig_s2', ''),
            'manager_name_s2': request.form.get('manager_name_s2', '')
        }

        # Process report photos if any
        report_photos_raw = request.form.get('report_photos_json', '[]')
        saved_photos = []
        try:
            photos_data = json.loads(report_photos_raw)
            if isinstance(photos_data, list):
                for photo_item in photos_data:
                    file_path = save_base64_photo(photo_item, session.get('username', 'user'), prefix='report')
                    if file_path:
                        saved_photos.append(file_path)
        except Exception as err:
            print(f"Error parsing report photos: {err}")

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO daily_operation_reports 
                    (branch, team, report_date, submitted_by, morning_brief, daily_summary, additional_tasks, manpower_data, customer_stats, team_staff, report_photos)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    branch, team, report_date, session.get('username'),
                    morning_brief, daily_summary, additional_tasks,
                    json.dumps(manpower_data, ensure_ascii=False),
                    json.dumps(customer_stats, ensure_ascii=False),
                    json.dumps(team_staff, ensure_ascii=False),
                    json.dumps(saved_photos, ensure_ascii=False)
                ))
                report_id = cursor.lastrowid
            conn.close()

            flash(f"บันทึกรายงานการปฏิบัติงานสำนักงานขาย สาขา {branch} เรียบร้อยแล้ว", "success")
            return redirect(url_for('daily_report.daily_report_detail', report_id=report_id))
        except Exception as e:
            flash(f"เกิดข้อผิดพลาดในการบันทึกรายงาน: {e}", "error")

    user_branch = session.get('branch')
    already_submitted_report = None
    if user_branch and not is_admin:
        try:
            conn_check = get_db_connection()
            with conn_check.cursor() as c_chk:
                c_chk.execute("""
                    SELECT id, report_date, submitted_by, created_at FROM daily_operation_reports
                    WHERE branch = %s AND report_date = %s
                    ORDER BY id DESC LIMIT 1
                """, (user_branch, today_str))
                already_submitted_report = c_chk.fetchone()
            conn_check.close()
        except Exception as e:
            print(f"Error checking today report: {e}")

    return render_template(
        'daily_report.html',
        branches=get_all_branches(),
        today=today_str,
        selected_branch=user_branch,
        already_submitted_report=already_submitted_report
    )


@daily_report_bp.route('/daily-report/history')
@login_required
def daily_report_history():
    branch_filter = request.args.get('branch', 'ALL')
    date_filter = request.args.get('date', '').strip()
    search_query = request.args.get('q', '').strip()

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = "SELECT id, branch, team, report_date, submitted_by, report_photos, is_verified, headcount_checked, dress_code_checked, verified_by, verified_at, created_at FROM daily_operation_reports WHERE 1=1"
            params = []

            if session.get('role') != 'ADMIN':
                query += " AND submitted_by = %s"
                params.append(session.get('username'))

            if branch_filter != 'ALL':
                branch_keyword = branch_filter.replace("สาขา", "").split("(")[0].strip()
                query += " AND (branch = %s OR branch LIKE %s OR %s LIKE CONCAT('%%', branch, '%%'))"
                params.extend([branch_filter, f"%{branch_keyword}%", branch_filter])

            if date_filter:
                query += " AND report_date = %s"
                params.append(date_filter)

            if search_query:
                query += " AND (branch LIKE %s OR submitted_by LIKE %s)"
                term = f"%{search_query}%"
                params.extend([term, term])

            query += " ORDER BY id ASC"
            cursor.execute(query, tuple(params))
            reports = cursor.fetchall()
            for r in reports:
                try:
                    p_list = json.loads(r['report_photos']) if r.get('report_photos') else []
                    r['photos_count'] = len(p_list) if isinstance(p_list, list) else 0
                    r['photos_list'] = p_list if isinstance(p_list, list) else []
                except Exception:
                    r['photos_count'] = 0
                    r['photos_list'] = []
        conn.close()
        return render_template(
            'daily_report_history.html',
            reports=reports,
            branches=get_all_branches(),
            current_branch=branch_filter,
            current_date=date_filter,
            search_query=search_query
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการโหลดประวัติ: {e}", "error")
        return render_template(
            'daily_report_history.html',
            reports=[],
            branches=get_all_branches(),
            current_branch=branch_filter,
            current_date=date_filter,
            search_query=search_query
        )


@daily_report_bp.route('/daily-report/<int:report_id>')
@login_required
def daily_report_detail(report_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM daily_operation_reports WHERE id = %s", (report_id,))
            report = cursor.fetchone()
        
        if not report:
            conn.close()
            flash("ไม่พบข้อมูลรายงานการปฏิบัติงานที่ระบุ", "error")
            return redirect(url_for('daily_report.daily_report_history'))

        manpower_data = json.loads(report['manpower_data']) if report.get('manpower_data') else {}
        customer_stats = json.loads(report['customer_stats']) if report.get('customer_stats') else {}
        team_staff = json.loads(report['team_staff']) if report.get('team_staff') else {}
        report_photos = json.loads(report['report_photos']) if report.get('report_photos') else []

        # Auto-merge Section 1 from linked Morning Audit if submitted there
        report, manpower_data, team_staff, report_photos = enrich_daily_report_with_linked_audit(
            conn, report, manpower_data, team_staff, report_photos
        )
        conn.close()

        # Calculate actual onsite staff from Section 1 (Total - Leaves)
        total_qty = 0
        try:
            total_qty = int(float(str(manpower_data.get('total', {}).get('qty', 0) or 0).strip()))
        except Exception:
            total_qty = 0

        leaves_qty = 0
        for lk in ['personal_leave', 'sick_leave', 'vacation_leave', 'dayoff']:
            try:
                leaves_qty += int(float(str(manpower_data.get(lk, {}).get('qty', 0) or 0).strip()))
            except Exception:
                pass

        onsite_staff_count = max(0, total_qty - leaves_qty) if total_qty > 0 else 0

        return render_template(
            'daily_report_detail.html',
            report=report,
            manpower=manpower_data,
            stats=customer_stats,
            team_staff=team_staff,
            report_photos=report_photos,
            onsite_staff_count=onsite_staff_count
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการโหลดรายละเอียด: {e}", "error")
        return redirect(url_for('daily_report.daily_report_history'))


@daily_report_bp.route('/daily-report/<int:report_id>/verify', methods=['POST'])
@daily_report_bp.route('/daily-report/<int:report_id>/verify-dress-code', methods=['POST'])
@admin_required
def daily_report_verify(report_id):
    """AJAX endpoint for Admin to verify headcount and dress code checkboxes."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        is_verified = bool(data.get('is_verified', data.get('checked', False)))
        headcount_checked = bool(data.get('headcount_checked', False))
        dress_code_checked = bool(data.get('dress_code_checked', False))
        admin_name = session.get('username', 'ADMIN')

        conn = get_db_connection()
        with conn.cursor() as cursor:
            if is_verified:
                cursor.execute("""
                    UPDATE daily_operation_reports 
                    SET is_verified = 1, headcount_checked = %s, dress_code_checked = %s, verified_by = %s, verified_at = NOW() 
                    WHERE id = %s
                """, (1 if headcount_checked else 0, 1 if dress_code_checked else 0, admin_name, report_id))
            else:
                cursor.execute("""
                    UPDATE daily_operation_reports 
                    SET is_verified = 0, verified_by = NULL, verified_at = NULL 
                    WHERE id = %s
                """, (report_id,))

            # Fetch updated values
            cursor.execute("SELECT is_verified, headcount_checked, dress_code_checked, verified_by, verified_at FROM daily_operation_reports WHERE id = %s", (report_id,))
            updated_row = cursor.fetchone()
        conn.close()

        v_at_str = updated_row['verified_at'].strftime('%d/%m/%Y %H:%M') if updated_row and updated_row['verified_at'] else None
        return jsonify({
            'success': True,
            'is_verified': bool(updated_row['is_verified']) if updated_row else False,
            'headcount_checked': bool(updated_row['headcount_checked']) if updated_row else False,
            'dress_code_checked': bool(updated_row['dress_code_checked']) if updated_row else False,
            'verified_by': updated_row['verified_by'] if updated_row else None,
            'verified_at': v_at_str,
            'message': 'บันทึกการตรวจสอบเรียบร้อยแล้ว' if is_verified else 'ยกเลิกการตรวจสอบแล้ว'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@daily_report_bp.route('/daily-report/<int:report_id>/ai-staff-analysis', methods=['POST'])
@login_required
def daily_report_ai_staff_analysis(report_id):
    """Triggers Gemini Vision to analyze attached staff photos for headcount & dress code."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM daily_operation_reports WHERE id = %s", (report_id,))
            report = cursor.fetchone()
        
        if not report:
            conn.close()
            return jsonify({'success': False, 'error': 'ไม่พบรายงานที่ระบุ'}), 404

        manpower_data = json.loads(report['manpower_data']) if report.get('manpower_data') else {}
        customer_stats = json.loads(report['customer_stats']) if report.get('customer_stats') else {}
        team_staff = json.loads(report['team_staff']) if report.get('team_staff') else {}
        report_photos = json.loads(report['report_photos']) if report.get('report_photos') else []

        # Auto-merge Section 1 from linked Morning Audit if photos/manpower exist there
        report, manpower_data, team_staff, report_photos = enrich_daily_report_with_linked_audit(
            conn, report, manpower_data, team_staff, report_photos
        )
        conn.close()

        reported_count = manpower_data.get('total', {}).get('qty', 0) if isinstance(manpower_data, dict) else 0

        # Run AI Vision analysis
        analysis_result = analyze_staff_photo_with_gemini(report_photos, reported_count=reported_count)

        # Save to database
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE daily_operation_reports 
                SET ai_staff_analysis = %s 
                WHERE id = %s
            """, (json.dumps(analysis_result, ensure_ascii=False), report_id))
        conn.close()

        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'message': 'วิเคราะห์ภาพถ่ายพนักงานด้วย AI สำเร็จ'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@daily_report_bp.route('/daily-report/<int:report_id>/pdf')
@login_required
def daily_report_pdf(report_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM daily_operation_reports WHERE id = %s", (report_id,))
            report = cursor.fetchone()

        if not report:
            conn.close()
            flash("ไม่พบข้อมูลรายงานการปฏิบัติงานที่ระบุ", "error")
            return redirect(url_for('daily_report.daily_report_history'))

        manpower_data = json.loads(report['manpower_data']) if report.get('manpower_data') else {}
        customer_stats = json.loads(report['customer_stats']) if report.get('customer_stats') else {}
        team_staff = json.loads(report['team_staff']) if report.get('team_staff') else {}
        report_photos = json.loads(report['report_photos']) if report.get('report_photos') else []

        # Auto-merge Section 1 from linked Morning Audit if needed
        report, manpower_data, team_staff, report_photos = enrich_daily_report_with_linked_audit(
            conn, report, manpower_data, team_staff, report_photos
        )
        conn.close()

        pdf_buffer = generate_daily_report_pdf(report, manpower_data, customer_stats, team_staff, report_photos=[])

        clean_branch = report.get('branch', 'DailyReport').replace(' ', '_').replace('/', '_')
        report_date = str(report.get('report_date', ''))
        filename = f"Daily_Report_{report_id}_{clean_branch}_{report_date}.pdf"

        is_export = request.args.get('export') == '1' or request.args.get('download') == '1'
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=is_export,
            download_name=filename
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการสร้างไฟล์ PDF: {e}", "error")
        return redirect(url_for('daily_report.daily_report_detail', report_id=report_id))
