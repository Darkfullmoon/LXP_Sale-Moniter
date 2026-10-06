# -*- coding: utf-8 -*-
"""
Morning Audit Configuration and Structure (FM-MS-007 Rev.00)
รายงาน Morning Audit สำนักงานขาย (ประจำวัน)
"""

BRANCH_LIST = []

MORNING_AUDIT_STRUCTURE = [
    {
        "category_id": 1,
        "category_title": "หมวดที่ 1. ความสะอาดเรียบร้อยของสำนักงานขาย",
        "category_icon": "sparkles",
        "audit_items": [
            {
                "id": "c1_1",
                "no": 1,
                "title": "มีป้ายชื่อบริษัท ,โลโก้บริษัท , เลขที่อาคารติดเรียบร้อย (ถ้ามี) สีไม่ซีด สภาพสมบูรณ์",
                "evidence_fields": [
                    {"name": "c1_1_defect", "label": "กรณีพบว่าป้ายซีดหรือชำรุด", "type": "text", "placeholder": "ระบุจุดที่ซีดหรือชำรุด"},
                    {"name": "c1_1_target", "label": "Target แก้ไขแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c1_2",
                "no": 2,
                "title": "ป้ายกล้องวงจปิด (CCTV) ติดกระจกประตูทางเข้าสำนักงานขาย สภาพสมบูรณ์",
                "evidence_fields": [
                    {"name": "c1_2_defect", "label": "กรณีพบว่าป้ายซีดหรือชำรุด", "type": "text", "placeholder": "ระบุจุดที่ชำรุด/ซีด"},
                    {"name": "c1_2_target", "label": "Target แก้ไขแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c1_3",
                "no": 3,
                "title": "สำนักงานขายไม่มีขยะหรือกลิ่นไม่พึงประสงค์ และสะอาด",
                "evidence_fields": [
                    {"name": "c1_3_defect", "label": "กรณีพบว่าบริเวณใดไม่สะอาด", "type": "text", "placeholder": "ระบุบริเวณ/ปัญหาที่พบ"},
                    {"name": "c1_3_target", "label": "Target แก้ไขแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c1_4",
                "no": 4,
                "title": "เคาน์เตอร์พนักงานต้อนรับจัดเรียบร้อยเป็นระเบียบ สะอาด ไม่มีอาหารและเครื่องดื่ม",
                "evidence_fields": [
                    {"name": "c1_4_defect", "label": "กรณีพบว่าเคาน์เตอร์ไม่สะอาด", "type": "text", "placeholder": "ระบุสิ่งที่ต้องปรับปรุง"},
                    {"name": "c1_4_target", "label": "Target แก้ไขแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c1_5",
                "no": 5,
                "title": "เฟอร์นิเจอร์และ Built In มีสภาพสมบูรณ์ สะอาด",
                "evidence_fields": [
                    {"name": "c1_5_defect", "label": "ชื่อโมเดลชำรุด", "type": "text", "placeholder": "ระบุเฟอร์นิเจอร์/Built-in ที่ชำรุด"},
                    {"name": "c1_5_target", "label": "Target ซ่อมแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c1_6",
                "no": 6,
                "title": "อุปกรณ์ตกแต่ง อาทิ ดอกไม้ , แคตตาล็อก อยู่ในตำแหน่งที่ถูกต้อง เหมาะสม สะอาด",
                "evidence_fields": [
                    {"name": "c1_6_defect", "label": "กรณีแคตตาล็อกไม่ครบ", "type": "text", "placeholder": "ระบุรายการที่ขาด"},
                    {"name": "c1_6_qty", "label": "จำนวนที่เบิกเพิ่ม (เล่ม)", "type": "number", "placeholder": "0"}
                ]
            },
            {
                "id": "c1_7",
                "no": 7,
                "title": "จอ LED เปิดใช้งานปกติ สภาพสมบูรณ์ สะอาด",
                "evidence_fields": [
                    {"name": "c1_7_file", "label": "ระบุชื่อไฟล์ TV", "type": "text", "placeholder": "ระบุชื่อไฟล์ TV หรือปัญหาที่พบ"}
                ]
            },
            {
                "id": "c1_8",
                "no": 8,
                "title": "เครื่องปรับอากาศเปิดใช้งาน , อุณหภูมิที่เหมาะสม",
                "evidence_fields": [
                    {"name": "c1_8_temp", "label": "อุณหภูมิ (°C)", "type": "number", "placeholder": "เช่น 24"},
                    {"name": "c1_8_target", "label": "กรณีเครื่องปรับอากาศเสีย Target ซ่อม", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c1_9",
                "no": 9,
                "title": "แสงสว่างภายในโชว์รูมเพียงพอ เหมาะสม",
                "evidence_fields": [
                    {"name": "c1_9_area", "label": "กรณีแสงสว่างไม่เพียงพอ (ระบุบริเวณ)", "type": "text", "placeholder": "บริเวณที่แสงสว่างไม่พอ"},
                    {"name": "c1_9_target", "label": "Target แก้ไขแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c1_10",
                "no": 10,
                "title": "เก้าอี้ , โซฟา , หมอนอิง และเฟอร์นิเจอร์วางในตำแหน่งที่เหมาะสม สภาพสมบูรณ์",
                "evidence_fields": [
                    {"name": "c1_10_defect", "label": "กรณีชำรุด", "type": "text", "placeholder": "ระบุจุดที่ชำรุด/ไม่เหมาะสม"},
                    {"name": "c1_10_target", "label": "Target แก้ไขแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c1_11",
                "no": 11,
                "title": "เครื่องกระจายกลิ่นหอมเปิดใช้งาน มีกลิ่นที่เหมาะสมในบริเวณสำนักงานขาย",
                "evidence_fields": [
                    {"name": "c1_11_scent", "label": "ชื่อกลิ่นหอมที่ใช้งาน", "type": "text", "placeholder": "ระบุชื่อกลิ่นหอมที่ใช้งาน"}
                ]
            },
            {
                "id": "c1_12",
                "no": 12,
                "title": "เสียงเพลงเปิดคลอเบาๆ",
                "evidence_fields": [
                    {"name": "c1_12_song", "label": "โปรดระบุชื่อไฟล์เพลง", "type": "text", "placeholder": "ระบุชื่อไฟล์เพลงที่เปิด"}
                ]
            },
            {
                "id": "c1_13",
                "no": 13,
                "title": "เครื่องดื่ม + ขนมเพียงพอสำหรับรองรับลูกค้า",
                "evidence_fields": [
                    {"name": "c1_13_snack_exp", "label": "วันที่ขนมหมดอายุ", "type": "date", "placeholder": "วว/ดด/ปปปป"},
                    {"name": "c1_13_drink_exp", "label": "วันที่เครื่องดื่มหมดอายุ", "type": "date", "placeholder": "วว/ดด/ปปปป"},
                    {"name": "c1_13_water_qty", "label": "น้ำดื่มเหลือ (ขวด)", "type": "number", "placeholder": "0"}
                ]
            }
        ]
    },
    {
        "category_id": 2,
        "category_title": "หมวดที่ 2. ห้องรับรองลูกค้าและอุปกรณ์ประกอบการขาย",
        "category_icon": "coffee",
        "audit_items": [
            {
                "id": "c2_1",
                "no": 1,
                "title": "TV , อุปกรณ์พรีเซนต์ และรีโมทใช้งานได้ปกติ",
                "evidence_fields": [
                    {"name": "c2_1_file", "label": "ชื่อไฟล์ TV", "type": "text", "placeholder": "ระบุชื่อไฟล์ TV ที่เปิด หรือปัญหาที่พบ"}
                ]
            },
            {
                "id": "c2_2",
                "no": 2,
                "title": "เครื่องปรับอากาศเปิดใช้งาน , อุณหภูมิที่เหมาะสม",
                "evidence_fields": [
                    {"name": "c2_2_temp", "label": "อุณหภูมิ (°C)", "type": "number", "placeholder": "เช่น 24"},
                    {"name": "c2_2_target", "label": "กรณีเครื่องปรับอากาศเสีย Target ซ่อม", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c2_3",
                "no": 3,
                "title": "แสงสว่างภายในห้องรับรองเพียงพอ เหมาะสม",
                "evidence_fields": [
                    {"name": "c2_3_light_off", "label": "จำนวนหลอดไฟที่ดับ (ดวง)", "type": "number", "placeholder": "0"},
                    {"name": "c2_3_target", "label": "Target ซ่อมแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c2_4",
                "no": 4,
                "title": "โต๊ะ เก้าอี้ โซฟา และหมอนอิง วางในตำแหน่งที่จัดวาง เหมาะสม เรียบร้อย",
                "evidence_fields": [
                    {"name": "c2_4_defect", "label": "กรณีชำรุด", "type": "text", "placeholder": "ระบุจุดชำรุดหรือไม่เรียบร้อย"},
                    {"name": "c2_4_target", "label": "Target แก้ไขแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c2_5",
                "no": 5,
                "title": "เครื่องกระจายกลิ่นหอมเปิดใช้งาน กลิ่นที่เหมาะสมในบริเวณห้องรับรองลูกค้า",
                "evidence_fields": [
                    {"name": "c2_5_scent", "label": "ชื่อกลิ่นหอมที่ใช้งาน", "type": "text", "placeholder": "ระบุชื่อกลิ่นหอม"}
                ]
            },
            {
                "id": "c2_6",
                "no": 6,
                "title": "ห้องรับรองลูกค้าทุกห้องสะอาดเรียบร้อย ไม่มีขยะและกลิ่นไม่พึงประสงค์",
                "evidence_fields": [
                    {"name": "c2_6_defect", "label": "กรณีห้องไม่พร้อมใช้งาน", "type": "text", "placeholder": "ระบุห้องหรือบริเวณที่ไม่สะอาด/ไม่พร้อม"},
                    {"name": "c2_6_target", "label": "Target แก้ไขแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c2_7",
                "no": 7,
                "title": "Ipad อัปเดตข้อมูลและสามารถเชื่อมต่อทีวีใช้งานได้ปกติ",
                "evidence_fields": [
                    {"name": "c2_7_defect", "label": "ข้อมูล Ipad ที่ยังไม่อัปเดต", "type": "text", "placeholder": "ระบุข้อมูลที่ยังไม่อัปเดต"},
                    {"name": "c2_7_target", "label": "Target แก้ไขแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c2_8",
                "no": 8,
                "title": "แคตตาล็อกอัปเดตปัจจุบัน มีครบทุกแบรนด์",
                "evidence_fields": [
                    {"name": "c2_8_defect", "label": "กรณีแคตตาล็อกไม่ครบ", "type": "text", "placeholder": "ระบุแบรนด์ที่ขาด"},
                    {"name": "c2_8_qty", "label": "จำนวนที่เบิกเพิ่ม (เล่ม)", "type": "number", "placeholder": "0"}
                ]
            },
            {
                "id": "c2_9",
                "no": 9,
                "title": "แปลน A3 ข้อมูลประกอบการพรีเซนต์ของแต่ละแบรนด์อัปเดตและวางที่โต๊ะรับรอง",
                "evidence_fields": [
                    {"name": "c2_9_defect", "label": "แปลน A3 ไม่ครบ (ระบุชื่อแบรนด์)", "type": "text", "placeholder": "ระบุชื่อแบรนด์ที่ขาดหรือยังไม่อัปเดต"}
                ]
            }
        ]
    },
    {
        "category_id": 3,
        "category_title": "หมวดที่ 3. ความเรียบร้อยโซนโมเดล",
        "category_icon": "home",
        "audit_items": [
            {
                "id": "c3_1",
                "no": 1,
                "title": "โมเดลมีสภาพสมบูรณ์ สะอาด",
                "evidence_fields": [
                    {"name": "c3_1_defect", "label": "ชื่อโมเดลชำรุด (หลัง)", "type": "text", "placeholder": "ระบุชื่อโมเดลที่ชำรุด"},
                    {"name": "c3_1_target", "label": "Target ซ่อมแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c3_2",
                "no": 2,
                "title": "แปลนบ้าน A3 วางอยู่ใต้โมเดลทุกโมเดล (ยกเว้นบ้านแกรนด์อยู่บนฝาครอบบ้าน)",
                "evidence_fields": [
                    {"name": "c3_2_defect", "label": "แปลนบ้าน A3 ขาด (หลัง)", "type": "text", "placeholder": "ระบุโมเดลที่ขาด"},
                    {"name": "c3_2_target", "label": "Target อัปเดตเรียบร้อย", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c3_3",
                "no": 3,
                "title": "ตัวหนีบภาพ TIVE อยู่ในตำแหน่งทางขวามือของโมเดลและตรงกันทุกโมเดลในแนวตั้ง",
                "evidence_fields": [
                    {"name": "c3_3_defect", "label": "ป้าย TIVE ซีด/ไม่ครบ (หลัง)", "type": "text", "placeholder": "ระบุรุ่น/หลัง"},
                    {"name": "c3_3_target", "label": "Target อัปเดตเรียบร้อย", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c3_4",
                "no": 4,
                "title": "ป้ายราคามาตรฐานหน้าโมเดล ถูกต้อง สภาพสมบูรณ์",
                "evidence_fields": [
                    {"name": "c3_4_defect", "label": "ป้ายราคาที่ยังไม่อัปเดต (หลัง)", "type": "text", "placeholder": "ระบุรุ่น/หลัง"},
                    {"name": "c3_4_target", "label": "Target อัปเดตเรียบร้อย", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c3_5",
                "no": 5,
                "title": "แท่นวางโมเดลวางในตำแหน่งเหมาะสม สภาพสมบูรณ์ สะอาด",
                "evidence_fields": [
                    {"name": "c3_5_defect", "label": "แท่นวางโมเดลชำรุด (แท่น)", "type": "text", "placeholder": "ระบุแท่นที่ชำรุด"},
                    {"name": "c3_5_target", "label": "Target ซ่อมแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c3_6",
                "no": 6,
                "title": "สายไฟ LED และหลอดไฟ LED ที่ส่องโมเดลเปิดใช้งานปกติ ไม่พบฝุ่น",
                "evidence_fields": [
                    {"name": "c3_6_defect", "label": "จำนวนหลอดไฟที่ดับ (ดวง)", "type": "number", "placeholder": "0"},
                    {"name": "c3_6_target", "label": "Target ซ่อมแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            }
        ]
    },
    {
        "category_id": 4,
        "category_title": "หมวดที่ 4. ห้องวัสดุเรียบร้อย",
        "category_icon": "package",
        "audit_items": [
            {
                "id": "c4_1",
                "no": 1,
                "title": "วัสดุมีการอัปเดตถูกต้อง",
                "evidence_fields": [
                    {"name": "c4_1_defect", "label": "วัสดุที่ยังไม่อัปเดต (ชิ้น)", "type": "text", "placeholder": "ระบุรายการวัสดุ"},
                    {"name": "c4_1_target", "label": "Target อัปเดตเรียบร้อย", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c4_2",
                "no": 2,
                "title": "วัสดุติดตั้งในตำแหน่งที่ถูกต้อง",
                "evidence_fields": [
                    {"name": "c4_2_defect", "label": "วัสดุที่รอติดตั้ง (ชิ้น)", "type": "text", "placeholder": "ระบุรายการวัสดุ"},
                    {"name": "c4_2_target", "label": "Target ติดตั้งแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c4_3",
                "no": 3,
                "title": "วัสดุติดป้าย Label / ป้ายบ่งชี้ถูกต้อง",
                "evidence_fields": [
                    {"name": "c4_3_defect", "label": "ป้ายลาเบลวัสดุที่ยังไม่อัปเดต (ชิ้น)", "type": "text", "placeholder": "ระบุรายการ"},
                    {"name": "c4_3_target", "label": "Target ติดป้ายแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c4_4",
                "no": 4,
                "title": "สายไฟ LED และหลอดไฟ LED ที่ส่องวัสดุเปิดใช้งานปกติ",
                "evidence_fields": [
                    {"name": "c4_4_defect", "label": "จำนวนหลอดไฟที่ดับ (ดวง)", "type": "number", "placeholder": "0"},
                    {"name": "c4_4_target", "label": "Target แก้ไขแล้วเสร็จ", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            }
        ]
    },
    {
        "category_id": 5,
        "category_title": "หมวดที่ 5. เอกสารการขายต่างๆ",
        "category_icon": "file-text",
        "audit_items": [
            {
                "id": "c5_1",
                "no": 1,
                "title": "เอกสารการขายอัปเดตถูกต้อง",
                "evidence_fields": [
                    {"name": "c5_1_date", "label": "วันที่เอกสารเวียน Cal Sheet", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c5_2",
                "no": 2,
                "title": "ราคาโปรโมชั่น อัปเดตถูกต้อง",
                "evidence_fields": [
                    {"name": "c5_2_date", "label": "วันที่เอกสารเวียนราคาโปรโมชั่น (วันที่เริ่มใช้-วันสิ้นสุดโปรโมชั่น)", "type": "text", "placeholder": "เช่น 01/08/2026 - 31/08/2026"}
                ]
            },
            {
                "id": "c5_3",
                "no": 3,
                "title": "Price list อัปเดตถูกต้อง",
                "evidence_fields": [
                    {"name": "c5_3_date", "label": "วันที่เอกสารเวียน Price list", "type": "date", "placeholder": "วว/ดด/ปปปป"}
                ]
            },
            {
                "id": "c5_4",
                "no": 4,
                "title": "เอกสารต่างๆอัปเดตครบถ้วนและจัดเก็บในลิ้นชักที่เหมาะสมมีป้ายบ่งชี้",
                "evidence_fields": [
                    {"name": "c5_4_defect", "label": "เอกสารที่ยังไม่อัปเดต (ถ้ามี)", "type": "text", "placeholder": "ระบุรายการเอกสาร"}
                ]
            }
        ]
    }
]

# Calculate total audit items
TOTAL_AUDIT_ITEMS = sum(len(cat["audit_items"]) for cat in MORNING_AUDIT_STRUCTURE)

# Quick lookup map for item metadata
AUDIT_ITEMS_DICT = {}
for _cat in MORNING_AUDIT_STRUCTURE:
    for _itm in _cat.get("audit_items", []):
        AUDIT_ITEMS_DICT[_itm["id"]] = {
            "id": _itm.get("id"),
            "no": _itm.get("no"),
            "title": _itm.get("title"),
            "category": _cat.get("category_title")
        }
