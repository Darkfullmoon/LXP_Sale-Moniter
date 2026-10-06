# -*- coding: utf-8 -*-
"""
Inspection & Inventory Blueprint for LXP Sale Monitor.
Handles /add-item, /inspection (review), /inspection/action/<id>, and /history.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from db import get_db_connection
from utils import login_required, admin_required

inspection_bp = Blueprint('inspection', __name__)


@inspection_bp.route('/add-item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        item_code = request.form.get('item_code', '').strip().upper()
        item_name = request.form.get('item_name', '').strip()
        category = request.form.get('category', '').strip()
        quantity_str = request.form.get('quantity', '1').strip()

        if not item_code or not item_name or not category:
            flash("กรุณากรอกข้อมูลรายการให้ครบถ้วน", "error")
            return render_template('add_item.html')

        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                quantity = 1
        except ValueError:
            flash("จำนวนต้องเป็นตัวเลขที่มากกว่า 0", "error")
            return render_template('add_item.html')

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO inspections (item_code, item_name, category, quantity, submitted_by, status)
                    VALUES (%s, %s, %s, %s, %s, 'PENDING')
                """, (item_code, item_name, category, quantity, session.get('username')))
            conn.close()

            flash(f"เพิ่มรายการ '{item_name}' (รหัส: {item_code}) เรียบร้อยแล้ว อยู่ในสถานะรอการตรวจสอบ", "success")
            return redirect(url_for('inspection.history'))
        except Exception as e:
            flash(f"เกิดข้อผิดพลาดในการเพิ่มรายการ: {str(e)}", "error")

    return render_template('add_item.html')


@inspection_bp.route('/inspection')
@admin_required
def inspection():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM inspections WHERE status = 'PENDING' ORDER BY created_at ASC")
            pending_list = cursor.fetchall()
        conn.close()
        return render_template('inspection.html', items=pending_list)
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการโหลดรายการตรวจสอบ: {e}", "error")
        return render_template('inspection.html', items=[])


@inspection_bp.route('/inspection/action/<int:item_id>', methods=['POST'])
@admin_required
def inspection_action(item_id):
    action = request.form.get('action')  # 'APPROVE' or 'REJECT'
    notes = request.form.get('notes', '').strip()

    if action not in ['APPROVE', 'REJECT']:
        flash("การกระทำไม่ถูกต้อง", "error")
        return redirect(url_for('inspection.inspection'))

    new_status = 'APPROVED' if action == 'APPROVE' else 'REJECTED'

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE inspections
                SET status = %s, inspector_notes = %s, inspected_by = %s, inspected_at = %s
                WHERE id = %s
            """, (new_status, notes, session.get('username'), datetime.now(), item_id))
        conn.close()

        status_text = "อนุมัติเรียบร้อยแล้ว" if action == 'APPROVE' else "ปฏิเสธรายการเรียบร้อยแล้ว"
        flash(f"บันทึกผลการตรวจสอบ ID #{item_id}: {status_text}", "success")
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการบันทึกผลตรวจสอบ: {e}", "error")

    return redirect(url_for('inspection.inspection'))


@inspection_bp.route('/history')
@login_required
def history():
    status_filter = request.args.get('status', 'ALL')
    search_query = request.args.get('q', '').strip()

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = "SELECT * FROM inspections WHERE 1=1"
            params = []

            # If regular user, optionally show their own items, or all inspected items
            if session.get('role') != 'ADMIN':
                query += " AND (submitted_by = %s OR status != 'PENDING')"
                params.append(session.get('username'))

            if status_filter != 'ALL':
                query += " AND status = %s"
                params.append(status_filter)

            if search_query:
                query += " AND (item_code LIKE %s OR item_name LIKE %s OR submitted_by LIKE %s)"
                term = f"%{search_query}%"
                params.extend([term, term, term])

            query += " ORDER BY created_at DESC"
            cursor.execute(query, tuple(params))
            history_list = cursor.fetchall()
        conn.close()
        return render_template('history.html', items=history_list, current_status=status_filter, search_query=search_query)
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการโหลดประวัติ: {e}", "error")
        return render_template('history.html', items=[], current_status=status_filter, search_query=search_query)
