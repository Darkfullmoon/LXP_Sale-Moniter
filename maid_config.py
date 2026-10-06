# -*- coding: utf-8 -*-
"""
Maid Work Schedule Checklist Configuration.
Defines all 19 daily tasks and 4 weekly tasks from Landy Home FM Maid Schedule Form.
"""

# Daily Tasks (ประจำวัน - ลำดับ 1 ถึง 19)
MAID_DAILY_TASKS = [
    {
        "no": 1,
        "title": "เปิดไฟฟ้าสาขา เปิดไฟโมเดล เปิดทีวี และตู้กดน้ำโพง",
        "time_slot": "08.00 - 08.10",
        "is_break": False
    },
    {
        "no": 2,
        "title": "เตรียมพื้นที่และอุปกรณ์ชงเครื่องดื่ม ขนมสำหรับลูกค้า",
        "time_slot": "08.10 - 08.30",
        "is_break": False
    },
    {
        "no": 3,
        "title": "ทำความสะอาดพื้นและถูพื้น ชั้น 1",
        "time_slot": "08.30 - 09.00",
        "is_break": False
    },
    {
        "no": 4,
        "title": "ทำความสะอาดพื้นและถูพื้น ชั้น 2 และ 3",
        "time_slot": "09.00 - 09.30",
        "is_break": False
    },
    {
        "no": 5,
        "title": "เช็ดโต๊ะพนักงาน พื้นที่ขาย และชั้นเอกสารต่างๆ",
        "time_slot": "09.30 - 10.00",
        "is_break": False
    },
    {
        "no": 6,
        "title": "เช็ดทำความสะอาดกระจกหน้าสาขา บานประตูด้านหน้า",
        "time_slot": "10.00 - 10.30",
        "is_break": False
    },
    {
        "no": 7,
        "title": "พักเบรค",
        "time_slot": "10.30 - 10.45",
        "is_break": True
    },
    {
        "no": 8,
        "title": "เช็ดทำความสะอาดห้องวัสดุและพื้นที่ห้องวัสดุ",
        "time_slot": "10.45 - 11.00",
        "is_break": False
    },
    {
        "no": 9,
        "title": "เช็ดทำความสะอาดชั้นวางโมเดลทั้งหมด และบริเวณอื่นๆ",
        "time_slot": "11.00 - 11.30",
        "is_break": False
    },
    {
        "no": 10,
        "title": "เช็ดทำความสะอาดโมเดลทั้งหมด",
        "time_slot": "11.30 - 12.00",
        "is_break": False
    },
    {
        "no": 11,
        "title": "พักเบรคกลางวัน",
        "time_slot": "12.00 - 13.00",
        "is_break": True
    },
    {
        "no": 12,
        "title": "เช็ดทำความสะอาดกระจกภายในสาขา และห้องประชุม",
        "time_slot": "13.00 - 13.30",
        "is_break": False
    },
    {
        "no": 13,
        "title": "ทำความสะอาดห้องน้ำ ทั้ง 2 ห้อง",
        "time_slot": "13.30 - 14.00",
        "is_break": False
    },
    {
        "no": 14,
        "title": "ทำความสะอาดลานพนักงานขาย มุมโรงอาหารต่างๆ",
        "time_slot": "14.00 - 14.15",
        "is_break": False
    },
    {
        "no": 15,
        "title": "ทำความสะอาดเพดานในสาขา",
        "time_slot": "14.15 - 14.30",
        "is_break": False
    },
    {
        "no": 16,
        "title": "จัดเก็บของภายในสาขาให้เป็นระเบียบ เรียบร้อย",
        "time_slot": "14.30 - 14.45",
        "is_break": False
    },
    {
        "no": 17,
        "title": "ต้มน้ำร้อน / ชงน้ำสำหรับลูกค้า และซักผ้าเช็ดโต๊ะและผ้าต่างๆ",
        "time_slot": "14.45 - 15.00",
        "is_break": False
    },
    {
        "no": 18,
        "title": "ตกแต่งต้นไม้หน้าสาขา และทำความสะอาดบริเวณหน้าสาขา",
        "time_slot": "15.00 - 15.30",
        "is_break": False
    },
    {
        "no": 19,
        "title": "เก็บขยะ, นำขยะทิ้งให้เรียบร้อยและเปลี่ยนถุงขยะทันที",
        "time_slot": "15.30 - 16.00",
        "is_break": False
    }
]

# Weekly Tasks (ประจำสัปดาห์ - ลำดับ 20 ถึง 23)
MAID_WEEKLY_TASKS = [
    {
        "no": 20,
        "title": "ทำความสะอาดตู้เย็น และจัดเรียงน้ำดื่มให้เรียบร้อย เช็ควันหมดอายุ",
        "time_slot": "ช่วงเช้า"
    },
    {
        "no": 21,
        "title": "ทำความสะอาดเครื่องทำกาแฟ, เครื่องทำน้ำร้อนและอุปกรณ์ไฟฟ้า",
        "time_slot": "ช่วงเช้า"
    },
    {
        "no": 22,
        "title": "ทำความสะอาดภาพรวมภายในสาขา ตามหลัก 5 ส.",
        "time_slot": "ช่วงเย็น"
    },
    {
        "no": 23,
        "title": "ทำความสะอาดห้องเก็บของ ตามหลัก 5 ส.",
        "time_slot": "ช่วงเย็น"
    }
]

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]


def format_month_year_th(month_year_str):
    """
    Converts 'YYYY-MM' (e.g. '2026-08') to 'สิงหาคม 2569'.
    """
    if not month_year_str or '-' not in str(month_year_str):
        return str(month_year_str or '')
    try:
        parts = str(month_year_str).split('-')
        y_int = int(parts[0])
        m_int = int(parts[1])
        th_m = THAI_MONTHS[m_int] if 1 <= m_int <= 12 else str(m_int)
        th_y = y_int + 543
        return f"{th_m} {th_y}"
    except Exception:
        return str(month_year_str)


def get_days_in_month(month_year_str):
    """
    Returns the number of days in the given 'YYYY-MM' string (e.g. 28, 29, 30, 31).
    """
    import calendar
    try:
        parts = str(month_year_str).split('-')
        return calendar.monthrange(int(parts[0]), int(parts[1]))[1]
    except Exception:
        return 31


from datetime import date

WEEKLY_BASE_DATE = date(2026, 8, 1)


def get_weekly_schedule_layout(month_year_str, today_day=None, is_current_month=False, is_admin=False):
    """
    Computes the continuous 7-day rolling cycle for weekly tasks (20, 21, 22, 23).
    Rolls continuously across month boundaries every 7 days.
    """
    try:
        parts = str(month_year_str).split('-')
        year = int(parts[0])
        month = int(parts[1])
    except Exception:
        year, month = 2026, 8

    days_in_month = get_days_in_month(month_year_str)

    layout = {}
    for task in MAID_WEEKLY_TASKS:
        task_no = task['no']
        day_status = []
        for d in range(1, 32):
            if d > days_in_month:
                day_status.append({
                    'day': d,
                    'type': 'blocked',
                    'is_editable': False,
                    'disabled': True
                })
            else:
                d_date = date(year, month, d)
                day_offset = (d_date - WEEKLY_BASE_DATE).days
                active_task_no = 20 + ((day_offset // 7) % 4)

                if active_task_no == task_no:
                    # Check if today is in this 7-day cycle
                    week_start_offset = (day_offset // 7) * 7
                    week_end_offset = week_start_offset + 6

                    if is_admin:
                        is_editable = True
                    elif is_current_month and today_day:
                        today_date = date(year, month, today_day)
                        today_offset = (today_date - WEEKLY_BASE_DATE).days
                        is_editable = (week_start_offset <= today_offset <= week_end_offset)
                    else:
                        is_editable = False

                    day_status.append({
                        'day': d,
                        'type': 'open',
                        'is_editable': is_editable,
                        'disabled': False
                    })
                else:
                    day_status.append({
                        'day': d,
                        'type': 'blocked',
                        'is_editable': False,
                        'disabled': False
                    })

        # Merge contiguous days into segments
        segments = []
        open_seg_count = 0
        current_seg = None
        for item in day_status:
            t = item['type']
            if current_seg is None:
                current_seg = {
                    'type': t,
                    'start_day': item['day'],
                    'end_day': item['day'],
                    'colspan': 1,
                    'is_editable': item['is_editable'],
                    'disabled': item['disabled']
                }
            elif current_seg['type'] == t and (t == 'blocked' or current_seg['is_editable'] == item['is_editable']):
                current_seg['end_day'] = item['day']
                current_seg['colspan'] += 1
            else:
                if current_seg['type'] == 'open':
                    open_seg_count += 1
                    current_seg['key'] = f"{task_no}" if open_seg_count == 1 else f"{task_no}_{open_seg_count}"
                segments.append(current_seg)
                current_seg = {
                    'type': t,
                    'start_day': item['day'],
                    'end_day': item['day'],
                    'colspan': 1,
                    'is_editable': item['is_editable'],
                    'disabled': item['disabled']
                }
        if current_seg:
            if current_seg['type'] == 'open':
                open_seg_count += 1
                current_seg['key'] = f"{task_no}" if open_seg_count == 1 else f"{task_no}_{open_seg_count}"
            segments.append(current_seg)

        layout[task_no] = {
            'task': task,
            'segments': segments
        }

    return layout


def get_active_week_info(month_year_str, today_day=None, is_current_month=False):
    """
    Returns active 7-day window info for user mobile view:
    {
        'days': [22, 23, 24, 25, 26, 27, 28],
        'start_day': 22,
        'end_day': 28,
        'active_task_no': 23
    }
    """
    from datetime import date, timedelta
    try:
        parts = str(month_year_str).split('-')
        year = int(parts[0])
        month = int(parts[1])
    except Exception:
        year, month = 2026, 8

    days_in_month = get_days_in_month(month_year_str)
    target_day = today_day if (is_current_month and today_day) else min(days_in_month, max(1, today_day or 1))
    target_date = date(year, month, target_day)
    day_offset = (target_date - WEEKLY_BASE_DATE).days

    active_task_no = 20 + ((day_offset // 7) % 4)

    week_start_offset = (day_offset // 7) * 7
    week_start_date = WEEKLY_BASE_DATE + timedelta(days=week_start_offset)
    week_end_date = week_start_date + timedelta(days=6)

    active_days = []
    for d in range(1, days_in_month + 1):
        d_date = date(year, month, d)
        if week_start_date <= d_date <= week_end_date:
            active_days.append(d)

    if not active_days:
        active_days = list(range(1, min(8, days_in_month + 1)))

    return {
        'days': active_days,
        'start_day': active_days[0],
        'end_day': active_days[-1],
        'active_task_no': active_task_no
    }
