# -*- coding: utf-8 -*-
"""
Dashboard Blueprint for LXP Sale Monitor.
Handles root redirect (/) and /dashboard overview view.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session

from db import get_db_connection
from utils import login_required, get_all_branches, get_daily_submission_status

dashboard_bp = Blueprint('dashboard', __name__)



@dashboard_bp.route('/')
def index():
    if 'user_id' in session:
        if session.get('require_password_change'):
            return redirect(url_for('auth.change_password'))
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard view showing overview stats, morning audit summary, and recent items."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Inspection Stats
            cursor.execute("SELECT COUNT(*) as total FROM inspections")
            total_items = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as pending FROM inspections WHERE status = 'PENDING'")
            pending_items = cursor.fetchone()['pending']
            
            cursor.execute("SELECT COUNT(*) as approved FROM inspections WHERE status = 'APPROVED'")
            approved_items = cursor.fetchone()['approved']

            cursor.execute("SELECT COUNT(*) as rejected FROM inspections WHERE status = 'REJECTED'")
            rejected_items = cursor.fetchone()['rejected']

            # Morning Audit Stats
            cursor.execute("SELECT COUNT(*) as total_audits, SUM(passed_items) as sum_passed, SUM(total_items) as sum_total FROM morning_audits")
            audit_stat_row = cursor.fetchone()
            total_audits = audit_stat_row['total_audits'] or 0
            sum_passed = audit_stat_row['sum_passed'] or 0
            sum_total = audit_stat_row['sum_total'] or 0
            avg_pass_rate = round((sum_passed / sum_total * 100), 1) if sum_total > 0 else 0.0

            # Daily Operation Reports Count
            cursor.execute("SELECT COUNT(*) as total_reports FROM daily_operation_reports")
            total_daily_reports = cursor.fetchone()['total_reports'] or 0

            # Maid Schedules Count
            cursor.execute("SELECT COUNT(*) as total_maid FROM maid_schedules")
            total_maid_schedules = cursor.fetchone()['total_maid'] or 0

            # Recent records
            user_name = session.get('username', '')
            if session.get('role') == 'ADMIN':
                cursor.execute("SELECT * FROM inspections ORDER BY created_at DESC LIMIT 5")
                recent_items = cursor.fetchall()
                cursor.execute("SELECT id, branch, audit_date, passed_items, failed_items, submitted_by FROM morning_audits ORDER BY audit_date DESC, created_at DESC LIMIT 4")
                recent_audits = cursor.fetchall()
                cursor.execute("SELECT id, branch, team, report_date, submitted_by FROM daily_operation_reports ORDER BY report_date DESC, created_at DESC LIMIT 4")
                recent_dailies = cursor.fetchall()
                cursor.execute("SELECT id, branch, month_year, submitted_by, updated_at FROM maid_schedules ORDER BY updated_at DESC LIMIT 4")
                recent_maid_schedules = cursor.fetchall()
            else:
                cursor.execute("SELECT * FROM inspections WHERE submitted_by = %s ORDER BY created_at DESC LIMIT 5", (user_name,))
                recent_items = cursor.fetchall()
                cursor.execute("SELECT id, branch, audit_date, passed_items, failed_items, submitted_by FROM morning_audits WHERE submitted_by = %s ORDER BY audit_date DESC, created_at DESC LIMIT 4", (user_name,))
                recent_audits = cursor.fetchall()
                cursor.execute("SELECT id, branch, team, report_date, submitted_by FROM daily_operation_reports WHERE submitted_by = %s ORDER BY report_date DESC, created_at DESC LIMIT 4", (user_name,))
                recent_dailies = cursor.fetchall()
                cursor.execute("SELECT id, branch, month_year, submitted_by, updated_at FROM maid_schedules WHERE submitted_by = %s OR branch LIKE %s ORDER BY updated_at DESC LIMIT 4", (user_name, f"%{user_name}%"))
                recent_maid_schedules = cursor.fetchall()
                if not recent_maid_schedules:
                    cursor.execute("SELECT id, branch, month_year, submitted_by, updated_at FROM maid_schedules ORDER BY updated_at DESC LIMIT 4")
                    recent_maid_schedules = cursor.fetchall()

        conn.close()

        stats = {
            'total': total_items,
            'pending': pending_items,
            'approved': approved_items,
            'rejected': rejected_items,
            'total_audits': total_audits,
            'total_daily_reports': total_daily_reports,
            'total_maid_schedules': total_maid_schedules,
            'avg_pass_rate': avg_pass_rate
        }

        # Daily submission status for today
        sub_summary, sub_branches, _ = get_daily_submission_status()

        return render_template(
            'dashboard.html',
            stats=stats,
            sub_summary=sub_summary,
            sub_branches=sub_branches,
            recent_items=recent_items,
            recent_audits=recent_audits,
            recent_dailies=recent_dailies,
            recent_maid_schedules=recent_maid_schedules,
            branches=get_all_branches()
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการดึงข้อมูล Dashboard: {e}", "error")
        return render_template(
            'dashboard.html',
            stats={},
            sub_summary={'total_branches': 0, 'morning_on_time': 0, 'morning_late': 0, 'morning_missing': 0, 'evening_on_time': 0, 'evening_late': 0, 'evening_missing': 0, 'overall_rate': 0.0},
            sub_branches=[],
            recent_items=[],
            recent_audits=[],
            recent_dailies=[],
            recent_maid_schedules=[],
            branches=get_all_branches()
        )
