# -*- coding: utf-8 -*-
"""
Shared utilities, decorators, validators, and helper functions for LXP Sale Monitor.
"""

import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime
from functools import wraps
from flask import session, flash, redirect, url_for
from dotenv import load_dotenv

from db import get_db_connection
from audit_config import BRANCH_LIST

import secrets
import hmac

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(_env_path)

# Constants
USERNAME_PATTERN = r'^[A-Z]{3}$'  # Exactly 3 uppercase English letters
PASSWORD_EXPIRY_DAYS = 90         # 3 months (90 days)
DEFAULT_INITIAL_PASSWORD = "Test*123"


def generate_csrf_token():
    """Generates a cryptographically secure CSRF token and stores it in session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf_token(token):
    """Validates submitted CSRF token against session token using constant-time comparison."""
    expected = session.get('_csrf_token')
    if not expected or not token:
        return False
    return hmac.compare_digest(str(expected), str(token).strip())


# Cache for branches to avoid querying DB on every single request / template render
_BRANCHES_CACHE = None
_BRANCHES_CACHE_TIMESTAMP = 0
BRANCH_CACHE_TTL = 120  # 2 minutes


def invalidate_branch_cache():
    """Invalidates the branch list cache when branches are added/removed."""
    global _BRANCHES_CACHE, _BRANCHES_CACHE_TIMESTAMP
    _BRANCHES_CACHE = None
    _BRANCHES_CACHE_TIMESTAMP = 0


def get_all_branches():
    """Fetches all active branches with in-memory TTL caching."""
    global _BRANCHES_CACHE, _BRANCHES_CACHE_TIMESTAMP
    now = datetime.now().timestamp()
    if _BRANCHES_CACHE is not None and (now - _BRANCHES_CACHE_TIMESTAMP) < BRANCH_CACHE_TTL:
        return _BRANCHES_CACHE

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM branches WHERE is_active = 1 ORDER BY id ASC")
            rows = cursor.fetchall()
        conn.close()
        if rows is not None:
            _BRANCHES_CACHE = [r['name'] for r in rows]
            _BRANCHES_CACHE_TIMESTAMP = now
            return _BRANCHES_CACHE
    except Exception:
        pass

    _BRANCHES_CACHE = list(BRANCH_LIST)
    _BRANCHES_CACHE_TIMESTAMP = now
    return _BRANCHES_CACHE


def save_base64_photo(photo_item, username='user', prefix='report', max_dim=1280, quality=80):
    """
    Saves and optimizes base64 image data to disk as compressed WebP/JPEG.
    Reduces photo size by ~70-85% for lightning-fast page loading and PDF generation.
    Returns the relative URL path (e.g. /static/uploads/daily_reports/filename.webp).
    """
    if not photo_item or not isinstance(photo_item, str):
        return None

    if photo_item.startswith('/static/'):
        return photo_item

    if not photo_item.startswith('data:image'):
        return None

    import io
    import base64
    from PIL import Image

    try:
        header, encoded = photo_item.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        img = Image.open(io.BytesIO(img_bytes))

        # Convert RGBA to RGB for JPEG/WebP compatibility
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if 'A' in img.getbands() else None)
            img = bg

        # Resize if larger than max_dim
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'daily_reports')
        os.makedirs(upload_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        username_safe = re.sub(r'[^A-Za-z0-9_]', '', username)
        filename = f"{prefix}_{username_safe}_{timestamp}.webp"
        file_path = os.path.join(upload_dir, filename)

        # Save with high-efficiency WebP compression
        img.save(file_path, 'WEBP', quality=quality, method=4)
        return f"/static/uploads/daily_reports/{filename}"

    except Exception as e:
        # Fallback to direct raw save if Pillow fails
        try:
            upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'daily_reports')
            os.makedirs(upload_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            username_safe = re.sub(r'[^A-Za-z0-9_]', '', username)
            filename = f"{prefix}_{username_safe}_{timestamp}.jpg"
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(img_bytes)
            return f"/static/uploads/daily_reports/{filename}"
        except Exception as fe:
            print(f"[Photo Optimization Error]: {fe}")
            return None


def enrich_daily_report_with_linked_audit(conn, report, manpower_data, team_staff, report_photos):
    """
    Auto-merges Section 1 data (Manpower, Brief, Photos, Signatures) from the same-day Morning Audit
    into the Daily Operation Report if missing in the Daily Report.
    """
    need_manpower = not manpower_data or not any(v.get('qty') or v.get('names') for v in manpower_data.values() if isinstance(v, dict))
    need_brief = not report.get('morning_brief')
    need_photos = not report_photos or len(report_photos) == 0
    need_sig_s1 = not team_staff.get('manager_sig') and not team_staff.get('manager_sig_s1')

    if need_manpower or need_brief or need_photos or need_sig_s1:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT audit_data FROM morning_audits 
                    WHERE branch = %s AND audit_date = %s 
                    ORDER BY id DESC LIMIT 1
                """, (report.get('branch'), report.get('report_date')))
                ma_row = cursor.fetchone()
                if ma_row and ma_row.get('audit_data'):
                    ma_payload = json.loads(ma_row['audit_data'])
                    if isinstance(ma_payload, dict):
                        if need_manpower and ma_payload.get('manpower'):
                            manpower_data = ma_payload.get('manpower')
                        if need_brief and ma_payload.get('morning_brief'):
                            report['morning_brief'] = ma_payload.get('morning_brief')
                        if need_photos and ma_payload.get('audit_photos'):
                            report_photos = ma_payload.get('audit_photos')
                        if need_sig_s1 and ma_payload.get('team_staff'):
                            for k, v in ma_payload.get('team_staff', {}).items():
                                if not team_staff.get(k):
                                    team_staff[k] = v
        except Exception as e_ma:
            print(f"Error fetching linked morning audit: {e_ma}")

    return report, manpower_data, team_staff, report_photos


def format_branch_filter(name):
    """Ensures branch name always displays cleanly."""
    if not name:
        return '-'
    return str(name).strip()


def format_date_dmy(val):
    """Formats date object or date string (YYYY-MM-DD) to Day/Month/Year (DD/MM/YYYY)."""
    if not val:
        return '-'
    try:
        if isinstance(val, (datetime, )):
            return val.strftime('%d/%m/%Y')
        if hasattr(val, 'strftime'):
            return val.strftime('%d/%m/%Y')
        val_str = str(val).strip()
        # Match YYYY-MM-DD
        match = re.match(r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})', val_str)
        if match:
            year, month, day = match.groups()
            return f"{int(day):02d}/{int(month):02d}/{year}"
        # Match DD-MM-YYYY or DD/MM/YYYY
        match_dmy = re.match(r'^(\d{1,2})[-/](\d{1,2})[-/](\d{4})', val_str)
        if match_dmy:
            day, month, year = match_dmy.groups()
            return f"{int(day):02d}/{int(month):02d}/{year}"
        return val_str
    except Exception:
        return str(val)


def validate_username(username):
    """Validates that username contains EXACTLY 3 uppercase English letters (A-Z)."""
    if not username:
        return False, "กรุณากรอกชื่อผู้ใช้"
    if not re.match(USERNAME_PATTERN, username):
        return False, "ชื่อผู้ใช้ต้องเป็นตัวอักษรภาษาอังกฤษพิมพ์ใหญ่ 3 ตัวเท่านั้น (เช่น ADM, USR)"
    return True, ""


def validate_password_strength(password):
    """
    Validates that password meets security requirements:
    1. At least 8 characters long
    2. At least one uppercase English letter (A-Z)
    3. At least one lowercase English letter (a-z)
    4. At least one digit (0-9)
    5. At least one special character (!@#$%^&*...)
    6. Must not be the default initial password
    """
    if not password:
        return False, "กรุณากรอกรหัสผ่าน"
    if len(password) < 8:
        return False, "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร"
    if not re.search(r'[A-Z]', password):
        return False, "รหัสผ่านต้องมีตัวอักษรภาษาอังกฤษพิมพ์ใหญ่ (A-Z) อย่างน้อย 1 ตัว"
    if not re.search(r'[a-z]', password):
        return False, "รหัสผ่านต้องมีตัวอักษรภาษาอังกฤษพิมพ์เล็ก (a-z) อย่างน้อย 1 ตัว"
    if not re.search(r'[0-9]', password):
        return False, "รหัสผ่านต้องมีตัวเลข (0-9) อย่างน้อย 1 ตัว"
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "รหัสผ่านต้องมีอักขระพิเศษ (เช่น !@#$%^&*()_+) อย่างน้อย 1 ตัว"
    if password == DEFAULT_INITIAL_PASSWORD:
        return False, f"รหัสผ่านใหม่ต้องไม่ตรงกับรหัสผ่านเริ่มต้น ({DEFAULT_INITIAL_PASSWORD})"
    return True, ""


def generate_random_password(length=8):
    """
    Generates a secure, readable random password with length >= 8.
    Guarantees at least 1 uppercase, 1 lowercase, 1 digit, and 1 special symbol,
    while excluding ambiguous characters (0, O, 1, l, I).
    """
    uppers = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    lowers = 'abcdefghijkmnpqrstuvwxyz'
    digits = '23456789'
    specials = '!@#$%^&*'

    chars = [
        secrets.choice(uppers),
        secrets.choice(lowers),
        secrets.choice(digits),
        secrets.choice(specials)
    ]
    all_allowed = uppers + lowers + digits + specials
    for _ in range(max(0, length - 4)):
        chars.append(secrets.choice(all_allowed))

    rng = secrets.SystemRandom()
    rng.shuffle(chars)
    return ''.join(chars)


def is_password_expired(password_changed_at):
    """Checks whether the password has exceeded 3 months (90 days) from database timestamp."""
    if not password_changed_at:
        return True
    if isinstance(password_changed_at, str):
        try:
            password_changed_at = datetime.strptime(password_changed_at, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return True
    delta = datetime.now() - password_changed_at
    return delta.days >= PASSWORD_EXPIRY_DAYS


SESSION_TIMEOUT_SECONDS = 24 * 3600  # 24 hours


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("กรุณาเข้าสู่ระบบก่อนเข้าใช้งาน", "warning")
            return redirect(url_for('auth.login'))
        
        # Enforce 24-hour session timeout
        login_time = session.get('login_time')
        if login_time and (datetime.now().timestamp() - login_time > SESSION_TIMEOUT_SECONDS):
            session.clear()
            flash("เซสชันการเข้าสู่ระบบหมดอายุ (ครบกำหนด 24 ชั่วโมง) กรุณาเข้าสู่ระบบใหม่อีกครั้ง", "warning")
            return redirect(url_for('auth.login'))

        if session.get('require_password_change'):
            if not session.get('is_first_login'):
                flash("รหัสผ่านของคุณมีอายุเกิน 3 เดือน กรุณาเปลี่ยนรหัสผ่านใหม่ก่อนเข้าใช้งาน", "warning")
            return redirect(url_for('auth.change_password'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("กรุณาเข้าสู่ระบบก่อนเข้าใช้งาน", "warning")
            return redirect(url_for('auth.login'))
        
        # Enforce 24-hour session timeout
        login_time = session.get('login_time')
        if login_time and (datetime.now().timestamp() - login_time > SESSION_TIMEOUT_SECONDS):
            session.clear()
            flash("เซสชันการเข้าสู่ระบบหมดอายุ (ครบกำหนด 24 ชั่วโมง) กรุณาเข้าสู่ระบบใหม่อีกครั้ง", "warning")
            return redirect(url_for('auth.login'))

        if session.get('require_password_change'):
            if not session.get('is_first_login'):
                flash("รหัสผ่านของคุณมีอายุเกิน 3 เดือน กรุณาเปลี่ยนรหัสผ่านใหม่ก่อนเข้าใช้งาน", "warning")
            return redirect(url_for('auth.change_password'))
        if session.get('role') != 'ADMIN':
            flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้ (เฉพาะผู้ดูแลระบบ ADMIN เท่านั้น)", "error")
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def clean_ai_output(text):
    if not text:
        return text
    # Strip any meta analysis/constraints before first header
    patterns = [
        r'(###?\s*1\.?\s*Executive Summary.*)',
        r'(###?\s*Executive Summary.*)',
        r'(\bExecutive Summary:.*)',
        r'(\bExecutive Summary\b.*)'
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            text = m.group(1).strip()
            break
    # Strip trailing meta evaluation checklists
    text = re.sub(r'\n\s*[\*\-]\s*Only use input data\?.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\n\s*[\*\-]\s*Summarize minimally\?.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\n\s*[\*\-]\s*Identify anomalies\?.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\n\s*[\*\-]\s*Structure followed\?.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\n\s*[\*\-]\s*Professional Thai\?.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()


def generate_morning_audit_ai_analysis(ma):
    """
    Generates an Executive Quality & Standard Analysis report for a specific Morning Audit record (FM-MS-007)
    using Google Gemini API (REST gemini-2.5-flash with structured analytical fallback).
    """
    total_items = ma.get('total_items') or 36
    passed_items = ma.get('passed_items') or 0
    failed_items = ma.get('failed_items') or 0
    pass_pct = round((passed_items / total_items) * 100, 1) if total_items > 0 else 100.0
    fail_pct = round(100.0 - pass_pct, 1)
    branch_name = ma.get('branch', 'ไม่ระบุสาขา')
    audit_date = str(ma.get('audit_date', ''))
    submitted_by = ma.get('submitted_by', '-')

    failed_items_details = []
    raw_adata = ma.get('audit_data')
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
    except Exception as e:
        print("Error parsing audit data for AI:", e)

    system_instruction_text = (
        "คุณคือผู้เชี่ยวชาญด้านการตรวจสอบและประกันคุณภาพมาตรฐานสำนักงานขาย (Sales Office Quality & Standard Auditor)\n"
        "หน้าที่ของคุณคือ วิเคราะห์ผลการตรวจ Morning Audit (แบบฟอร์ม FM-MS-007 Rev.00) ของสาขานี้ และสรุปรายงานสำหรับผู้บริหาร (Executive Management Report)\n\n"
        "โครงสร้างรายงานที่คุณต้องสรุป:\n"
        "### 1. Executive Summary (สรุปภาพรวมผู้บริหาร)\n"
        "ระบุสาขา วันที่ตรวจ สัดส่วน % ผ่าน/ไม่ผ่านเกณฑ์ อย่างกระชับ ชัดเจน และตรงประเด็น\n\n"
        "### 2. Overall Status & Quality Assessment (ระดับมาตรฐานและการประเมินคุณภาพ)\n"
        "- ระบุสถานะ เช่น 🟢 ผ่านเกณฑ์สมบูรณ์ (NORMAL - 100%), 🟡 เฝ้าระวัง/มีข้อบกพร่องเล็กน้อย (WATCH - 85-99%), หรือ 🔴 ต้องดำเนินการแก้ไขเร่งด่วน (ACTION REQUIRED - <85%)\n"
        "- สรุปการประเมินจุดเด่นและจุดที่ต้องปรับปรุง\n\n"
        "### 3. Key Issues (ประเด็นข้อบกพร่องที่ตรวจพบ)\n"
        "- สรุปรายการข้อบกพร่อง พร้อมหมวดและหลักฐานที่บันทึก (หากผ่าน 100% ให้ระบุว่าผ่านเกณฑ์มาตรฐานครบถ้วนทุกรายการ)\n\n"
        "### 4. Management Action (ข้อเสนอแนะการบริหารจัดการ)\n"
        "- ข้อเสนอแนะเชิงปฏิบัติการสำหรับผู้จัดการสาขาและทีมงานเพื่อรักษาและยกระดับมาตรฐาน\n\n"
        "### 5. Attention & Follow-up (สิ่งที่ควรติดตามเป็นพิเศษ)\n"
        "- กรอบเวลาการแก้ไขข้อบกพร่อง (เช่น ภายใน 24 ชม.) และแนวทางป้องกันการเกิดซ้ำ\n\n"
        "### 6. Final Conclusion (บทสรุป)\n"
        "สรุปความพร้อมของสาขาในการเปิดให้บริการลูกค้า\n\n"
        "กฎสำคัญ:\n"
        "- ใช้ภาษาไทยที่เป็นทางการ สุภาพ กระชับ ตรงประเด็นแบบผู้บริหาร\n"
        "- จัดรูปแบบเป็น Markdown หัวข้อชัดเจน\n"
        "- ห้ามแสดงขั้นตอนการคิด (thinking/chain-of-thought) และให้เริ่มต้นที่ ### 1. Executive Summary ทันที"
    )

    data_lines = [
        f"รายงานการตรวจ Morning Audit (FM-MS-007) สาขา: {branch_name}",
        f"วันที่ตรวจประเมิน: {audit_date}",
        f"ผู้บันทึกผลการตรวจ: {submitted_by}",
        f"ผลคะแนนการประเมิน: ผ่าน {passed_items}/{total_items} ข้อ ({pass_pct}%), ไม่ผ่าน {failed_items} ข้อ ({fail_pct}%)",
        ""
    ]

    if failed_items_details:
        data_lines.append("=== รายการข้อบกพร่องและหลักฐานที่บันทึก (Defects & Evidence) ===")
        for idx, itm in enumerate(failed_items_details, 1):
            data_lines.append(f"{idx}. หมวด: {itm['category']} (ข้อ {itm['no']}: {itm['title']})")
            data_lines.append(f"   • หลักฐาน/ข้อบกพร่องที่พบ: {itm['defect_note']}")
    else:
        data_lines.append("ผลการตรวจผ่านเกณฑ์มาตรฐาน 100% ครบถ้วนทุกรายการ ไม่พบข้อบกพร่อง")

    if ma.get('material_room_note') and str(ma.get('material_room_note')).strip():
        data_lines.append(f"\n• ข้อสังเกตเพิ่มเติมห้องเก็บอุปกรณ์: '{str(ma['material_room_note']).strip()}'")

    data_lines.append("\nโปรดวิเคราะห์ข้อมูลการตรวจ Morning Audit และสร้าง Executive Management Report ตามโครงสร้างที่กำหนดข้างต้น")

    user_data_prompt = "ข้อมูลสำหรับการวิเคราะห์:\n" + "\n".join(data_lines)

    ai_output_text = ""
    gemini_key = (
        os.getenv("GEMINI_API_KEY1") or 
        os.getenv("GEMINI_API_KEY2") or 
        os.getenv("GEMINI_API_KEY") or 
        os.getenv("GOOGLE_API_KEY") or 
        ""
    ).strip()

    if gemini_key:
        model_name = "gemini-2.5-flash"
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction_text}]},
            "contents": [{"parts": [{"text": user_data_prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        encoded_payload = json.dumps(payload).encode('utf-8')

        # Fast direct REST call to Google Gemini API (gemini-2.5-flash)
        try:
            rest_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
            req = urllib.request.Request(
                rest_url, 
                data=encoded_payload, 
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                candidates = resp_data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts and 'text' in parts[0]:
                        ai_output_text = clean_ai_output(parts[0]['text'])
        except Exception as e:
            print(f"[Gemini AI] Call to {model_name} failed ({e}), falling back to structured analytical engine.")

    # Structured analytical fallback if API is inaccessible
    if not ai_output_text:
        defect_bullets = ""
        if failed_items_details:
            defect_bullets = "\n".join([
                f"- **ข้อที่ {f['no']} (หมวด {f['category']})**: {f['title']} (หลักฐาน/ข้อบกพร่อง: {f['defect_note']})"
                for f in failed_items_details
            ])
            status_badge = "🔴 ACTION REQUIRED" if pass_pct < 85 else "🟡 WATCH"
            status_desc = "พบรายการที่ไม่ผ่านเกณฑ์มาตรฐานความสะอาดและความพร้อมของสำนักงานขาย"
        else:
            defect_bullets = "- ไม่พบข้อบกพร่อง ทุกรายการผ่านเกณฑ์มาตรฐาน 100%"
            status_badge = "🟢 NORMAL"
            status_desc = "การตรวจประเมินเป็นไปตามมาตรฐานที่กำหนดอย่างครบถ้วนสมบูรณ์"

        ai_output_text = f"""### 1. Executive Summary
การตรวจประเมินมาตรฐาน Morning Audit (FM-MS-007) ของสาขา {branch_name} ประจำวันที่ {audit_date} ผ่านเกณฑ์การตรวจสอบ {pass_pct}% ({passed_items} จาก {total_items} ข้อ)

### 2. Overall Status & Quality Assessment
{status_badge} – {status_desc}

### 3. Key Issues (ประเด็นข้อบกพร่องที่ตรวจพบ)
{defect_bullets}

### 4. Management Action (ข้อเสนอแนะการบริหารจัดการ)
1. **Maintain Standards:** ให้ผู้จัดการสาขากำชับการรักษามาตรฐานความสะอาดและความพร้อมของพื้นที่อย่างสม่ำเสมอ
2. **Quality Assurance:** ดำเนินการตรวจสอบตามแบบฟอร์ม FM-MS-007 ต่อเนื่องทุกวันทำการ

### 5. Attention & Follow-up (สิ่งที่ควรติดตามเป็นพิเศษ)
{"ให้ติดตามการแก้ไขรายการข้อบกพร่องที่ระบุข้างต้นให้เสร็จสิ้นภายใน 24 ชม." if failed_items_details else "ไม่มีประเด็นที่ต้องติดตามเป็นพิเศษ"}

### 6. Final Conclusion
สาขา {branch_name} มีความพร้อมในการให้บริการและปฏิบัติงานตามมาตรฐาน {"โดยต้องเร่งแก้ไขรายการที่ไม่ผ่านเกณฑ์" if failed_items_details else "ครบถ้วนสมบูรณ์"}"""

    return ai_output_text


def get_retention_cutoff_date(months=4):
    """
    Calculates calendar cutoff date exactly `months` ago.
    E.g., if today is 2026-08-31, 4 months ago is 2026-04-30 / 2026-05-01.
    """
    import calendar
    from datetime import date
    today = date.today()
    year = today.year
    month = today.month - months
    while month <= 0:
        month += 12
        year -= 1
    max_day = calendar.monthrange(year, month)[1]
    day = min(today.day, max_day)
    return date(year, month, day)


def run_data_retention_cleanup(retention_months=4):
    """
    Automated data retention policy:
    Deletes all operational reports, audits, customer stats, metadata,
    and associated uploaded images/files older than `retention_months` (4 months).
    Ensures safe filesystem cleanup without breaking active dependencies.
    """
    cutoff_date = get_retention_cutoff_date(retention_months)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d')
    base_dir = os.path.dirname(os.path.abspath(__file__))

    deleted_stats = {
        'cutoff_date': cutoff_str,
        'deleted_reports': 0,
        'deleted_audits': 0,
        'deleted_maid_schedules': 0,
        'deleted_files': 0
    }

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Clean Daily Operation Reports older than 4 months
            cursor.execute("SELECT id, report_photos FROM daily_operation_reports WHERE report_date < %s", (cutoff_str,))
            old_reports = cursor.fetchall()
            for r in old_reports:
                if r.get('report_photos'):
                    try:
                        photos = json.loads(r['report_photos'])
                        for p in photos:
                            if isinstance(p, str) and p.startswith('/static/uploads/'):
                                local_path = os.path.normpath(os.path.join(base_dir, p.lstrip('/\\')))
                                if os.path.exists(local_path) and os.path.isfile(local_path):
                                    os.remove(local_path)
                                    deleted_stats['deleted_files'] += 1
                    except Exception:
                        pass

            if old_reports:
                cursor.execute("DELETE FROM daily_operation_reports WHERE report_date < %s", (cutoff_str,))
                deleted_stats['deleted_reports'] = len(old_reports)

            # 2. Clean Morning Audits older than 4 months
            cursor.execute("SELECT id, audit_data FROM morning_audits WHERE audit_date < %s", (cutoff_str,))
            old_audits = cursor.fetchall()
            for a in old_audits:
                if a.get('audit_data'):
                    try:
                        payload = json.loads(a['audit_data'])
                        photos = payload.get('audit_photos', []) if isinstance(payload, dict) else []
                        for p in photos:
                            if isinstance(p, str) and p.startswith('/static/uploads/'):
                                local_path = os.path.normpath(os.path.join(base_dir, p.lstrip('/\\')))
                                if os.path.exists(local_path) and os.path.isfile(local_path):
                                    os.remove(local_path)
                                    deleted_stats['deleted_files'] += 1
                    except Exception:
                        pass

            if old_audits:
                cursor.execute("DELETE FROM morning_audits WHERE audit_date < %s", (cutoff_str,))
                deleted_stats['deleted_audits'] = len(old_audits)

            # 3. Clean Maid Schedules older than 4 months
            try:
                cursor.execute("SELECT id, cleaning_records FROM maid_schedules WHERE schedule_date < %s", (cutoff_str,))
                old_maids = cursor.fetchall()
                if old_maids:
                    cursor.execute("DELETE FROM maid_schedules WHERE schedule_date < %s", (cutoff_str,))
                    deleted_stats['deleted_maid_schedules'] = len(old_maids)
            except Exception:
                pass

        conn.close()
        print(f"[Data Retention Cleanup] Success: cutoff={cutoff_str}, stats={deleted_stats}")
    except Exception as e:
        print(f"[Data Retention Cleanup Error]: {e}")

    return deleted_stats


def analyze_staff_photo_with_gemini(photo_input, reported_count=0, custom_prompt=None):
    """
    Analyzes staff/workplace photos using Google Gemini Vision (gemini-2.5-flash).
    Strictly detects real human employees (ignoring cartoons, mascots, objects, posters),
    counts the number of persons in the photo, compares with reported_count,
    and analyzes uniform/dress code neatness.
    """
    import base64
    import mimetypes

    base_dir = os.path.dirname(os.path.abspath(__file__))
    gemini_key = (
        os.getenv("GEMINI_API_KEY1") or 
        os.getenv("GEMINI_API_KEY2") or 
        os.getenv("GEMINI_API_KEY") or 
        os.getenv("GOOGLE_API_KEY") or 
        ""
    ).strip()

    # Normalize and optimize photo input:
    # ตามข้อกำหนด: ให้ AI วิเคราะห์เฉพาะรูปภาพแรก (ภาพถ่ายพนักงาน/บุคคล) เท่านั้น
    # ภาพที่ 2-7 ไม่ต้องส่งให้ AI เพื่อประหยัดโควตาและลดเวลาประมวลผล
    import io
    from PIL import Image

    image_parts = []
    if isinstance(photo_input, list):
        photos_to_process = [photo_input[0]] if len(photo_input) > 0 and photo_input[0] else []
    else:
        photos_to_process = [photo_input] if photo_input else []

    for p in photos_to_process:
        if not p or not isinstance(p, str):
            continue
        try:
            if p.startswith('data:image'):
                header, encoded = p.split(',', 1)
                try:
                    raw_bytes = base64.b64decode(encoded)
                    im = Image.open(io.BytesIO(raw_bytes))
                    im.thumbnail((800, 800))
                    buf = io.BytesIO()
                    im.save(buf, format='JPEG', quality=80)
                    encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
                except Exception:
                    pass
                image_parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encoded
                    }
                })
            elif (os.path.exists(p) and os.path.isfile(p)) or p.startswith('/static/') or p.startswith('static/') or p.startswith('\\static\\') or p.startswith('static\\'):
                if os.path.exists(p) and os.path.isfile(p):
                    local_path = p
                else:
                    local_path = os.path.normpath(os.path.join(base_dir, p.lstrip('/\\')))
                if os.path.exists(local_path) and os.path.isfile(local_path):
                    try:
                        im = Image.open(local_path)
                        im.thumbnail((800, 800))
                        buf = io.BytesIO()
                        im.save(buf, format='JPEG', quality=80)
                        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        image_parts.append({
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": b64
                            }
                        })
                    except Exception as img_err:
                        print(f"[Image resize error]: {img_err}")
                        mime, _ = mimetypes.guess_type(local_path)
                        mime = mime or "image/jpeg"
                        with open(local_path, 'rb') as f:
                            b64 = base64.b64encode(f.read()).decode('utf-8')
                            image_parts.append({
                                "inline_data": {
                                    "mime_type": mime,
                                    "data": b64
                                }
                            })
        except Exception as err:
            print(f"[AI Vision Load Error]: {err}")

    # Load reference uniform images if provided in static/img/reference_uniforms
    ref_dir = os.path.join(base_dir, 'static', 'img', 'reference_uniforms')
    ref_image_parts = []
    if os.path.exists(ref_dir):
        for fname in sorted(os.listdir(ref_dir)):
            if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                fpath = os.path.join(ref_dir, fname)
                try:
                    im_ref = Image.open(fpath)
                    im_ref.thumbnail((800, 800))
                    buf = io.BytesIO()
                    im_ref.save(buf, format='JPEG', quality=80)
                    b64_ref = base64.b64encode(buf.getvalue()).decode('utf-8')
                    ref_image_parts.append({
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_ref
                        }
                    })
                except Exception as e:
                    print(f"[Reference uniform load error]: {e}")

    # Parse safe integer for reported headcount
    safe_reported = 0
    try:
        safe_reported = int(float(str(reported_count).strip()))
    except (ValueError, TypeError):
        safe_reported = 0

    uniform_ref_instruction = ""
    if ref_image_parts:
        uniform_ref_instruction = (
            "- ภาพตัวอย่างชุดยูนิฟอร์มอ้างอิงมาตรฐาน (Reference Uniforms): มีภาพตัวอย่างชุดมาตรฐานแนบมาด้วย ซึ่งอนุญาต 2 รูปแบบที่ถูกต้องตามเกณฑ์:\n"
            "  1. แบบเสื้อโปโล: เสื้อโปโลสีขาวมาตรฐาน (มีป้ายโลโก้ที่อกเสื้อ) + กางเกงขายาวสีดำ/สีเข้มสุภาพ + รองเท้าสุภาพ\n"
            "  2. แบบชุดสูทสากลทางการ: เสื้อสูทสีดำ/กรมท่า/เทาเข้ม สวมทับเสื้อเชิ้ตสีขาวด้านใน + กางเกง/กระโปรงสุภาพ + รองเท้าสุภาพ\n"
            "  (ทั้ง 2 รูปแบบนี้ถือว่าถูกต้องตามระเบียบบริษัททั้งคู่ ให้ประเมิน dress_code_status = 'PASS')\n"
            "  หากพนักงานสวมเสื้อแฟชั่น, เสื้อยืดคอกลมไม่มีปก, หรือเสื้อเชิ้ตลำลองโดยไม่มีสูท ให้ระบุ dress_code_status = 'FAIL' หรือ 'WARN'\n"
        )

    system_instruction = (
        "คุณคือ AI ผู้เชี่ยวชาญด้านการตรวจสอบและประกันมาตรฐานบุคลากรสำนักงานขาย (Sales Office Staff & Uniform Inspector)\n"
        "หน้าที่ของคุณคือ วิเคราะห์ภาพถ่ายแรกที่แนบมา ซึ่งเป็นภาพถ่ายพนักงาน/บุคคลประจำสำนักงานขาย:\n\n"
        "1. กฎการตรวจสอบความถูกต้องของภาพถ่ายจริง (Anti-Spoofing & Screen Photo Prohibition - กฎเหล็ก ไม่อนุญาตให้ถ่ายจากจอ):\n"
        "- ไม่อนุญาตให้ใช้กล้องถ่ายภาพซ้ำจากหน้าจอคอมพิวเตอร์, หน้าจอมอนิเตอร์, แท็บเล็ต, มือถือ, หรือรูปถ่ายบนกระดาษ/โปสเตอร์ โดยเด็ดขาด (ห้ามอนุโลม)\n"
        "- ตรวจจับสัญญาณการถ่ายจากหน้าจออย่างเข้มงวด: ริ้วคลื่น Moiré pattern, เม็ดพิกเซลหน้าจอดิจิทัล, ขอบจอมอนิเตอร์ (Bezel), รูเว็บแคมบนจอ, แถบเมนู/Taskbar/เมาส์, และแสงสะท้อนบนจอดิจิทัล\n"
        "- หากตรวจพบว่าเป็นภาพที่ถ่ายจากหน้าจอคอมพิวเตอร์หรืออุปกรณ์ดิจิทัล:\n"
        "  * กำหนด is_screen_photo = true, screen_photo_status = 'FAIL'\n"
        "  * กำหนด dress_code_status = 'FAIL'\n"
        "  * กำหนด dress_code_summary = 'ไม่ผ่านเกณฑ์: ตรวจพบภาพถ่ายซ้ำจากหน้าจอคอมพิวเตอร์ (ไม่อนุญาต ต้องเป็นพนักงานตัวจริงในสำนักงาน)'\n"
        "  * เพิ่มใน observations ว่า '⚠️ ตรวจพบการถ่ายภาพจากหน้าจอคอมพิวเตอร์/จอมอนิเตอร์: ไม่อนุญาต ต้องถ่ายพนักงานตัวจริงที่ยืนปฏิบัติงานในสำนักงานเท่านั้น'\n"
        "- หากเป็นภาพถ่ายพนักงานตัวจริงในสถานที่ปฏิบัติงาน: กำหนด is_screen_photo = false, screen_photo_status = 'PASS', screen_photo_summary = 'ภาพถ่ายพนักงานจริงในสำนักงาน'\n\n"
        "2. กฎการตรวจนับบุคคล (Person Detection & Counting):\n"
        "- ตรวจจับและนับพนักงานที่เป็นมนุษย์จริงในภาพถ่าย\n"
        "- ห้ามนับเฉพาะ: ตัวการ์ตูน, ภาพกราฟิก 2D/3D, ป้ายโลโก้, หรือหุ่นจำลองคนขนาดจิ๋วในโมเดลบ้าน\n"
        "- สรุปจำนวนพนักงานที่ตรวจพบใน detected_count (หากตรวจพบพนักงานครบตามที่รายงานระบุ safe_reported หรือมากกว่า ให้ถือว่าผ่านเกณฑ์จำนวนคน)\n\n"
        "3. กฎการตรวจสอบมุมมองภาพเต็มตัว (Full-Body Requirement):\n"
        "- ตรวจสอบว่าภาพถ่ายพนักงานเห็นเต็มตัว (ตั้งแต่ศีรษะ เสื้อ กางเกง/กระโปรง จนถึงรองเท้า) หรือไม่\n"
        "- หากเห็นเต็มตัว: is_full_body = true, full_body_status = 'PASS', full_body_summary = 'ภาพถ่ายเห็นพนักงานเต็มตัวครบถ้วน'\n"
        "- หากถ่ายเฉพาะครึ่งตัวหรือไม่เห็นรองเท้า: is_full_body = false, full_body_status = 'FAIL', full_body_summary = 'ภาพถ่ายไม่เต็มตัว (ไม่เห็นกางเกงหรือรองเท้า)'\n"
        "- หากไม่พบพนักงาน: is_full_body = false, full_body_status = 'NO_STAFF', full_body_summary = 'ไม่พบพนักงานในภาพถ่าย'\n\n"
        "4. กฎการตรวจสอบการแต่งกาย (Uniform & Dress Code):\n"
        + uniform_ref_instruction +
        "- ตรวจสอบการแต่งกาย เช่น เสื้อโปโลยูนิฟอร์มองค์กร, เสื้อเชิ้ต/สูท, กางเกง/กระโปรงสุภาพ, รองเท้า และความเรียบร้อย\n\n"
        "5. โครงสร้าง JSON ที่ต้องส่งกลับ:\n"
        "{\n"
        '  "is_screen_photo": false,\n'
        '  "screen_photo_status": "PASS",\n'
        '  "screen_photo_summary": "ภาพถ่ายพนักงานจริงในสถานที่ปฏิบัติงาน",\n'
        '  "detected_count": 0,\n'
        '  "detected_persons_detail": [\n'
        '     {"position": "...", "is_full_body": true, "description": "..."}\n'
        '  ],\n'
        '  "is_full_body": true,\n'
        '  "full_body_status": "PASS",\n'
        '  "full_body_summary": "ภาพถ่ายเห็นพนักงานเต็มตัวครบถ้วน",\n'
        '  "dress_code_status": "PASS",\n'
        '  "dress_code_summary": "พนักงานสวมยูนิฟอร์มเรียบร้อย",\n'
        '  "observations": ["ข้อสังเกตเพิ่มเติม"]\n'
        "}"
    )

    user_prompt_text = custom_prompt or (
        f"กรุณาวิเคราะห์รูปภาพพนักงานภาพแรกที่แนบมา: "
        "1. ตรวจสอบว่าเป็นการถ่ายจากคนจริงในสำนักงาน หรือเป็นการถ่ายซ้ำจากหน้าจอคอมพิวเตอร์/จอมอนิเตอร์ "
        f"2. สแกนตรวจนับพนักงานในภาพ (รายงานระบุ {safe_reported} คน) "
        "3. ตรวจสอบว่าถ่ายเห็นเต็มตัว (ตั้งแต่ศีรษะจรดเท้า) หรือไม่ "
        "4. ตรวจสอบความถูกต้องของยูนิฟอร์มและการแต่งกายพนักงาน"
    )

    gemini_keys = [
        k for k in [
            (os.getenv("GEMINI_API_KEY1") or "").strip(),
            (os.getenv("GEMINI_API_KEY2") or "").strip(),
            (os.getenv("GEMINI_API_KEY") or "").strip(),
            (os.getenv("GOOGLE_API_KEY") or "").strip(),
        ] if k
    ]

    result_data = None

    if gemini_keys and image_parts:
        candidate_models = ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-3.5-flash-lite"]
        contents_parts = []
        if ref_image_parts:
            contents_parts.append({"text": "ภาพตัวอย่างชุดยูนิฟอร์มพนักงานมาตรฐานของบริษัท (Reference Uniforms):"})
            for r_img in ref_image_parts[:3]:
                contents_parts.append(r_img)
            contents_parts.append({"text": "ภาพถ่ายพนักงานจริงที่ต้องการตรวจสอบประเมินผล (Audited Photo):"})
        else:
            contents_parts.append({"text": user_prompt_text})

        contents_parts.append(image_parts[0]) # วิเคราะห์เฉพาะภาพแรกเท่านั้น

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": contents_parts}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }
        encoded_payload = json.dumps(payload).encode('utf-8')

        for model_name in candidate_models:
            if result_data:
                break
            for g_key in gemini_keys:
                try:
                    rest_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={g_key}"
                    req = urllib.request.Request(
                        rest_url,
                        data=encoded_payload,
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=35) as resp:
                        resp_json = json.loads(resp.read().decode('utf-8'))
                    candidates = resp_json.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        if parts and 'text' in parts[0]:
                            raw_ai_text = parts[0]['text'].strip()
                            if raw_ai_text.startswith('```'):
                                raw_ai_text = re.sub(r'^```(?:json)?\s*', '', raw_ai_text)
                                raw_ai_text = re.sub(r'\s*```$', '', raw_ai_text)
                            parsed = json.loads(raw_ai_text)
                            
                            # Support both single object and list of objects
                            if isinstance(parsed, list) and len(parsed) > 0:
                                best = max(parsed, key=lambda x: int(x.get('detected_count', 0)))
                                detected_num = int(best.get('detected_count', 0))
                                dress_summary = best.get('dress_code_summary', '')
                                dress_status = best.get('dress_code_status', 'PASS')
                                is_full_body = any(bool(x.get('is_full_body', False)) for x in parsed)
                                full_body_status = 'PASS' if is_full_body else 'FAIL'
                                full_body_summary = best.get('full_body_summary', 'ภาพถ่ายเห็นพนักงานเต็มตัวครบถ้วน' if is_full_body else 'ภาพถ่ายไม่เต็มตัว')
                                obs = best.get('observations', [])
                                persons_detail = best.get('detected_persons_detail', [])
                                is_screen = bool(best.get('is_screen_photo', False))
                                screen_status = best.get('screen_photo_status', 'FAIL' if is_screen else 'PASS')
                                screen_summary = best.get('screen_photo_summary', 'ตรวจพบภาพถ่ายจากหน้าจอคอมพิวเตอร์' if is_screen else 'ภาพถ่ายพนักงานจริงในสำนักงาน')
                            else:
                                detected_num = int(parsed.get('detected_count', 0))
                                dress_summary = parsed.get('dress_code_summary', '')
                                dress_status = parsed.get('dress_code_status', 'PASS')
                                is_full_body = bool(parsed.get('is_full_body', False))
                                full_body_status = parsed.get('full_body_status', 'PASS' if is_full_body else 'FAIL')
                                full_body_summary = parsed.get('full_body_summary', '')
                                obs = parsed.get('observations', [])
                                persons_detail = parsed.get('detected_persons_detail', [])
                                is_screen = bool(parsed.get('is_screen_photo', False))
                                screen_status = parsed.get('screen_photo_status', 'FAIL' if is_screen else 'PASS')
                                screen_summary = parsed.get('screen_photo_summary', 'ตรวจพบภาพถ่ายจากหน้าจอคอมพิวเตอร์' if is_screen else 'ภาพถ่ายพนักงานจริงในสำนักงาน')

                            if is_screen:
                                dress_status = "FAIL"
                                dress_summary = "ไม่ผ่านเกณฑ์: ตรวจพบภาพถ่ายซ้ำจากหน้าจอคอมพิวเตอร์ (ไม่อนุญาต ต้องเป็นพนักงานตัวจริงในสำนักงาน)"
                                if not any("หน้าจอคอมพิวเตอร์" in o for o in obs):
                                    obs.insert(0, "⚠️ ตรวจพบการถ่ายภาพจากหน้าจอคอมพิวเตอร์: ไม่อนุญาต ต้องถ่ายพนักงานตัวจริงที่ยืนปฏิบัติงานในสำนักงานเท่านั้น")

                            if detected_num == 0:
                                dress_summary = "ไม่พบพนักงานในภาพถ่าย"
                                dress_status = "NO_STAFF"
                                is_full_body = False
                                full_body_status = "NO_STAFF"
                                full_body_summary = "ไม่พบพนักงานในภาพถ่าย"
                            elif not full_body_summary:
                                full_body_summary = "ภาพถ่ายเห็นพนักงานเต็มตัวตามเกณฑ์" if is_full_body else "ภาพถ่ายไม่เต็มตัว (ต้องถ่ายเต็มตัวตั้งแต่ศีรษะจรดเท้า)"

                            # Matched if detected count meets or matches reported count
                            matched = (detected_num == safe_reported) or (safe_reported > 0 and detected_num >= safe_reported)
                            if not obs:
                                if detected_num == 0:
                                    obs = ["ไม่พบพนักงานในภาพถ่ายที่แนบมา"]
                                else:
                                    obs = [f"ตรวจพบพนักงานในภาพจำนวน {detected_num} คน ({'ตรงกับรายงาน' if matched else 'ไม่ตรงกับรายงาน'})"]
                                    if not is_full_body:
                                        obs.append("ภาพถ่ายไม่เต็มตัว: ควรถ่ายให้เห็นพนักงานตั้งแต่ศีรษะจรดเท้า")

                            full_body_tag = '🟢 ถ่ายเห็นเต็มตัวครบถ้วน' if is_full_body else ('⚪ ไม่พบพนักงาน' if detected_num == 0 else '🔴 ภาพถ่ายไม่เต็มตัว (ต้องถ่ายเต็มตัว)')
                            screen_tag = '🔴 ไม่ผ่าน (ตรวจพบการถ่ายจากหน้าจอคอมพิวเตอร์)' if is_screen else '🟢 ถูกต้อง (ถ่ายพนักงานจริงในสำนักงาน)'

                            full_text = f"""### สรุปผลการวิเคราะห์ภาพถ่ายพนักงานโดย AI
- **ความถูกต้องของภาพถ่าย:** {screen_tag}
- **จำนวนพนักงานที่ตรวจพบ:** {detected_num} คน
- **จำนวนพนักงานที่ระบุในรายงาน:** {safe_reported} คน
- **สถานะความสอดคล้อง:** {'🟢 จำนวนตรงกันถูกต้อง' if matched else '🔴 จำนวนไม่ตรงกับรายงาน'}
- **มุมมองการถ่ายภาพ (เต็มตัว):** {full_body_tag} ({full_body_summary})
- **การแต่งกายและความเรียบร้อย:** {dress_summary}"""

                            result_data = {
                                "is_screen_photo": is_screen,
                                "screen_photo_status": screen_status,
                                "screen_photo_summary": screen_summary,
                                "detected_count": detected_num,
                                "reported_count": safe_reported,
                                "is_count_matched": matched,
                                "is_full_body": is_full_body,
                                "full_body_status": full_body_status,
                                "full_body_summary": full_body_summary,
                                "dress_code_status": dress_status,
                                "dress_code_summary": dress_summary,
                                "observations": obs,
                                "detected_persons_detail": persons_detail,
                                "full_analysis_text": full_text
                            }
                            break # Success! Break out of key loop
                except Exception as e:
                    print(f"[Gemini Vision AI] API call error with key ...{g_key[-6:] if len(g_key)>6 else ''}: {e}")
                    continue

    # Honest fallback (never fake numbers)
    if not result_data:
        detected = 0
        matched = (detected == safe_reported)
        dress_summary = "ไม่พบพนักงานในภาพถ่าย"
        dress_status = "NO_STAFF"
        obs = ["ไม่พบพนักงานในภาพถ่ายที่แนบมา (หรือการเชื่อมต่อ AI ขัดข้อง)"]

        result_data = {
            "is_screen_photo": False,
            "screen_photo_status": "NO_STAFF",
            "screen_photo_summary": "ไม่พบพนักงานในภาพถ่าย",
            "detected_count": 0,
            "reported_count": safe_reported,
            "is_count_matched": matched,
            "is_full_body": False,
            "full_body_status": "NO_STAFF",
            "full_body_summary": "ไม่พบพนักงานในภาพถ่าย",
            "dress_code_status": dress_status,
            "dress_code_summary": dress_summary,
            "observations": obs,
            "detected_persons_detail": [],
            "full_analysis_text": f"""### สรุปผลการวิเคราะห์ภาพถ่ายพนักงานโดย AI
- **จำนวนพนักงานที่ตรวจพบ:** 0 คน
- **จำนวนพนักงานที่ระบุในรายงาน:** {safe_reported} คน
- **สถานะความสอดคล้อง:** {'🟢 จำนวนตรงกันถูกต้อง' if matched else '🔴 จำนวนไม่ตรงกับรายงาน'}
- **มุมมองการถ่ายภาพ (เต็มตัว):** ⚪ ไม่พบพนักงานในภาพถ่าย
- **การแต่งกายและความเรียบร้อย:** {dress_summary}"""
        }

    return result_data



def get_daily_submission_status(target_date_str=None):
    """
    Computes submission compliance status for all branches on a given target date.
    Deadlines:
      - Morning Audit (FM-MS-007): Before 09:15 AM
      - Evening Daily Report (FM-MS-224): Before 05:00 PM (17:00)
    Returns: (summary_dict, branches_status_list, target_date_str)
    """
    from datetime import date, time as dtime

    today = date.today()
    if not target_date_str:
        target_date_str = today.strftime('%Y-%m-%d')

    try:
        target_date_obj = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except Exception:
        target_date_obj = today
        target_date_str = today.strftime('%Y-%m-%d')

    is_today = (target_date_obj == today)
    is_future = (target_date_obj > today)
    now_dt = datetime.now()
    now_time = now_dt.time()

    # กำหนดเวลาส่งรายงานตามมาตรฐาน (Deadlines: เช้าก่อน 09:15 น., เย็นก่อน 17:00 น.)
    morning_deadline = dtime(9, 15, 0)
    evening_deadline = dtime(17, 0, 0)

    branches = get_all_branches()

    conn = get_db_connection()
    morning_map = {}
    evening_map = {}

    with conn.cursor() as cursor:
        # Fetch Morning Audits for date
        cursor.execute("""
            SELECT id, branch, audit_date, submitted_by, is_verified, dress_code_checked, 
                   verified_by, verified_at, ai_staff_analysis, created_at 
            FROM morning_audits 
            WHERE audit_date = %s
            ORDER BY created_at ASC
        """, (target_date_str,))
        m_rows = cursor.fetchall()
        for row in m_rows:
            b_name = row['branch']
            if b_name not in morning_map:
                morning_map[b_name] = row

        # Fetch Daily Operation Reports for date
        cursor.execute("""
            SELECT id, branch, team, report_date, submitted_by, is_verified, dress_code_checked, 
                   verified_by, verified_at, ai_staff_analysis, created_at 
            FROM daily_operation_reports 
            WHERE report_date = %s
            ORDER BY created_at ASC
        """, (target_date_str,))
        e_rows = cursor.fetchall()
        for row in e_rows:
            b_name = row['branch']
            if b_name not in evening_map:
                evening_map[b_name] = row

    conn.close()

    branches_status = []
    summary = {
        'total_branches': len(branches),
        'target_date': target_date_str,
        'morning_on_time': 0,
        'morning_late': 0,
        'morning_missing': 0,
        'morning_pending': 0,
        'evening_on_time': 0,
        'evening_late': 0,
        'evening_missing': 0,
        'evening_pending': 0,
        'both_completed': 0,
        'overall_rate': 0.0
    }

    for b in branches:
        # Helper to match branch names loosely
        m_rec = morning_map.get(b)
        if not m_rec:
            # Try partial keyword match
            for k, v in morning_map.items():
                if k in b or b in k:
                    m_rec = v
                    break

        e_rec = evening_map.get(b)
        if not e_rec:
            for k, v in evening_map.items():
                if k in b or b in k:
                    e_rec = v
                    break

        # Process Morning Audit Status
        m_status = "PENDING"
        m_time_str = "-"
        if m_rec:
            c_at = m_rec.get('created_at')
            if isinstance(c_at, datetime):
                m_time_str = c_at.strftime('%H:%M')
                m_sub_time = c_at.time()
                if m_sub_time <= morning_deadline:
                    m_status = "ON_TIME"
                    summary['morning_on_time'] += 1
                else:
                    m_status = "LATE"
                    summary['morning_late'] += 1
            else:
                m_status = "ON_TIME"
                summary['morning_on_time'] += 1
        else:
            if is_future:
                m_status = "PENDING"
                summary['morning_pending'] += 1
            elif is_today:
                if now_time < morning_deadline:
                    m_status = "PENDING"
                    summary['morning_pending'] += 1
                else:
                    m_status = "MISSING"
                    summary['morning_missing'] += 1
            else:
                m_status = "MISSING"
                summary['morning_missing'] += 1

        # Process Evening Report Status
        e_status = "PENDING"
        e_time_str = "-"
        if e_rec:
            c_at = e_rec.get('created_at')
            if isinstance(c_at, datetime):
                e_time_str = c_at.strftime('%H:%M')
                e_sub_time = c_at.time()
                if e_sub_time <= evening_deadline:
                    e_status = "ON_TIME"
                    summary['evening_on_time'] += 1
                else:
                    e_status = "LATE"
                    summary['evening_late'] += 1
            else:
                e_status = "ON_TIME"
                summary['evening_on_time'] += 1
        else:
            if is_future:
                e_status = "PENDING"
                summary['evening_pending'] += 1
            elif is_today:
                if now_time < evening_deadline:
                    e_status = "PENDING"
                    summary['evening_pending'] += 1
                else:
                    e_status = "MISSING"
                    summary['evening_missing'] += 1
            else:
                e_status = "MISSING"
                summary['evening_missing'] += 1

        # Calculate Overall Branch Status
        if m_rec and e_rec:
            summary['both_completed'] += 1
            if m_status == "ON_TIME" and e_status == "ON_TIME":
                overall = "COMPLETE_ON_TIME"
            else:
                overall = "COMPLETE_WITH_LATE"
        elif m_status == "MISSING" or e_status == "MISSING":
            overall = "MISSING"
        else:
            overall = "PENDING"

        branches_status.append({
            'branch': b,
            'morning': {
                'has_record': m_rec is not None,
                'id': m_rec['id'] if m_rec else None,
                'submitted_by': m_rec['submitted_by'] if m_rec else '-',
                'time_str': m_time_str,
                'status': m_status,
                'is_verified': bool(m_rec.get('is_verified')) if m_rec else False,
                'dress_code_checked': bool(m_rec.get('dress_code_checked')) if m_rec else False,
                'verified_by': m_rec.get('verified_by') if m_rec else None,
                'verified_at': m_rec.get('verified_at').strftime('%d/%m/%Y %H:%M') if (m_rec and m_rec.get('verified_at')) else None
            },
            'evening': {
                'has_record': e_rec is not None,
                'id': e_rec['id'] if e_rec else None,
                'submitted_by': e_rec['submitted_by'] if e_rec else '-',
                'time_str': e_time_str,
                'status': e_status,
                'is_verified': bool(e_rec.get('is_verified')) if e_rec else False,
                'dress_code_checked': bool(e_rec.get('dress_code_checked')) if e_rec else False,
                'verified_by': e_rec.get('verified_by') if e_rec else None,
                'verified_at': e_rec.get('verified_at').strftime('%d/%m/%Y %H:%M') if (e_rec and e_rec.get('verified_at')) else None
            },
            'overall': overall
        })

    # Overall compliance percentage
    total_slots = len(branches) * 2
    submitted_slots = (summary['morning_on_time'] + summary['morning_late']) + (summary['evening_on_time'] + summary['evening_late'])
    summary['overall_rate'] = round((submitted_slots / total_slots * 100), 1) if total_slots > 0 else 0.0

    return summary, branches_status, target_date_str


