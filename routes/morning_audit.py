# -*- coding: utf-8 -*-
"""
Morning Audit Blueprint for LXP Sale Monitor (FM-MS-007 Rev.00).
Handles /morning-audit, /morning-audit/history, /morning-audit/<id>, PDF generation, and AI analysis.
"""

import os
import re
import json
import base64
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    session, send_file, current_app, jsonify
)

from db import get_db_connection
from audit_config import MORNING_AUDIT_STRUCTURE, TOTAL_AUDIT_ITEMS
from pdf_generator import generate_morning_audit_pdf
from utils import (
    login_required, admin_required, get_all_branches,
    generate_morning_audit_ai_analysis, save_base64_photo,
    analyze_staff_photo_with_gemini
)

morning_audit_bp = Blueprint('morning_audit', __name__)


@morning_audit_bp.route('/morning-audit/upload-photo', methods=['POST'])
@login_required
def upload_audit_photo():
    """Accepts a single base64 photo via AJAX, optimizes and saves it as WebP, returns the file path."""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or 'photo' not in data:
            return jsonify({'success': False, 'error': 'No photo data'}), 400

        photo_b64 = data['photo']
        file_url = save_base64_photo(photo_b64, session.get('username', 'user'), prefix='audit')
        if file_url:
            return jsonify({'success': True, 'path': file_url})
        return jsonify({'success': False, 'error': 'Failed to process image'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@morning_audit_bp.route('/morning-audit/check-exists')
@login_required
def check_morning_audit_exists():
    """AJAX check to see if an audit has already been submitted for a branch and date."""
    branch = request.args.get('branch', '').strip()
    audit_date = request.args.get('date', '').strip()
    if not branch or not audit_date:
        return jsonify({'exists': False})

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, submitted_by, created_at 
                FROM morning_audits 
                WHERE branch = %s AND audit_date = %s 
                ORDER BY id DESC LIMIT 1
            """, (branch, audit_date))
            row = cursor.fetchone()
        conn.close()

        if row:
            c_at_str = row['created_at'].strftime('%H:%M น.') if row.get('created_at') else ''
            return jsonify({
                'exists': True,
                'id': row['id'],
                'submitted_by': row.get('submitted_by', ''),
                'created_at': c_at_str
            })
    except Exception as e:
        print(f"Error in check_morning_audit_exists: {e}")
    return jsonify({'exists': False})


@morning_audit_bp.route('/morning-audit', methods=['GET', 'POST'])
@login_required
def morning_audit():
    today_str = datetime.now().strftime('%Y-%m-%d')
    if request.method == 'POST':
        branch = request.form.get('branch', '').strip()
        audit_date = request.form.get('audit_date', today_str).strip()
        material_room_note = request.form.get('material_room_note', '').strip()

        # Check if already submitted and user is not ADMIN
        if session.get('role') != 'ADMIN':
            try:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, submitted_by, created_at 
                        FROM morning_audits 
                        WHERE branch = %s AND audit_date = %s
                        ORDER BY id DESC LIMIT 1
                    """, (branch, audit_date))
                    existing_audit = cursor.fetchone()
                conn.close()
                if existing_audit:
                    flash(f"สาขา {branch} ได้ทำการส่ง Morning Audit ประจำวันที่ {audit_date} เรียบร้อยแล้ว ฝั่งผู้ใช้งานไม่สามารถแก้ไขหรือส่งซ้ำได้", "warning")
                    return redirect(url_for('morning_audit.morning_audit_detail', audit_id=existing_audit['id']))
            except Exception as e:
                print(f"Error checking existing morning audit: {e}")

        if not branch:
            flash("กรุณาเลือกสาขาที่ทำการตรวจ", "error")
            return render_template(
                'morning_audit.html',
                sections=MORNING_AUDIT_STRUCTURE,
                branches=get_all_branches(),
                total_items=TOTAL_AUDIT_ITEMS,
                today=today_str,
                selected_branch=branch,
                selected_date=audit_date
            )

        audit_records = []
        passed_count = 0
        failed_count = 0

        for cat in MORNING_AUDIT_STRUCTURE:
            cat_data = {
                "category_id": cat["category_id"],
                "category_title": cat["category_title"],
                "audit_items": []
            }
            for item in cat["audit_items"]:
                status = request.form.get(f"status_{item['id']}", "PASS")
                evidence_data = {}
                
                if status == 'FAIL':
                    failed_count += 1
                    for field in item["evidence_fields"]:
                        evidence_data[field["name"]] = request.form.get(field["name"], '').strip()
                else:
                    status = 'PASS'
                    passed_count += 1

                cat_data["audit_items"].append({
                    "id": item["id"],
                    "no": item["no"],
                    "title": item["title"],
                    "status": status,
                    "evidence_fields": item["evidence_fields"],
                    "evidence": evidence_data
                })
            audit_records.append(cat_data)

        total_counted = passed_count + failed_count

        # Manpower data
        manpower_data = {
            'total': {'qty': request.form.get('staff_total_qty', '').strip(), 'names': request.form.get('staff_total_names', '').strip()},
            'offsite': {'qty': request.form.get('staff_offsite_qty', '').strip(), 'names': request.form.get('staff_offsite_names', '').strip()},
            'booth': {'qty': request.form.get('staff_booth_qty', '').strip(), 'names': request.form.get('staff_booth_names', '').strip()},
            'personal_leave': {'qty': request.form.get('staff_personal_leave_qty', '').strip(), 'names': request.form.get('staff_personal_leave_names', '').strip()},
            'sick_leave': {'qty': request.form.get('staff_sick_leave_qty', '').strip(), 'names': request.form.get('staff_sick_leave_names', '').strip()},
            'vacation_leave': {'qty': request.form.get('staff_vacation_leave_qty', '').strip(), 'names': request.form.get('staff_vacation_leave_names', '').strip()},
            'dayoff': {'qty': request.form.get('staff_dayoff_qty', '').strip(), 'names': request.form.get('staff_dayoff_names', '').strip()}
        }

        # Morning Brief & Signatures
        morning_brief = request.form.get('morning_brief', '').strip()
        team_staff = {
            'manager': request.form.get('staff_manager', '').strip(),
            'manager_sig': request.form.get('staff_manager_sig', '').strip(),
            'senior_sale': request.form.get('staff_senior_sale', '').strip(),
            'senior_sale_sig': request.form.get('staff_senior_sale_sig', '').strip(),
            'coordinator': request.form.get('staff_coordinator', '').strip(),
            'coordinator_sig': request.form.get('staff_coordinator_sig', '').strip(),
            'architect': request.form.get('staff_architect', '').strip(),
            'architect_sig': request.form.get('staff_architect_sig', '').strip(),
            'manager_s1': request.form.get('manager_name_s1', '').strip(),
            'manager_s1_sig': request.form.get('manager_sig_s1', '').strip(),
        }

        # Process photos if any
        audit_photos_raw = request.form.get('audit_photos_json') or request.form.get('report_photos_json') or '[]'
        saved_photos = []
        try:
            photos_data = json.loads(audit_photos_raw)
            if isinstance(photos_data, list):
                for photo_item in photos_data:
                    file_path = save_base64_photo(photo_item, session.get('username', 'user'), prefix='audit')
                    if file_path:
                        saved_photos.append(file_path)
        except Exception as err:
            print(f"Error parsing audit photos: {err}")

        # Validate mandatory 7 photos
        if len(saved_photos) < 7:
            flash(f"กรุณาใช้กล้องถ่ายรูปรายงานการตรวจให้ครบอย่างน้อย 7 รูปก่อนบันทึก (ปัจจุบันบันทึกได้ {len(saved_photos)} / 7 รูป)", "warning")
            return render_template(
                'morning_audit.html',
                sections=MORNING_AUDIT_STRUCTURE,
                branches=get_all_branches(),
                total_items=TOTAL_AUDIT_ITEMS,
                today=today_str,
                selected_branch=branch,
                selected_date=audit_date
            )
        saved_photos = saved_photos[:7]

        full_audit_payload = {
            'sections': audit_records,
            'manpower': manpower_data,
            'morning_brief': morning_brief,
            'team_staff': team_staff,
            'audit_photos': saved_photos
        }

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO morning_audits 
                    (branch, audit_date, submitted_by, total_items, passed_items, failed_items, material_room_note, audit_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    branch,
                    audit_date,
                    session.get('username'),
                    total_counted,
                    passed_count,
                    failed_count,
                    material_room_note,
                    json.dumps(full_audit_payload, ensure_ascii=False)
                ))
                new_audit_id = cursor.lastrowid
            conn.close()

            flash(f"บันทึกผลการตรวจ Morning Audit สาขา {branch} พร้อมแนบรูปถ่ายเรียบร้อยแล้ว (ผ่าน {passed_count}/{total_counted} รายการ)", "success")
            return redirect(url_for('morning_audit.morning_audit_detail', audit_id=new_audit_id))
        except Exception as e:
            flash(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}", "error")

    branches = get_all_branches()
    user_name = session.get('username', '')
    matching = [b for b in branches if user_name in b]
    default_branch = matching[0] if matching else (branches[0] if branches else '')
    selected_branch = request.args.get('branch', default_branch).strip()
    selected_date = request.args.get('date', today_str).strip()

    already_submitted_audit = None
    if selected_branch and session.get('role') != 'ADMIN':
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, submitted_by, created_at 
                    FROM morning_audits 
                    WHERE branch = %s AND audit_date = %s 
                    ORDER BY id DESC LIMIT 1
                """, (selected_branch, selected_date))
                already_submitted_audit = cursor.fetchone()
            conn.close()
        except Exception as e:
            print(f"Error checking pre-existing audit: {e}")

    return render_template(
        'morning_audit.html',
        sections=MORNING_AUDIT_STRUCTURE,
        branches=branches,
        total_items=TOTAL_AUDIT_ITEMS,
        today=today_str,
        selected_branch=selected_branch,
        selected_date=selected_date,
        already_submitted_audit=already_submitted_audit
    )


@morning_audit_bp.route('/morning-audit/history')
@login_required
def morning_audit_history():
    branch_filter = request.args.get('branch', 'ALL')
    date_filter = request.args.get('date', '').strip()
    search_query = request.args.get('q', '').strip()

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = "SELECT id, branch, audit_date, submitted_by, total_items, passed_items, failed_items, audit_data, ai_analysis, ai_staff_analysis, is_verified, headcount_checked, dress_code_checked, verified_by, verified_at, created_at FROM morning_audits WHERE 1=1"
            params = []

            if session.get('role') != 'ADMIN':
                query += " AND submitted_by = %s"
                params.append(session.get('username'))

            if branch_filter != 'ALL':
                branch_keyword = branch_filter.replace("สาขา", "").split("(")[0].strip()
                query += " AND (branch = %s OR branch LIKE %s OR %s LIKE CONCAT('%%', branch, '%%'))"
                params.extend([branch_filter, f"%{branch_keyword}%", branch_filter])

            if date_filter:
                query += " AND audit_date = %s"
                params.append(date_filter)

            if search_query:
                query += " AND (branch LIKE %s OR submitted_by LIKE %s)"
                term = f"%{search_query}%"
                params.extend([term, term])

            query += " ORDER BY id ASC"
            cursor.execute(query, tuple(params))
            audits = cursor.fetchall()

            for a in audits:
                try:
                    pdata = json.loads(a.get('audit_data', '{}'))
                    photos = pdata.get('audit_photos', []) if isinstance(pdata, dict) else []
                    a['photos'] = photos
                    a['photo_count'] = len(photos)
                except Exception:
                    a['photos'] = []
                    a['photo_count'] = 0
        conn.close()
        return render_template(
            'morning_audit_history.html',
            audits=audits,
            branches=get_all_branches(),
            current_branch=branch_filter,
            current_date=date_filter,
            search_query=search_query
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการโหลดประวัติ Morning Audit: {e}", "error")
        return render_template(
            'morning_audit_history.html',
            audits=[],
            branches=get_all_branches(),
            current_branch=branch_filter,
            current_date=date_filter,
            search_query=search_query
        )


@morning_audit_bp.route('/morning-audit/<int:audit_id>')
@login_required
def morning_audit_detail(audit_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM morning_audits WHERE id = %s", (audit_id,))
            audit = cursor.fetchone()
        conn.close()

        if not audit:
            flash("ไม่พบข้อมูลรายงาน Morning Audit ที่ระบุ", "error")
            return redirect(url_for('morning_audit.morning_audit_history'))

        parsed_data = json.loads(audit['audit_data'])
        if isinstance(parsed_data, dict) and 'sections' in parsed_data:
            audit_data = parsed_data['sections']
            daily_plan = {
                'manpower': parsed_data.get('manpower', {}),
                'morning_brief': parsed_data.get('morning_brief', ''),
                'team_staff': parsed_data.get('team_staff', {})
            }
            audit_photos = parsed_data.get('audit_photos', [])
        else:
            audit_data = parsed_data
            daily_plan = {}
            audit_photos = []

        # Parse AI staff analysis if present
        ai_staff_analysis = None
        if audit.get('ai_staff_analysis'):
            try:
                ai_staff_analysis = json.loads(audit['ai_staff_analysis'])
            except Exception:
                ai_staff_analysis = None

        return render_template(
            'morning_audit_detail.html',
            audit=audit,
            audit_data=audit_data,
            daily_plan=daily_plan,
            audit_photos=audit_photos,
            ai_staff_analysis=ai_staff_analysis
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการโหลดรายละเอียด: {e}", "error")
        return redirect(url_for('morning_audit.morning_audit_history'))


@morning_audit_bp.route('/morning-audit/<int:audit_id>/verify', methods=['POST'])
@morning_audit_bp.route('/morning-audit/<int:audit_id>/verify-dress-code', methods=['POST'])
@admin_required
def morning_audit_verify(audit_id):
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
                    UPDATE morning_audits 
                    SET is_verified = 1, headcount_checked = %s, dress_code_checked = %s, verified_by = %s, verified_at = NOW() 
                    WHERE id = %s
                """, (1 if headcount_checked else 0, 1 if dress_code_checked else 0, admin_name, audit_id))
            else:
                cursor.execute("""
                    UPDATE morning_audits 
                    SET is_verified = 0, verified_by = NULL, verified_at = NULL 
                    WHERE id = %s
                """, (audit_id,))

            # Fetch updated values
            cursor.execute("SELECT is_verified, headcount_checked, dress_code_checked, verified_by, verified_at FROM morning_audits WHERE id = %s", (audit_id,))
            updated_row = cursor.fetchone()
        conn.close()

        v_at_str = updated_row['verified_at'].strftime('%d/%m/%Y %H:%M') if updated_row and updated_row['verified_at'] else None
        
        if is_verified:
            hc_ok = bool(updated_row['headcount_checked'])
            dc_ok = bool(updated_row['dress_code_checked'])
            if hc_ok and dc_ok:
                msg = 'บันทึกการตรวจสอบเรียบร้อยแล้ว (ผ่านทั้งหมด)'
            elif not hc_ok and not dc_ok:
                msg = 'บันทึกผล: ไม่ผ่าน 2 รายการ'
            else:
                msg = 'บันทึกผล: ไม่ผ่าน 1 รายการ'
        else:
            msg = 'ยกเลิกการตรวจสอบแล้ว'

        return jsonify({
            'success': True,
            'is_verified': bool(updated_row['is_verified']) if updated_row else False,
            'headcount_checked': bool(updated_row['headcount_checked']) if updated_row else False,
            'dress_code_checked': bool(updated_row['dress_code_checked']) if updated_row else False,
            'verified_by': updated_row['verified_by'] if updated_row else None,
            'verified_at': v_at_str,
            'message': msg
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@morning_audit_bp.route('/morning-audit/<int:audit_id>/ai-staff-analysis', methods=['GET', 'POST'])
@login_required
def morning_audit_ai_staff_analysis(audit_id):
    """
    Returns cached AI staff analysis if available.
    Only re-analyzes with Gemini Vision when refresh=True or no cache exists.
    """
    try:
        # Check refresh parameter from query or JSON payload
        refresh = False
        if request.args.get('refresh', '0') == '1':
            refresh = True
        elif request.is_json:
            req_data = request.get_json(silent=True) or {}
            refresh = bool(req_data.get('refresh', False))

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM morning_audits WHERE id = %s", (audit_id,))
            audit = cursor.fetchone()
        conn.close()

        if not audit:
            return jsonify({'success': False, 'error': 'ไม่พบรายงานที่ระบุ'}), 404

        # If cached analysis exists and refresh is not requested, return cached
        if audit.get('ai_staff_analysis') and not refresh:
            try:
                cached_analysis = json.loads(audit['ai_staff_analysis'])
                return jsonify({
                    'success': True,
                    'is_cached': True,
                    'analysis': cached_analysis,
                    'message': 'โหลดผลวิเคราะห์รูปภาพพนักงานจากข้อมูลเดิม'
                })
            except Exception:
                pass  # Fall through to re-run if JSON corrupt

        parsed_data = json.loads(audit['audit_data']) if audit.get('audit_data') else {}
        audit_photos = parsed_data.get('audit_photos', []) if isinstance(parsed_data, dict) else []
        manpower = parsed_data.get('manpower', {}) if isinstance(parsed_data, dict) else {}
        
        try:
            total_staff = int(float(str(manpower.get('total', {}).get('qty', 0) or 0).strip()))
        except Exception:
            total_staff = 0

        leaves_total = 0
        for lk in ['personal_leave', 'sick_leave', 'vacation_leave', 'dayoff']:
            try:
                leaves_total += int(float(str(manpower.get(lk, {}).get('qty', 0) or 0).strip()))
            except Exception:
                pass

        reported_count = max(0, total_staff - leaves_total) if total_staff > 0 else 0

        # Run AI Vision analysis
        analysis_result = analyze_staff_photo_with_gemini(audit_photos, reported_count=reported_count)

        # Save to database
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE morning_audits 
                SET ai_staff_analysis = %s 
                WHERE id = %s
            """, (json.dumps(analysis_result, ensure_ascii=False), audit_id))
        conn.close()

        return jsonify({
            'success': True,
            'is_cached': False,
            'analysis': analysis_result,
            'message': 'วิเคราะห์ภาพถ่ายพนักงานด้วย AI สำเร็จ'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@morning_audit_bp.route('/morning-audit/<int:audit_id>/pdf')
@login_required
def morning_audit_pdf(audit_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM morning_audits WHERE id = %s", (audit_id,))
            audit = cursor.fetchone()
        conn.close()

        if not audit:
            flash("ไม่พบข้อมูลรายงาน Morning Audit ที่ระบุ", "error")
            return redirect(url_for('morning_audit.morning_audit_history'))

        parsed_data = json.loads(audit['audit_data'])
        if isinstance(parsed_data, dict) and 'sections' in parsed_data:
            audit_data = parsed_data['sections']
            daily_plan = {
                'manpower': parsed_data.get('manpower', {}),
                'morning_brief': parsed_data.get('morning_brief', ''),
                'team_staff': parsed_data.get('team_staff', {})
            }
            audit_photos = parsed_data.get('audit_photos', [])
        else:
            audit_data = parsed_data
            daily_plan = {}
            audit_photos = []

        pdf_buffer = generate_morning_audit_pdf(audit, audit_data, daily_plan, audit_photos)

        clean_branch = audit.get('branch', 'Audit').replace(' ', '_').replace('/', '_')
        audit_date = str(audit.get('audit_date', ''))
        filename = f"Morning_Audit_{audit_id}_{clean_branch}_{audit_date}.pdf"

        is_export = request.args.get('export') == '1' or request.args.get('download') == '1'
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=is_export,
            download_name=filename
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการสร้างไฟล์ PDF: {e}", "error")
        return redirect(url_for('morning_audit.morning_audit_detail', audit_id=audit_id))


@morning_audit_bp.route('/morning-audit/<int:audit_id>/ai-analysis')
@admin_required
def morning_audit_ai_analysis(audit_id):
    refresh = request.args.get('refresh', '0') == '1'
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM morning_audits WHERE id = %s", (audit_id,))
            report = cursor.fetchone()
        conn.close()

        if not report:
            flash("ไม่พบข้อมูลรายงาน Morning Audit ที่ระบุ", "error")
            return redirect(url_for('morning_audit.morning_audit_history'))

        total_items = report.get('total_items') or 36
        passed_items = report.get('passed_items') or 0
        failed_items = report.get('failed_items') or 0
        pass_pct = round((passed_items / total_items) * 100, 1) if total_items > 0 else 100.0
        fail_pct = round(100.0 - pass_pct, 1)

        # Parse failed items for structured display
        failed_items_details = []
        raw_adata = report.get('audit_data')
        try:
            adata = json.loads(raw_adata) if isinstance(raw_adata, str) else (raw_adata or [])
            if isinstance(adata, dict) and 'sections' in adata:
                adata = adata['sections']
            if isinstance(adata, list):
                for cat in adata:
                    cat_title = cat.get('category_title', 'หมวดการตรวจสอบ')
                    for itm in cat.get('audit_items', []):
                        st = str(itm.get('status') or itm.get('result') or '').upper().strip()
                        if st == 'FAIL':
                            ev = itm.get('evidence') or itm.get('fields') or {}
                            ev_details = [f"{k}: '{v}'" for k, v in ev.items() if str(v).strip()]
                            ev_str = ", ".join(ev_details) if ev_details else "ไม่ผ่านเกณฑ์มาตรฐาน"
                            failed_items_details.append({
                                "no": itm.get('no', '-'),
                                "title": itm.get('title', '-'),
                                "category": cat_title,
                                "defect_note": ev_str
                            })
        except Exception:
            pass

        is_cached = False
        ai_output_text = report.get('ai_analysis')

        if ai_output_text and not refresh:
            is_cached = True
        else:
            # Generate AI analysis with gemini-2.5-flash & fallback
            ai_output_text = generate_morning_audit_ai_analysis(report)
            is_cached = False

            # Cache into Database
            try:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE morning_audits SET ai_analysis = %s WHERE id = %s", (ai_output_text, audit_id))
                conn.close()
            except Exception as dbe:
                print("Error saving ai_analysis cache to DB:", dbe)

        stats_summary = {
            'total_items': total_items,
            'passed_items': passed_items,
            'failed_items': failed_items,
            'pass_pct': pass_pct,
            'fail_pct': fail_pct
        }

        return render_template(
            'morning_audit_ai_analysis.html',
            audit=report,
            stats=stats_summary,
            failed_items=failed_items_details,
            ai_output=ai_output_text,
            is_cached=is_cached
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการโหลดบทวิเคราะห์ AI: {e}", "error")
        return redirect(url_for('morning_audit.morning_audit_history'))


@morning_audit_bp.route('/ai-summarize', methods=['GET', 'POST'])
@morning_audit_bp.route('/ai/summarize', methods=['GET', 'POST'])
@admin_required
def ai_summarize():
    return redirect(url_for('morning_audit.morning_audit_history'))
