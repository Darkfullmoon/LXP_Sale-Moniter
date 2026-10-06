# -*- coding: utf-8 -*-
"""
PDF Generator for LXP Sale Monitor using ReportLab.
Produces official, high-quality A4 PDF documents with THSarabunNew Thai fonts.
"""

import os
import io
import re
import json
import base64
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, PolyLine, Line
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register THSarabunNew TrueType fonts
FONT_DIR = os.path.join(os.path.dirname(__file__), 'font')
pdfmetrics.registerFont(TTFont('THSarabunNew', os.path.join(FONT_DIR, 'THSarabunNew.ttf')))
pdfmetrics.registerFont(TTFont('THSarabunNew-Bold', os.path.join(FONT_DIR, 'THSarabunNew Bold.ttf')))
pdfmetrics.registerFont(TTFont('THSarabunNew-Italic', os.path.join(FONT_DIR, 'THSarabunNew Italic.ttf')))
pdfmetrics.registerFont(TTFont('THSarabunNew-BoldItalic', os.path.join(FONT_DIR, 'THSarabunNew BoldItalic.ttf')))


def create_checkbox(is_checked, is_pass=True):
    """Draws a sharp checkbox icon matching the web UI design."""
    d = Drawing(16, 16)
    if is_checked:
        if is_pass:
            # Green rounded box with crisp white checkmark
            d.add(Rect(1.5, 1.5, 13, 13, fillColor=colors.HexColor('#10B981'), strokeColor=colors.HexColor('#059669'), strokeWidth=0.8, rx=2, ry=2))
            d.add(PolyLine([(4.0, 7.5), (6.5, 4.5), (11.5, 10.8)], strokeColor=colors.white, strokeWidth=1.8))
        else:
            # Red rounded box with crisp white X
            d.add(Rect(1.5, 1.5, 13, 13, fillColor=colors.HexColor('#EF4444'), strokeColor=colors.HexColor('#DC2626'), strokeWidth=0.8, rx=2, ry=2))
            d.add(Line(4.5, 4.5, 11.5, 11.5, strokeColor=colors.white, strokeWidth=1.8))
            d.add(Line(4.5, 11.5, 11.5, 4.5, strokeColor=colors.white, strokeWidth=1.8))
    else:
        # Crisp empty box
        d.add(Rect(1.5, 1.5, 13, 13, fillColor=colors.white, strokeColor=colors.HexColor('#0F172A'), strokeWidth=0.9, rx=1.5, ry=1.5))
    return d


def decode_base64_image(data_uri, width=100, height=35):
    """
    Decodes a base64 Data URI (e.g. data:image/png;base64,...) and returns a ReportLab Image Flowable.
    Returns None if decoding fails or input is empty.
    """
    if not data_uri or not isinstance(data_uri, str) or not data_uri.strip():
        return None
    try:
        data_clean = data_uri.strip()
        if data_clean.startswith('data:'):
            if ',' in data_clean:
                header, encoded = data_clean.split(',', 1)
            else:
                encoded = data_clean
        else:
            encoded = data_clean
            
        img_bytes = base64.b64decode(encoded)
        img_buffer = io.BytesIO(img_bytes)
        return RLImage(img_buffer, width=width, height=height)
    except Exception:
        return None


def format_date_dmy(val):
    """Formats date object or date string (YYYY-MM-DD) to Day/Month/Year (DD/MM/YYYY)."""
    if not val:
        return '-'
    try:
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


def format_branch_name(name):
    """Formats branch name cleanly."""
    if not name:
        return '-'
    return str(name).strip()


# ================= 1. MORNING AUDIT PDF (FM-MS-007) =================
def generate_morning_audit_pdf(audit, audit_data, daily_plan=None, audit_photos=None):
    """
    Generates a full A4 PDF document for Morning Audit (FM-MS-007) using ReportLab.
    Returns bytes buffer in memory.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=24,
        rightMargin=24,
        topMargin=20,
        bottomMargin=20
    )

    story = []

    # Typography styles
    style_title = ParagraphStyle(
        'DocTitle',
        fontName='THSarabunNew-Bold',
        fontSize=20,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    style_header_line = ParagraphStyle(
        'HeaderLine',
        fontName='THSarabunNew',
        fontSize=14,
        leading=16.5,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    style_th = ParagraphStyle(
        'TableHead',
        fontName='THSarabunNew-Bold',
        fontSize=12.5,
        leading=14.5,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    style_cat_title = ParagraphStyle(
        'CatTitle',
        fontName='THSarabunNew-Bold',
        fontSize=13,
        leading=15,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#0F172A')
    )

    style_no = ParagraphStyle(
        'ItemNo',
        fontName='THSarabunNew-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    style_item_title = ParagraphStyle(
        'ItemTitle',
        fontName='THSarabunNew',
        fontSize=12,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_evidence_pass = ParagraphStyle(
        'EvidencePass',
        fontName='THSarabunNew',
        fontSize=11.5,
        leading=13.5,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#64748B')
    )

    style_evidence_fail = ParagraphStyle(
        'EvidenceFail',
        fontName='THSarabunNew',
        fontSize=11.5,
        leading=13.5,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#DC2626')
    )

    style_note_title = ParagraphStyle(
        'NoteTitle',
        fontName='THSarabunNew-Bold',
        fontSize=12.5,
        leading=14.5,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_note_text = ParagraphStyle(
        'NoteText',
        fontName='THSarabunNew',
        fontSize=12,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_doc_code = ParagraphStyle(
        'DocCode',
        fontName='THSarabunNew-Bold',
        fontSize=11,
        leading=13,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#475569')
    )

    # 1. Header (Centered Title + Centered Branch & Date)
    clean_branch = format_branch_name(audit.get('branch', ''))
    raw_date = audit.get('audit_date', '')
    clean_date = format_date_dmy(raw_date)

    header_para_1 = Paragraph("<b>รายงาน Morning Audit สำนักงานขาย (ประจำวัน)</b>", style_title)
    header_para_2 = Paragraph(f"<b>สาขา</b> &nbsp; <u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {clean_branch} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>วันที่ตรวจ</b> &nbsp; <u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {clean_date} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>", style_header_line)

    story.append(header_para_1)
    story.append(Spacer(1, 8))
    story.append(header_para_2)
    story.append(Spacer(1, 10))

    # 2. Main Audit Table
    col_widths = [24, 218, 36, 42, 227]

    table_data = [
        [
            Paragraph("<b>No</b>", style_th),
            Paragraph("<b>รายการที่ต้องพร้อมสำหรับการต้อนรับลูกค้าและเปิดสำนักงานขาย</b>", style_th),
            Paragraph("<b>ผลการตรวจ</b>", style_th),
            "",
            Paragraph("<b>บันทึกข้อสังเกต / สิ่งที่ไม่เป็นไปตามมาตรฐาน / evidence / หลักฐาน</b>", style_th)
        ],
        [
            "",
            "",
            Paragraph("<b>ผ่าน</b>", style_th),
            Paragraph("<b>ไม่ผ่าน</b>", style_th),
            ""
        ]
    ]

    t_styles = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (3, 0)),
        ('SPAN', (4, 0), (4, 1)),
        ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor('#F8FAFC')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]

    current_row_idx = 2
    for category in audit_data:
        cat_title = category.get('category_title', '')
        table_data.append([
            "",
            Paragraph(f"<b>{cat_title}</b>", style_cat_title),
            "", "", ""
        ])
        t_styles.append(('SPAN', (1, current_row_idx), (4, current_row_idx)))
        t_styles.append(('BACKGROUND', (0, current_row_idx), (4, current_row_idx), colors.HexColor('#F1F5F9')))
        current_row_idx += 1

        for item in category.get('audit_items', []):
            item_no = item.get('no', '')
            item_title = item.get('title', '')
            status = item.get('status', 'PASS')

            pass_cb = create_checkbox(is_checked=(status == 'PASS'), is_pass=True)
            fail_cb = create_checkbox(is_checked=(status == 'FAIL'), is_pass=False)

            if status == 'PASS':
                evidence_flow = Paragraph("(ผ่านเกณฑ์มาตรฐาน)", style_evidence_pass)
            else:
                ev_lines = []
                evidence_dict = item.get('evidence', {}) or {}
                for field in item.get('evidence_fields', []):
                    f_name = field.get('name')
                    f_label = field.get('label')
                    f_val = evidence_dict.get(f_name, '')
                    if f_val:
                        ev_lines.append(f"<b>{f_label}:</b> {f_val}")
                if not ev_lines:
                    ev_text = "ไม่ผ่านเกณฑ์มาตรฐาน"
                else:
                    ev_text = " | ".join(ev_lines)
                evidence_flow = Paragraph(ev_text, style_evidence_fail)

            table_data.append([
                Paragraph(f"<b>{item_no}</b>", style_no),
                Paragraph(item_title, style_item_title),
                pass_cb,
                fail_cb,
                evidence_flow
            ])
            t_styles.append(('ALIGN', (0, current_row_idx), (0, current_row_idx), 'CENTER'))
            t_styles.append(('ALIGN', (2, current_row_idx), (3, current_row_idx), 'CENTER'))
            current_row_idx += 1

    audit_table = Table(table_data, colWidths=col_widths, repeatRows=2)
    audit_table.setStyle(TableStyle(t_styles))
    story.append(audit_table)

    story.append(Spacer(1, 8))

    # 4. Bottom Note Section
    mat_note = audit.get('material_room_note', '') or '-'
    note_content = [
        [Paragraph("<b>หมายเหตุ : กรณีห้องวัสดุไม่ครบ/ไม่เรียบร้อย (หมวดที่ 4.) โปรดอธิบาย</b>", style_note_title)],
        [Paragraph(f"<u>&nbsp; {mat_note} &nbsp;</u>", style_note_text)],
        [Paragraph("FM-MS-007 Rev.00", style_doc_code)]
    ]
    note_table = Table(note_content, colWidths=[547])
    note_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    story.append(KeepTogether(note_table))

    # Optional Attached Photos Pages
    if audit_photos and len(audit_photos) > 0:
        story.append(PageBreak())
        style_photo_head = ParagraphStyle('PhotoHead', fontName='THSarabunNew-Bold', fontSize=14, leading=16, alignment=TA_LEFT, textColor=colors.HexColor('#0F172A'))
        story.append(Paragraph("<b>รูปถ่ายรายงาน Morning Audit (แนบท้าย)</b>", style_photo_head))
        story.append(Spacer(1, 8))

        photo_cells = []
        for p_idx, p_path in enumerate(audit_photos):
            img_flow = None
            if p_path.startswith('/static/'):
                rel_path = p_path.lstrip('/')
                full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), rel_path))
                if os.path.exists(full_path):
                    try:
                        img_flow = RLImage(full_path, width=250, height=180)
                    except Exception:
                        pass
            elif p_path.startswith('data:image'):
                img_flow = decode_base64_image(p_path, width=250, height=180)

            if img_flow:
                caption = Paragraph(f"รูปที่ {p_idx + 1}", ParagraphStyle('PNum', fontName='THSarabunNew-Bold', fontSize=10, leading=12, alignment=TA_CENTER))
                photo_cells.append([img_flow, caption])

        # Arrange photos in 2-column grid
        grid_rows = []
        for i in range(0, len(photo_cells), 2):
            row_data = []
            c1 = photo_cells[i]
            c1_table = Table([[c1[0]], [c1[1]]], colWidths=[260])
            c1_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
            row_data.append(c1_table)

            if i + 1 < len(photo_cells):
                c2 = photo_cells[i + 1]
                c2_table = Table([[c2[0]], [c2[1]]], colWidths=[260])
                c2_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
                row_data.append(c2_table)
            else:
                row_data.append("")
            grid_rows.append(row_data)

        if grid_rows:
            p_grid_table = Table(grid_rows, colWidths=[270, 270])
            p_grid_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 2), ('RIGHTPADDING', (0, 0), (-1, -1), 2)]))
            story.append(p_grid_table)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ================= 2. DAILY REPORT PDF (FM-MS-224) =================
def generate_daily_report_pdf(report, manpower, stats, team_staff, report_photos=None):
    """
    Generates a full A4 PDF document for Daily Operation Report (FM-MS-224) using ReportLab.
    Returns bytes buffer in memory.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=24,
        rightMargin=24,
        topMargin=18,
        bottomMargin=18
    )

    story = []

    # Typography Styles
    style_title = ParagraphStyle(
        'DailyTitle',
        fontName='THSarabunNew-Bold',
        fontSize=20,
        leading=22,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_meta_label = ParagraphStyle(
        'MetaLabel',
        fontName='THSarabunNew-Bold',
        fontSize=13.5,
        leading=15.5,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_meta_val = ParagraphStyle(
        'MetaVal',
        fontName='THSarabunNew-Bold',
        fontSize=13.5,
        leading=15.5,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#1E3A8A')
    )

    style_sec_title = ParagraphStyle(
        'SecTitle',
        fontName='THSarabunNew-Bold',
        fontSize=13.5,
        leading=15.5,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_th_center = ParagraphStyle(
        'THCenter',
        fontName='THSarabunNew-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    style_th_left = ParagraphStyle(
        'THLeft',
        fontName='THSarabunNew-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_cell_label = ParagraphStyle(
        'CellLabel',
        fontName='THSarabunNew',
        fontSize=12,
        leading=13.5,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_cell_qty = ParagraphStyle(
        'CellQty',
        fontName='THSarabunNew-Bold',
        fontSize=12.5,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1E3A8A')
    )

    style_cell_names = ParagraphStyle(
        'CellNames',
        fontName='THSarabunNew',
        fontSize=11.5,
        leading=13,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_textarea_text = ParagraphStyle(
        'TextAreaText',
        fontName='THSarabunNew',
        fontSize=11.5,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_stat_val = ParagraphStyle(
        'StatVal',
        fontName='THSarabunNew',
        fontSize=12,
        leading=13.5,
        alignment=TA_RIGHT,
        textColor=colors.black
    )

    style_sign_head = ParagraphStyle(
        'SignHead',
        fontName='THSarabunNew-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_sign_head_right = ParagraphStyle(
        'SignHeadRight',
        fontName='THSarabunNew-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    style_sign_staff = ParagraphStyle(
        'SignStaff',
        fontName='THSarabunNew',
        fontSize=11.5,
        leading=13,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_sign_staff_num = ParagraphStyle(
        'SignStaffNum',
        fontName='THSarabunNew-Bold',
        fontSize=11.5,
        leading=13,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    style_sign_staff_dots = ParagraphStyle(
        'SignStaffDots',
        fontName='THSarabunNew',
        fontSize=10,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#94A3B8')
    )

    style_sign_staff_center = ParagraphStyle(
        'SignStaffCenter',
        fontName='THSarabunNew-Bold',
        fontSize=11.5,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1E3A8A')
    )

    style_sign_staff_pos = ParagraphStyle(
        'SignStaffPos',
        fontName='THSarabunNew-Italic',
        fontSize=10.5,
        leading=12,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#334155')
    )

    style_sign_manager = ParagraphStyle(
        'SignManager',
        fontName='THSarabunNew-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    style_doc_code = ParagraphStyle(
        'DocCodeDaily',
        fontName='THSarabunNew-Bold',
        fontSize=11,
        leading=13,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#475569')
    )

    # 1. HEADER (Title, Branch, Date)
    branch_val = report.get('branch', '-')
    date_val = str(report.get('report_date', '-'))

    header_table_data = [
        [
            Paragraph("<b>รายงานการปฏิบัติงานสำนักงานขาย</b>", style_title),
            Paragraph(f"<b>สาขา</b> &nbsp;&nbsp; <u>&nbsp; {branch_val} &nbsp;</u>", style_meta_val)
        ],
        [
            "",
            Paragraph(f"<b>วันที่</b> &nbsp;&nbsp; <u>&nbsp; {date_val} &nbsp;</u>", style_meta_val)
        ]
    ]

    header_table = Table(header_table_data, colWidths=[240, 307])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))

    # Column Widths for Main Form Table (Total = 547 pt)
    col_w = [125, 38, 98, 286]

    # Build Section 1 & Section 2 Table
    table_rows = []
    t_styles = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]

    # Row 0: Section 1 Header
    table_rows.append([
        Paragraph("<b>แผนงานประจำวัน</b>", style_sec_title),
        "", "", ""
    ])
    t_styles.append(('SPAN', (0, 0), (3, 0)))
    t_styles.append(('BACKGROUND', (0, 0), (3, 0), colors.HexColor('#FFFFFF')))

    # Row 1: Column Sub-headers
    table_rows.append([
        Paragraph("<b>อัตรากำลังพล</b>", style_th_center),
        Paragraph("<b>จำนวน</b>", style_th_center),
        Paragraph("<b>ชื่อย่อพนักงาน</b>", style_th_center),
        Paragraph("<b>Morning Brief &nbsp;(รายละเอียด)</b>", style_th_center)
    ])
    t_styles.append(('BACKGROUND', (0, 1), (3, 1), colors.HexColor('#F8FAFC')))

    # Manpower Data Rows (Rows 2 to 8 -> 7 rows)
    mp = manpower or {}
    mp_total = mp.get('total', {})
    mp_offsite = mp.get('offsite', {})
    mp_booth = mp.get('booth', {})
    mp_personal = mp.get('personal_leave', {})
    mp_sick = mp.get('sick_leave', {})
    mp_vacation = mp.get('vacation_leave', {})
    mp_dayoff = mp.get('dayoff', {})

    mb_text = report.get('morning_brief', '') or '-'
    mb_formatted = "<br/>".join([line.strip() for line in mb_text.splitlines() if line.strip()]) or '-'
    mb_para = Paragraph(mb_formatted, style_textarea_text)

    manpower_rows_def = [
        ("จำนวนพนักงานทั้งหมด", mp_total.get('qty', '0'), mp_total.get('names', '-'), True),
        ("ทำงานนอกสถานที่", mp_offsite.get('qty', '0'), mp_offsite.get('names', '-'), False),
        ("ออกบูท", mp_booth.get('qty', '0'), mp_booth.get('names', '-'), False),
        ("ลากิจ", mp_personal.get('qty', '0'), mp_personal.get('names', '-'), False),
        ("ลาป่วย", mp_sick.get('qty', '0'), mp_sick.get('names', '-'), False),
        ("ลาพักร้อน", mp_vacation.get('qty', '0'), mp_vacation.get('names', '-'), False),
        ("สลับหยุด", mp_dayoff.get('qty', '0'), mp_dayoff.get('names', '-'), False),
    ]

    for idx, (label, qty, names, is_first) in enumerate(manpower_rows_def):
        r_idx = 2 + idx
        right_cell = mb_para if is_first else ""
        qty_style = style_cell_qty if is_first else style_th_center
        table_rows.append([
            Paragraph(label, style_cell_label),
            Paragraph(str(qty if qty else '0'), qty_style),
            Paragraph(names if names else '-', style_cell_names),
            right_cell
        ])

    # Span Morning brief across rows 2 to 8
    t_styles.append(('SPAN', (3, 2), (3, 8)))
    t_styles.append(('VALIGN', (3, 2), (3, 8), 'TOP'))

    # Row 9: Section 1 Signature Headers
    table_rows.append([
        Paragraph("<b>พนักงานเซ็นรับทราบ</b>", style_sign_head),
        "", "",
        Paragraph("<b>ผู้จัดการสำนักงานขาย</b>", style_sign_head_right)
    ])
    t_styles.append(('SPAN', (0, 9), (2, 9)))
    t_styles.append(('BACKGROUND', (0, 9), (3, 9), colors.HexColor('#F8FAFC')))

    # Row 10: Section 1 Signatures Body
    ts = team_staff or {}
    mgr_s1_name = ts.get('manager_name_s1') or ts.get('manager_s1') or ts.get('manager') or 'ผู้จัดการสำนักงานขาย'
    
    staff_s1_config = [
        ("1)", ts.get('manager_sig'), ts.get('manager'), "ผู้จัดการสำนักงานขาย"),
        ("2)", ts.get('senior_sale_sig'), ts.get('senior_sale'), "เจ้าหน้าที่ขายอาวุโส"),
        ("3)", ts.get('coordinator_sig'), ts.get('coordinator'), "เจ้าหน้าที่ประสานงานขายและการตลาด"),
        ("4)", ts.get('architect_sig'), ts.get('architect'), "สถาปนิกปรับแบบ"),
    ]
    
    staff_s1_sub_data = []
    for num, sig_base64, name, pos in staff_s1_config:
        clean_name = name.strip() if name and name.strip() else '..............................'
        sig_img = decode_base64_image(sig_base64, width=54, height=16)
        sig_cell = sig_img if sig_img else Paragraph("...................", style_sign_staff_dots)
        name_cell = Paragraph(f"<u>&nbsp; {clean_name} &nbsp;</u>", style_sign_staff_center)
        pos_cell = Paragraph(f"<i>{pos}</i>", style_sign_staff_pos)
        staff_s1_sub_data.append([
            Paragraph(f"<b>{num}</b>", style_sign_staff_num),
            sig_cell,
            name_cell,
            pos_cell
        ])
    
    staff_s1_subtable = Table(staff_s1_sub_data, colWidths=[14, 52, 84, 105])
    staff_s1_subtable.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
    ]))

    mgr_s1_sig_data = ts.get('manager_sig_s1') or ts.get('manager_s1_sig') or ts.get('manager_sig')
    mgr_s1_sig_img = decode_base64_image(mgr_s1_sig_data, width=75, height=25)
    if mgr_s1_sig_img:
        mgr_s1_cell_elements = [
            mgr_s1_sig_img,
            Spacer(1, 2),
            Paragraph(f"(&nbsp; <u>&nbsp; {mgr_s1_name} &nbsp;</u> &nbsp;)", style_sign_manager)
        ]
    else:
        mgr_s1_cell_elements = [
            Paragraph("..............................................................", style_sign_manager),
            Paragraph(f"(&nbsp; <u>&nbsp; {mgr_s1_name} &nbsp;</u> &nbsp;)", style_sign_manager)
        ]

    table_rows.append([
        staff_s1_subtable, "", "",
        mgr_s1_cell_elements
    ])
    t_styles.append(('SPAN', (0, 10), (2, 10)))
    t_styles.append(('VALIGN', (0, 10), (3, 10), 'MIDDLE'))
    t_styles.append(('ALIGN', (3, 10), (3, 10), 'CENTER'))

    # ================= SECTION 2: สรุปงานประจำวัน =================
    # Row 11: Section 2 Header
    table_rows.append([
        Paragraph("<b>สรุปงานประจำวัน</b>", style_sec_title),
        "", "", ""
    ])
    t_styles.append(('SPAN', (0, 11), (3, 11)))
    t_styles.append(('BACKGROUND', (0, 11), (3, 11), colors.HexColor('#FFFFFF')))

    # Row 12: Column Sub-headers
    table_rows.append([
        Paragraph("<b>สรุป &nbsp;(รายละเอียด)</b>", style_th_left),
        "", "",
        Paragraph("<b>สรุป &nbsp;(รายละเอียด)</b>", style_th_center)
    ])
    t_styles.append(('SPAN', (0, 12), (2, 12)))
    t_styles.append(('BACKGROUND', (0, 12), (3, 12), colors.HexColor('#F8FAFC')))

    # Row 13: Customer Statistics & Daily Summary Text
    st = stats or {}
    c_center = st.get('call_center', '0')
    c_walk = st.get('walk_in', '0')
    c_app = st.get('appointment', '0')
    c_book = st.get('booking', '0')
    c_mgr = st.get('call_manager', '0')
    c_senior = st.get('call_senior', '0')
    add_tasks = report.get('additional_tasks', '') or '-'

    stats_sub_data = [
        [Paragraph("จำนวนลูกค้าที่ได้จาก Call center", style_cell_label), Paragraph(f"<b>{c_center}</b> &nbsp; ราย", style_stat_val)],
        [Paragraph("จำนวนลูกค้า Walk in", style_cell_label), Paragraph(f"<b>{c_walk}</b> &nbsp; ราย", style_stat_val)],
        [Paragraph("จำนวนลูกค้านัดหมายวันนี้", style_cell_label), Paragraph(f"<b>{c_app}</b> &nbsp; ราย", style_stat_val)],
        [Paragraph("จำนวนลูกค้าจอง", style_cell_label), Paragraph(f"<b>{c_book}</b> &nbsp; ราย", style_stat_val)],
        [Paragraph("<b>จำนวน Call</b>", style_cell_label), ""],
        [Paragraph("ผู้จัดการสำนักงานขาย", style_cell_label), Paragraph(f"<b>{c_mgr}</b> &nbsp; ราย", style_stat_val)],
        [Paragraph("เจ้าหน้าที่ขายอาวุโส", style_cell_label), Paragraph(f"<b>{c_senior}</b> &nbsp; ราย", style_stat_val)],
        [Paragraph("<b>งานเพิ่มเติมระหว่างวันที่ต้องทำ:</b>", style_cell_label), ""],
        [Paragraph(f"{add_tasks}", style_textarea_text), ""]
    ]
    stats_subtable = Table(stats_sub_data, colWidths=[180, 75])
    stats_subtable.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('SPAN', (0, 4), (1, 4)),
        ('SPAN', (0, 7), (1, 7)),
        ('SPAN', (0, 8), (1, 8)),
    ]))

    ds_text = report.get('daily_summary', '') or '-'
    ds_formatted = "<br/>".join([line.strip() for line in ds_text.splitlines() if line.strip()]) or '-'
    ds_para = Paragraph(ds_formatted, style_textarea_text)

    table_rows.append([
        stats_subtable, "", "",
        ds_para
    ])
    t_styles.append(('SPAN', (0, 13), (2, 13)))
    t_styles.append(('VALIGN', (0, 13), (3, 13), 'TOP'))

    # Row 14: Section 2 Signature Headers
    table_rows.append([
        Paragraph("<b>พนักงานเซ็นรับทราบ</b>", style_sign_head),
        "", "",
        Paragraph("<b>ผู้จัดการสำนักงานขาย</b>", style_sign_head_right)
    ])
    t_styles.append(('SPAN', (0, 14), (2, 14)))
    t_styles.append(('BACKGROUND', (0, 14), (3, 14), colors.HexColor('#F8FAFC')))

    # Row 15: Section 2 Signatures Body
    mgr_s2_name = ts.get('manager_name_s2') or ts.get('staff_manager_s2') or ts.get('manager') or 'ผู้จัดการสำนักงานขาย'
    
    staff_s2_config = [
        ("1)", ts.get('staff_manager_s2_sig') or ts.get('manager_sig'), ts.get('staff_manager_s2') or ts.get('manager'), "ผู้จัดการสำนักงานขาย"),
        ("2)", ts.get('staff_senior_sale_s2_sig') or ts.get('senior_sale_sig'), ts.get('staff_senior_sale_s2') or ts.get('senior_sale'), "เจ้าหน้าที่ขายอาวุโส"),
        ("3)", ts.get('staff_coordinator_s2_sig') or ts.get('coordinator_sig'), ts.get('staff_coordinator_s2') or ts.get('coordinator'), "เจ้าหน้าที่ประสานงานขายและการตลาด"),
        ("4)", ts.get('staff_architect_s2_sig') or ts.get('architect_sig'), ts.get('staff_architect_s2') or ts.get('architect'), "สถาปนิกปรับแบบ"),
    ]
    
    staff_s2_sub_data = []
    for num, sig_base64, name, pos in staff_s2_config:
        clean_name = name.strip() if name and name.strip() else '..............................'
        sig_img = decode_base64_image(sig_base64, width=54, height=16)
        sig_cell = sig_img if sig_img else Paragraph("...................", style_sign_staff_dots)
        name_cell = Paragraph(f"<u>&nbsp; {clean_name} &nbsp;</u>", style_sign_staff_center)
        pos_cell = Paragraph(f"<i>{pos}</i>", style_sign_staff_pos)
        staff_s2_sub_data.append([
            Paragraph(f"<b>{num}</b>", style_sign_staff_num),
            sig_cell,
            name_cell,
            pos_cell
        ])
    
    staff_s2_subtable = Table(staff_s2_sub_data, colWidths=[14, 52, 84, 105])
    staff_s2_subtable.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
    ]))

    mgr_s2_sig_data = ts.get('manager_sig_s2') or ts.get('staff_manager_s2_sig') or ts.get('manager_sig')
    mgr_s2_sig_img = decode_base64_image(mgr_s2_sig_data, width=75, height=25)
    if mgr_s2_sig_img:
        mgr_s2_cell_elements = [
            mgr_s2_sig_img,
            Spacer(1, 2),
            Paragraph(f"(&nbsp; <u>&nbsp; {mgr_s2_name} &nbsp;</u> &nbsp;)", style_sign_manager)
        ]
    else:
        mgr_s2_cell_elements = [
            Paragraph("..............................................................", style_sign_manager),
            Paragraph(f"(&nbsp; <u>&nbsp; {mgr_s2_name} &nbsp;</u> &nbsp;)", style_sign_manager)
        ]

    table_rows.append([
        staff_s2_subtable, "", "",
        mgr_s2_cell_elements
    ])
    t_styles.append(('SPAN', (0, 15), (2, 15)))
    t_styles.append(('VALIGN', (0, 15), (3, 15), 'MIDDLE'))
    t_styles.append(('ALIGN', (3, 15), (3, 15), 'CENTER'))

    # Build Main Table
    main_table = Table(table_rows, colWidths=col_w)
    main_table.setStyle(TableStyle(t_styles))
    story.append(main_table)

    story.append(Spacer(1, 4))
    story.append(Paragraph("FM-MS-224 Rev.00", style_doc_code))

    # Optional Attached Photos Pages
    if report_photos and len(report_photos) > 0:
        story.append(PageBreak())
        style_photo_head = ParagraphStyle('PhotoHead', fontName='THSarabunNew-Bold', fontSize=14, leading=16, alignment=TA_LEFT, textColor=colors.HexColor('#0F172A'))
        story.append(Paragraph("<b>รูปถ่ายรายงานการปฏิบัติงานประจำวัน (แนบท้าย)</b>", style_photo_head))
        story.append(Spacer(1, 8))

        photo_cells = []
        for p_idx, p_path in enumerate(report_photos):
            img_flow = None
            if p_path.startswith('/static/'):
                rel_path = p_path.lstrip('/')
                full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), rel_path))
                if os.path.exists(full_path):
                    try:
                        img_flow = RLImage(full_path, width=250, height=180)
                    except Exception:
                        pass
            elif p_path.startswith('data:image'):
                img_flow = decode_base64_image(p_path, width=250, height=180)

            if img_flow:
                caption = Paragraph(f"รูปที่ {p_idx + 1}", ParagraphStyle('PNum', fontName='THSarabunNew-Bold', fontSize=10, leading=12, alignment=TA_CENTER))
                photo_cells.append([img_flow, caption])

        # Arrange photos in 2-column grid
        grid_rows = []
        for i in range(0, len(photo_cells), 2):
            row_data = []
            c1 = photo_cells[i]
            c1_table = Table([[c1[0]], [c1[1]]], colWidths=[260])
            c1_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
            row_data.append(c1_table)

            if i + 1 < len(photo_cells):
                c2 = photo_cells[i + 1]
                c2_table = Table([[c2[0]], [c2[1]]], colWidths=[260])
                c2_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
                row_data.append(c2_table)
            else:
                row_data.append("")
            grid_rows.append(row_data)

        if grid_rows:
            p_grid_table = Table(grid_rows, colWidths=[270, 270])
            p_grid_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 2), ('RIGHTPADDING', (0, 0), (-1, -1), 2)]))
            story.append(p_grid_table)

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_maid_schedule_pdf(schedule, sheet_data):
    """
    Generates an official landscape A4 PDF document for Maid Work Schedule (Daily & Weekly Checklist).
    """
    from maid_config import MAID_DAILY_TASKS, MAID_WEEKLY_TASKS, format_month_year_th, get_days_in_month

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=14,
        leftMargin=14,
        topMargin=14,
        bottomMargin=14
    )

    story = []

    # Styles
    title_style = ParagraphStyle('MTitle', fontName='THSarabunNew-Bold', fontSize=15, leading=17, alignment=TA_CENTER, textColor=colors.HexColor('#0F172A'))
    sub_style = ParagraphStyle('MSub', fontName='THSarabunNew', fontSize=10, leading=12, alignment=TA_CENTER, textColor=colors.HexColor('#475569'))
    info_style = ParagraphStyle('MInfo', fontName='THSarabunNew-Bold', fontSize=11, leading=13, alignment=TA_LEFT, textColor=colors.HexColor('#1E293B'))
    instruct_style = ParagraphStyle('MInstruct', fontName='THSarabunNew-BoldItalic', fontSize=9.5, leading=11, alignment=TA_LEFT, textColor=colors.HexColor('#DC2626'))
    
    th_center = ParagraphStyle('THC', fontName='THSarabunNew-Bold', fontSize=9, leading=10, alignment=TA_CENTER, textColor=colors.HexColor('#0F172A'))
    td_center = ParagraphStyle('TDC', fontName='THSarabunNew', fontSize=8.5, leading=9.5, alignment=TA_CENTER, textColor=colors.HexColor('#0F172A'))
    td_left = ParagraphStyle('TDL', fontName='THSarabunNew', fontSize=8.5, leading=10, alignment=TA_LEFT, textColor=colors.HexColor('#0F172A'))
    td_bold_left = ParagraphStyle('TDBL', fontName='THSarabunNew-Bold', fontSize=8.5, leading=10, alignment=TA_LEFT, textColor=colors.HexColor('#0F172A'))
    td_bold_center = ParagraphStyle('TDBC', fontName='THSarabunNew-Bold', fontSize=8.5, leading=10, alignment=TA_CENTER, textColor=colors.HexColor('#0F172A'))
    check_style = ParagraphStyle('Chk', fontName='THSarabunNew-Bold', fontSize=9, leading=9, alignment=TA_CENTER, textColor=colors.HexColor('#15803D'))
    initials_style = ParagraphStyle('Initials', fontName='THSarabunNew-Bold', fontSize=7.5, leading=8.5, alignment=TA_CENTER, textColor=colors.HexColor('#1E40AF'))

    branch = schedule.get('branch', '-')
    month_year = schedule.get('month_year', '')
    month_th = format_month_year_th(month_year)
    days_in_month = get_days_in_month(month_year)

    # 1. Header with Logo & Title
    logo_flowable = None
    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        try:
            logo_flowable = RLImage(logo_path, width=70, height=28)
        except Exception:
            logo_flowable = Paragraph("<b>SALES OFFICE</b>", th_center)

    header_cell_left = [
        Paragraph("<b>ตารางการทำงานแม่บ้าน สำนักงานขายประจำวัน</b>", title_style),
        Spacer(1, 2),
        Paragraph(f"สาขา: <b>{branch}</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ตารางเดือน: <b>{month_th}</b>", sub_style),
    ]

    header_table_data = [[
        Table([[c] for c in header_cell_left], colWidths=[700]),
        logo_flowable or ""
    ]]
    header_table = Table(header_table_data, colWidths=[700, 100])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)

    story.append(Paragraph("<b>คำแนะนำ:</b> ผู้จัดการสาขาตรวจและทำเครื่องหมายดังนี้: กรณีเรียบร้อยกรุณาใส่เครื่องหมาย <b>✓</b> / กรณีไม่เรียบร้อยให้เว้นว่างไว้ ให้ตรงกับช่องวันที่ตรวจ", instruct_style))
    story.append(Spacer(1, 3))

    # Calculate column widths for 31 days
    # Total available width in landscape A4: ~814 pt
    # Col 0 (ลำดับ): 22 pt
    # Col 1 (รายละเอียด): 165 pt
    # Col 2 (ช่วงเวลา): 65 pt
    # 31 day cols: (814 - 252) / 31 ≈ 18 pt each
    day_col_width = 18.0
    col_widths = [22, 165, 65] + [day_col_width] * 31

    # 2. Section 1: ประจำวัน (Daily Tasks)
    daily_data = sheet_data.get('daily', {})
    worker_initials = sheet_data.get('worker_initials', {})
    inspector_initials = sheet_data.get('inspector_initials', {})

    table_rows = []
    
    # Table Header Row 1: Section Title Span
    hdr_row1 = [
        Paragraph("<b>ลำดับ</b>", th_center),
        Paragraph("<b>รายละเอียด (ประจำวัน)</b>", th_center),
        Paragraph("<b>ช่วงเวลาทำงาน</b>", th_center),
    ] + [Paragraph(f"<b>{d}</b>", th_center) for d in range(1, 32)]
    table_rows.append(hdr_row1)

    tstyle = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
    ]

    for task in MAID_DAILY_TASKS:
        t_no = task['no']
        t_title = task['title']
        t_time = task['time_slot']
        is_brk = task.get('is_break', False)

        row = [
            Paragraph(str(t_no), td_center),
            Paragraph(t_title, td_bold_left if is_brk else td_left),
            Paragraph(t_time, td_center)
        ]

        for d in range(1, 32):
            if d > days_in_month:
                row.append("")
            elif is_brk:
                row.append(Paragraph("-", td_center))
            else:
                key = f"{t_no}_{d}"
                is_done = daily_data.get(key)
                if is_done:
                    row.append(Paragraph("✓", check_style))
                else:
                    row.append("")
        table_rows.append(row)

        curr_r = len(table_rows) - 1
        if is_brk:
            tstyle.append(('BACKGROUND', (0, curr_r), (-1, curr_r), colors.HexColor('#FEF3C7')))

    # Row: ชื่อผู้ทำ
    row_worker = [
        Paragraph("", td_center),
        Paragraph("<b>ชื่อผู้ทำ</b>", td_bold_left),
        Paragraph("-", td_center)
    ]
    for d in range(1, 32):
        if d > days_in_month:
            row_worker.append("")
        else:
            ini = str(worker_initials.get(str(d)) or worker_initials.get(d) or '').strip()
            row_worker.append(Paragraph(ini, initials_style) if ini else "")
    table_rows.append(row_worker)

    # Row: ชื่อผู้ตรวจ
    row_inspector = [
        Paragraph("", td_center),
        Paragraph("<b>ชื่อผู้ตรวจ</b>", td_bold_left),
        Paragraph("-", td_center)
    ]
    for d in range(1, 32):
        if d > days_in_month:
            row_inspector.append("")
        else:
            ini = str(inspector_initials.get(str(d)) or inspector_initials.get(d) or '').strip()
            row_inspector.append(Paragraph(ini, initials_style) if ini else "")
    table_rows.append(row_inspector)

    r_w_idx = len(table_rows) - 2
    r_i_idx = len(table_rows) - 1
    tstyle.append(('BACKGROUND', (0, r_w_idx), (-1, r_i_idx), colors.HexColor('#EFF6FF')))
    tstyle.append(('FONTNAME', (0, r_w_idx), (-1, r_i_idx), 'THSarabunNew-Bold'))

    daily_table = Table(table_rows, colWidths=col_widths)
    daily_table.setStyle(TableStyle(tstyle))
    story.append(daily_table)

    story.append(Spacer(1, 4))

    # 3. Section 2: ประจำสัปดาห์ (Weekly Tasks)
    weekly_data = sheet_data.get('weekly', {})
    weekly_worker_initials = sheet_data.get('weekly_worker_initials', {})
    weekly_inspector_initials = sheet_data.get('weekly_inspector_initials', {})

    w_table_rows = []
    w_hdr = [
        Paragraph("<b>ลำดับ</b>", th_center),
        Paragraph("<b>รายละเอียด</b>", th_center),
        Paragraph("<b>ช่วงเวลาทำงาน</b>", th_center),
    ] + [Paragraph(f"<b>{d}</b>", th_center) for d in range(1, 32)]
    w_table_rows.append(w_hdr)

    w_tstyle = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
    ]

    from maid_config import get_weekly_schedule_layout
    weekly_layout = get_weekly_schedule_layout(month_year)

    for task_no in [20, 21, 22, 23]:
        item = weekly_layout.get(task_no)
        if not item:
            continue
        task = item['task']
        row = [
            Paragraph(str(task['no']), td_center),
            Paragraph(task['title'], td_left),
            Paragraph(task['time_slot'], td_center)
        ]
        col_cursor = 3
        current_r_idx = len(w_table_rows)
        for seg in item['segments']:
            val = ""
            if seg['type'] == 'open':
                val = str(weekly_data.get(seg['key']) or weekly_data.get(str(task_no)) or '').strip()
                row.append(Paragraph(f"<b>{val}</b>" if val else "", td_bold_center))
            else:
                row.append("")

            # Fill empty strings for column span
            for _ in range(seg['colspan'] - 1):
                row.append("")

            end_col = col_cursor + seg['colspan'] - 1
            if seg['colspan'] > 1:
                w_tstyle.append(('SPAN', (col_cursor, current_r_idx), (end_col, current_r_idx)))
            if seg['type'] == 'blocked':
                w_tstyle.append(('BACKGROUND', (col_cursor, current_r_idx), (end_col, current_r_idx), colors.HexColor('#E2E8F0')))
            col_cursor += seg['colspan']

        w_table_rows.append(row)

    # Weekly Row: ชื่อผู้ทำ
    w_row_worker = [
        Paragraph("", td_center),
        Paragraph("<b>ชื่อผู้ทำ</b>", td_bold_left),
        Paragraph("-", td_center)
    ]
    for d in range(1, 32):
        if d > days_in_month:
            w_row_worker.append("")
        else:
            ini = str(weekly_worker_initials.get(str(d)) or weekly_worker_initials.get(d) or '').strip()
            w_row_worker.append(Paragraph(ini, initials_style) if ini else "")
    w_table_rows.append(w_row_worker)

    # Weekly Row: ชื่อผู้ตรวจ
    w_row_inspector = [
        Paragraph("", td_center),
        Paragraph("<b>ชื่อผู้ตรวจ</b>", td_bold_left),
        Paragraph("-", td_center)
    ]
    for d in range(1, 32):
        if d > days_in_month:
            w_row_inspector.append("")
        else:
            ini = str(weekly_inspector_initials.get(str(d)) or weekly_inspector_initials.get(d) or '').strip()
            w_row_inspector.append(Paragraph(ini, initials_style) if ini else "")
    w_table_rows.append(w_row_inspector)

    w_w_idx = len(w_table_rows) - 2
    w_i_idx = len(w_table_rows) - 1
    w_tstyle.append(('BACKGROUND', (0, w_w_idx), (-1, w_i_idx), colors.HexColor('#EFF6FF')))

    weekly_table = Table(w_table_rows, colWidths=col_widths)
    weekly_table.setStyle(TableStyle(w_tstyle))
    story.append(weekly_table)

    doc.build(story)
    buffer.seek(0)
    return buffer

