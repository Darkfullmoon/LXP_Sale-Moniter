# 🏢 LXP Sale Monitor (ระบบตรวจและติดตามมาตรฐานสำนักงานขาย)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.1-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/Database-MySQL%20%2F%20MariaDB-orange.svg?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%20Flash-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![ReportLab](https://img.shields.io/badge/PDF-ReportLab%205.0-red.svg)](https://www.reportlab.com/)
[![Security](https://img.shields.io/badge/Security-CSRF%20%7C%20RBAC%20%7C%2090--day%20Expiry-green.svg)](#-enterprise-security--compliance)

เว็บแอปพลิเคชันระบบบริหารจัดการ ตรวจสอบมาตรฐาน และติดตามการดำเนินงานประจำวันของสำนักงานขายสาขา (Sales Office Operation & Audit System) รองรับการบันทึกแบบฟอร์มมาตรฐานองค์กร การประมวลผลและตรวจสอบภาพถ่ายด้วย **AI (Google Gemini)** การออกรายงานเอกสาร **PDF ภาษาไทย** อัตโนมัติ พร้อมแดชบอร์ดติดตามการส่งงานแบบ Real-time ตามรอบเวลา Cut-off

---

## 📑 สารบัญ (Table of Contents)

- [✨ ฟีเจอร์หลัก (Key Features)](#-ฟีเจอร์หลัก-key-features)
  - [1. Morning Audit (FM-MS-007 Rev.00)](#1-morning-audit-fm-ms-007-rev00)
  - [2. Daily Operation Report (FM-MS-224 Rev.00)](#2-daily-operation-report-fm-ms-224-rev00)
  - [3. Maid Cleaning Schedule](#3-maid-cleaning-schedule-ตารางการทำงานแม่บ้าน)
  - [4. Submission Monitor & Cut-off Tracking](#4-submission-monitor--cut-off-tracking)
  - [5. AI-Powered Smart Audit & Anti-Spoofing](#5-ai-powered-smart-audit--anti-spoofing)
  - [6. Weekly Customer Analytics](#6-weekly-customer-analytics)
- [🔒 Enterprise Security & Compliance](#-enterprise-security--compliance)
- [🛠️ สถาปัตยกรรมและเทคโนโลยี (Tech Stack)](#️-สถาปัตยกรรมและเทคโนโลยี-tech-stack)
- [📁 โครงสร้างโปรเจกต์ (Project Structure)](#-โครงสร้างโปรเจกต์-project-structure)
- [🚀 คู่มือการติดตั้งและเริ่มต้นใช้งาน (Installation & Setup)](#-คู่มือการติดตั้งและเริ่มต้นใช้งาน-installation--setup)
  - [สิ่งที่ต้องเตรียมล่วงหน้า (Prerequisites)](#สิ่งที่ต้องเตรียมล่วงหน้า-prerequisites)
  - [ขั้นตอนการติดตั้ง (Step-by-Step)](#ขั้นตอนการติดตั้ง-step-by-step)
- [⚙️ การตั้งค่าสภาพแวดล้อม (.env Configuration)](#️-การตั้งค่าสภาพแวดล้อม-env-configuration)
- [👤 ข้อมูลบัญชีผู้ใช้เริ่มต้น (Default Credentials)](#-ข้อมูลบัญชีผู้ใช้เริ่มต้น-default-credentials)
- [📄 มาตรฐานแบบฟอร์มที่รองรับ (Standard Forms)](#-มาตรฐานแบบฟอร์มที่รองรับ-standard-forms)
- [🏢 การจัดการสาขา (Branch Management)](#-การจัดการสาขา-branch-management)

---

## ✨ ฟีเจอร์หลัก (Key Features)

### 1. Morning Audit (FM-MS-007 Rev.00)
ระบบตรวจเช็กความพร้อมสำนักงานขายประจำวันตอนเช้า ครอบคลุมเกณฑ์มาตรฐาน **36 ข้อตรวจ** แบ่งออกเป็น 5 หมวดหลัก:
- **หมวดที่ 1 ความสะอาดเรียบร้อยของสำนักงานขาย (13 ข้อ):** ตรวจป้ายบริษัท, ป้าย CCTV, กลิ่น/ความสะอาด, เคาน์เตอร์ต้อนรับ, เฟอร์นิเจอร์, ดอกไม้/แคตตาล็อก, จอ LED, แอร์/อุณหภูมิ, แสงสว่าง, น้ำดื่ม/ขนม
- **หมวดที่ 2 ห้องรับรองลูกค้าและอุปกรณ์ประกอบการขาย (9 ข้อ):** TV/อุปกรณ์พรีเซนต์, แอร์, ไฟส่องสว่าง, โซฟา/หมอนอิง, กลิ่นหอม, ความพร้อมห้องรับรอง, iPad อัปเดต, แคตตาล็อกทุกแบรนด์, แปลนบ้าน A3
- **หมวดที่ 3 ความเรียบร้อยโซนโมเดล (6 ข้อ):** สภาพโมเดล, แปลนใต้โมเดล, ป้าย TIVE, ป้ายราคามาตรฐาน, แท่นวาง, ไฟ LED ส่องโมเดล
- **หมวดที่ 4 ห้องวัสดุเรียบร้อย (4 ข้อ):** วัสดุอัปเดต, ตำแหน่งติดตั้ง, ป้าย Label บ่งชี้, ไฟ LED ห้องวัสดุ
- **หมวดที่ 5 เอกสารการขายต่างๆ (4 ข้อ):** Cal Sheet, ราคาโปรโมชั่น, Price list, การจัดเก็บในลิ้นชัก
- 📸 บันทึกหลักฐานรูปถ่าย (Defect Photo) พร้อมระบุวันที่เป้าหมายการแก้ไข (Target Date)
- 🖨️ ออกรายงานสรุปผลการตรวจเป็นเอกสาร PDF ภาษาไทยมาตรฐาน (THSarabunNew)

### 2. Daily Operation Report (FM-MS-224 Rev.00)
รายงานสรุปการปฏิบัติงานประจำวันของแต่ละสาขา:
- บันทึกข้อความ Morning Brief ประจำวัน
- สรุปงานประจำวัน (Daily Summary) และงานที่ได้รับมอบหมายเพิ่มเติม (Additional Tasks)
- สถิติผู้เข้าเยี่ยมชมสำนักงานขาย (Walk-in, นัดหมายล่วงหน้า, ทำสัญญา, สอบถามทางโทรศัพท์)
- บันทึก Manpower กำลังพล และรายชื่อทีมงานที่ปฏิบัติหน้าที่
- 🔗 **Smart Link Sync:** ดึงข้อมูลกำลังพล, Morning Brief และรูปถ่ายจาก Morning Audit ของวันเดียวกันมาเชื่อมโยงให้อัตโนมัติ
- 🖨️ ดาวน์โหลดรายงานการปฏิบัติงานเป็น PDF พร้อมตารางและลายเซ็นผู้รับผิดชอบ

### 3. Maid Cleaning Schedule (ตารางการทำงานแม่บ้าน)
ระบบบันทึกและตรวจสอบตารางการปฏิบัติงานของแม่บ้านประจำสำนักงานขาย:
- **งานประจำวัน (Daily Tasks):** 19 ลำดับงานตามช่วงเวลา (เช่น เปิดไฟฟ้า 08:00, เตรียมเครื่องดื่ม 08:10, ถูพื้นแต่ละชั้น, เช็ดกระจก, ทำความสะอาดห้องน้ำ ฯลฯ)
- **งานประจำสัปดาห์ (Weekly Tasks):** 4 ภารกิจ Deep Cleaning
- บันทึกผลรายเดือน ตรวจสอบประวัติย้อนหลัง และ Export ออกเป็น PDF ประจำเดือน

### 4. Submission Monitor & Cut-off Tracking
แดชบอร์ดสำหรับผู้บริหารและฝ่ายปฏิบัติการ ติดตามสถานะการส่งรายงานของแต่ละสาขาแบบ Real-time:
- ⏰ **รอบเช้า (Morning Cut-off):** กำหนดส่งภายใน **09:15 น.**
- ⏰ **รอบเย็น (Evening Cut-off):** กำหนดส่งภายใน **17:00 น.**
- แสดง Badge แจ้งเตือนสถานะทันที: `ตรงเวลา (On Time)`, `ส่งช้า (Late)`, หรือ `ยังไม่ส่ง (Missing)`
- ตัวกรองวันที่ย้อนหลัง และตัวกรองเจาะจงรายสาขา

### 5. AI-Powered Smart Audit & Anti-Spoofing
ผสานพลัง **Google Gemini (gemini-2.5-flash / gemini-3.5-flash)** ยกระดับความถูกต้องและความน่าเชื่อถือ:
- 🧠 **Executive Summary Generation:** วิเคราะห์ผลการตรวจ Morning Audit อัตโนมัติ พร้อมสรุปจุดบกพร่องและข้อเสนอแนะเชิงรุก
- 🛡️ **Anti-Spoofing Screen Detection:** ตรวจสอบว่าภาพถ่ายพนักงานถ่ายจากคนจริงในสำนักงานจริง หรือเป็นการถ่ายซ้ำจากหน้าจอคอมพิวเตอร์/จอมอนิเตอร์
- 👥 **Headcount & Full-Body Verification:** ตรวจนับจำนวนพนักงานจริงในภาพเปรียบเทียบกับจำนวนที่รายงาน พร้อมตรวจว่าถ่ายเห็นเต็มตัว (ศีรษะจรดเท้า) หรือไม่
- 👔 **Dress Code Compliance:** ตรวจสอบความถูกต้องของยูนิฟอร์มพนักงานตามมาตรฐานของบริษัทเทียบกับภาพ Reference

### 6. Weekly Customer Analytics
- หน้าแดชบอร์ดสรุปยอดจำนวนลูกค้าประจำสัปดาห์ (Weekly Customer Traffic)
- เปรียบเทียบสถิติระหว่างสาขาเพื่อสนับสนุนการวางแผนงานขาย

---

## 🔒 Enterprise Security & Compliance

- **3-Letter Uppercase Username:** บังคับรูปแบบ Username ต้องเป็นอักษรภาษาอังกฤษพิมพ์ใหญ่ 3 ตัวเท่านั้น (เช่น `ADM`, `USR`, `BKK`) ตาม Format `^[A-Z]{3}$`
- **90-Day Password Expiration:** รหัสผ่านมีอายุ 90 วัน (3 เดือน) หากหมดอายุระบบจะบังคับให้เปลี่ยนรหัสผ่านใหม่ก่อนเข้าใช้งาน
- **Forced Password Change on First Login:** บัญชีที่เข้าสู่ระบบครั้งแรกด้วยรหัสผ่านเริ่มต้น จะต้องเปลี่ยนรหัสผ่านทันที
- **Strict Password Policy:** รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 8 ตัวอักษร ประกอบด้วยพิมพ์ใหญ่ (A-Z), พิมพ์เล็ก (a-z), ตัวเลข (0-9) และอักขระพิเศษ
- **CSRF Protection:** ป้องกัน Cross-Site Request Forgery แบบครอบคลุมทุก Mutating HTTP Methods (POST, PUT, PATCH, DELETE) ทั้งแบบ Web Form และ AJAX Request
- **Absolute Session Lifetime:** เซสชันตัดการเชื่อมต่ออัตโนมัติภายใน 24 ชั่วโมง พร้อม `HTTPOnly` และ `SameSite=Lax` Cookie
- **High-Performance Image Optimization:** ย่อขนาดรูปถ่ายและบีบอัดเป็นฟอร์แมต `.webp` อัตโนมัติด้วย Pillow Lanczos ป้องกันเซิร์ฟเวอร์เต็มและโหลดได้รวดเร็ว
- **Data Retention & Privacy Policy:** มีฟังก์ชันล้างข้อมูลย้อนหลังตามนโยบายจัดเก็บข้อมูลขององค์กร

---

## 🛠️ สถาปัตยกรรมและเทคโนโลยี (Tech Stack)

| ส่วนประกอบ | เทคโนโลยีที่เลือกใช้ |
|---|---|
| **Backend Framework** | [Python 3.10+](https://www.python.org/) & [Flask 3.1](https://flask.palletsprojects.com/) (Modular Blueprint Architecture) |
| **Database** | [MySQL](https://www.mysql.com/) / MariaDB (Driver: `PyMySQL` utf8mb4) |
| **Artificial Intelligence** | [Google Gemini API](https://ai.google.dev/) (`gemini-2.5-flash`, `gemini-3.5-flash`) |
| **PDF Generation** | [ReportLab 5.0](https://www.reportlab.com/) + Custom Thai TrueType Fonts (`THSarabunNew`) |
| **Image Processing** | [Pillow 12.x](https://python-pillow.org/) (WebP conversion & auto-orientation) |
| **Frontend** | Vanilla HTML5, CSS3 (Modern Glassmorphism, Responsive Dark/Light UI), JavaScript ES6+ |
| **Icons & UI** | Font Awesome 6 & Lucide Icons |
| **Security & Auth** | Werkzeug Security, Secrets, HMAC CSRF Validation |

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
Lxp_sale_monitor/
├── app.py                      # จุดเริ่มต้นแอปพลิเคชัน Flask & Blueprints Registration
├── db.py                       # ระบบเชื่อมต่อฐานข้อมูล MySQL & การสร้างตารางอัตโนมัติ
├── audit_config.py             # โครงสร้างแบบฟอร์มตรวจ Morning Audit 36 ข้อ (FM-MS-007)
├── maid_config.py              # โครงสร้างตารางงานแม่บ้านประจำวัน/สัปดาห์
├── pdf_generator.py            # เอนจินสร้างไฟล์ PDF ภาษาไทย (ReportLab)
├── utils.py                    # โมดูลฟังก์ชันช่วยเหลือ, ตรวจสอบความปลอดภัย, เชื่อมต่อ Gemini AI
├── requirements.txt            # รายการไลบรารี Python ที่โปรเจกต์ต้องการ
├── .env.example                # ตัวอย่างไฟล์ตั้งค่า Environment Variables
├── mysql.sql / mydb.sql        # สคริปต์ฐานข้อมูลสำรองสำหรับ Import เริ่มต้น
├── font/                       # ฟอนต์ภาษาไทยสำหรับสร้าง PDF (THSarabunNew)
│   ├── THSarabunNew.ttf
│   ├── THSarabunNew Bold.ttf
│   ├── THSarabunNew Italic.ttf
│   └── THSarabunNew BoldItalic.ttf
├── routes/                     # แยกระบบการทำงานด้วย Flask Blueprints
│   ├── __init__.py             # ฟังก์ชันลงทะเบียน Blueprints ทั้งหมด
│   ├── auth.py                 # ระบบยืนยันตัวตน, เปลี่ยนรหัสผ่าน, สมัครผู้ใช้
│   ├── dashboard.py            # แดชบอร์ดหลักและภาพรวมระบบ
│   ├── morning_audit.py        # ระบบ Morning Audit, อัปโหลดรูป, AI Analysis, PDF
│   ├── daily_report.py         # ระบบ Daily Operation Report, Manpower, PDF
│   ├── maid.py                 # ระบบตารางงานแม่บ้านประจำเดือน และ PDF
│   ├── admin.py                # การจัดการผู้ใช้, สาขา, Submission Monitor, ล้างข้อมูล
│   └── inspection.py           # ระบบตรวจเช็กสภาพทรัพย์สิน/อุปกรณ์ (Pending/Approved)
├── templates/                  # หน้าเว็บ Jinja2 Templates (HTML)
│   ├── app_layout.html         # โครงสร้างหน้าเว็บหลัก (Sidebar, Navbar, Theme)
│   ├── login.html              # หน้าเข้าสู่ระบบ
│   ├── morning_audit.html      # แบบฟอร์มตรวจเช็ก Morning Audit
│   ├── daily_report.html       # แบบฟอร์มบันทึก Daily Operation Report
│   ├── maid_schedule.html      # แบบฟอร์มและตารางงานแม่บ้าน
│   ├── submission_monitor.html # หน้าจอติดตามเวลาส่งงานประจำวัน
│   └── ...                     # หน้าจอจัดการอื่นๆ
└── static/                     # ไฟล์สถิต (CSS, JS, โลโก้ และโฟลเดอร์เก็บรูปอัปโหลด)
```

---

## 🚀 คู่มือการติดตั้งและเริ่มต้นใช้งาน (Installation & Setup)

### สิ่งที่ต้องเตรียมล่วงหน้า (Prerequisites)
1. **Python 3.10** ขึ้นไป ([ดาวน์โหลดที่นี่](https://www.python.org/downloads/))
2. **MySQL Server 8.0+** หรือ **MariaDB 10.4+** (เปิดใช้งาน service พอร์ต 3306)
3. **Git** สำหรับ Clone โค้ด

---

### ขั้นตอนการติดตั้ง (Step-by-Step)

#### 1. Clone คลังเก็บโค้ด (Clone Repository)
```bash
git clone https://github.com/Darkfullmoon/LXP_Sale-Moniter.git
cd LXP_Sale-Moniter
```

#### 2. สร้างและเปิดใช้งาน Virtual Environment
- **บน Windows:**
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate
  ```
- **บน macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

#### 3. ติดตั้ง Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. ตั้งค่าตัวแปรสภาพแวดล้อม (.env)
คัดลอกไฟล์ตัวอย่าง `.env.example` แล้วสร้างไฟล์ `.env`:
```bash
# Windows Command Prompt
copy .env.example .env

# PowerShell หรือ Linux/macOS
cp .env.example .env
```
เปิดไฟล์ `.env` แล้วแก้ไขข้อมูลการเชื่อมต่อ MySQL และ API Key ของคุณ (ดูรายละเอียดใน [หัวข้อถัดไป](#️-การตั้งค่าสภาพแวดล้อม-env-configuration))

#### 5. เตรียมฐานข้อมูล (Database Setup)
ระบบมีฟังก์ชัน `init_db()` ในตัวที่จะ **สร้างฐานข้อมูลและตารางที่จำเป็นทั้งหมดให้อัตโนมัติ** เมื่อรันแอปพลิเคชันครั้งแรก พร้อมใส่ข้อมูลสาขาเริ่มต้น 11 สาขา และบัญชี Admin เริ่มต้นให้ทันที

*(ทางเลือกเพิ่มเติม)* หากต้องการ Import โครงสร้างและข้อมูลตัวอย่างด้วยตนเองผ่าน phpMyAdmin หรือ MySQL CLI:
```bash
mysql -u root -p < mydb.sql
```

#### 6. เริ่มต้นรันแอปพลิเคชัน (Run Server)
```bash
python app.py
```
เมื่อรันสำเร็จ หน้าจอจะแสดงลิงก์สำหรับเข้าใช้งาน:
```text
* Running on http://127.0.0.1:5000
* Running on http://<YOUR_LOCAL_IP>:5000 (เปิดจากมือถือ/แท็บเล็ตในเครือข่ายเดียวกันได้)
```
เปิดเบราว์เซอร์ไปที่ `http://localhost:5000` เพื่อเข้าสู่ระบบ

---

## ⚙️ การตั้งค่าสภาพแวดล้อม (.env Configuration)

ตัวอย่างค่าคอนฟิกในไฟล์ `.env`:

```ini
# ==========================================
# Database Configuration
# ==========================================
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=mydb

# ==========================================
# Flask Application Security
# ==========================================
SECRET_KEY=generate_a_very_secure_random_key_here
FLASK_ENV=development
FLASK_DEBUG=1

# ==========================================
# Google Gemini API Keys (สำหรับระบบ AI ตรวจสอบ)
# ==========================================
GEMINI_API_KEY1=your_primary_google_gemini_api_key
GEMINI_API_KEY2=your_secondary_backup_gemini_api_key
```

> **หมายเหตุ:** สามารถขอรับ Google Gemini API Key ได้ฟรีผ่าน [Google AI Studio](https://aistudio.google.com/)

---

## 👤 ข้อมูลบัญชีผู้ใช้เริ่มต้น (Default Credentials)

เมื่อระบบเริ่มต้นการทำงานครั้งแรก จะสร้างบัญชีผู้ใช้มาตรฐานให้โดยอัตโนมัติ:

| Username | Role | รหัสผ่านเริ่มต้น | เงื่อนไขการเข้าใช้งาน |
|---|---|---|---|
| **`ADM`** | **ADMIN** (ผู้ดูแลระบบ) | `Test*123` | มีสิทธิ์เข้าถึงทุกเมนู, จัดการผู้ใช้, จัดการสาขา, ล้างประวัติ |
| **`USR`** | **USER** (เจ้าหน้าที่สาขา) | `Test*123` | **บังคับเปลี่ยนรหัสผ่านทันที** ในการเข้าสู่ระบบครั้งแรก |

### การเพิ่มบัญชีพนักงานใหม่ (Auto-Provisioning)
- พนักงานสามารถล็อกอินด้วย **ตัวอักษรภาษาอังกฤษพิมพ์ใหญ่ 3 ตัว** (เช่น `BKK`, `LPR`, `RYG`)
- ใส่รหัสผ่านเริ่มต้น `Test*123`
- ระบบจะสร้างบัญชีให้ใหม่อัตโนมัติ และนำทางไปยังหน้า **"เปลี่ยนรหัสผ่าน"** เพื่อตั้งรหัสผ่านส่วนตัวตามมาตรฐานความปลอดภัยก่อนเข้าใช้งาน

---

## 📄 มาตรฐานแบบฟอร์มที่รองรับ (Standard Forms)

| รหัสแบบฟอร์ม | ชื่อแบบฟอร์ม | คำอธิบาย |
|---|---|---|
| **FM-MS-007 Rev.00** | รายงาน Morning Audit สำนักงานขาย (ประจำวัน) | ตรวจเช็กมาตรฐานความสะอาด ความพร้อมโซนโมเดล อุปกรณ์ขาย และห้องวัสดุ 36 รายการ |
| **FM-MS-224 Rev.00** | Daily Operation Report | สรุปผลการดำเนินงานประจำวัน ข้อความบรีฟ ยอดลูกค้า กำลังพล และงานมอบหมายพิเศษ |
| **FM-MS Maid Schedule** | ตารางการทำงานแม่บ้าน สำนักงานขายประจำวัน / สัปดาห์ | เช็กลิสต์การทำความสะอาดและดูแลสุขอนามัย 19 งานประจำวัน และ 4 งานประจำสัปดาห์ |

---

## 🏢 การจัดการสาขา (Branch Management)

ระบบรองรับการเพิ่มและจัดการรายชื่อสาขาได้อย่างอิสระและยืดหยุ่น:
- ฐานข้อมูลเริ่มต้นจะถูกเตรียมไว้ให้พร้อมใช้งานโดยไม่มีการผูกมัดกับสาขาใด
- ผู้ดูแลระบบ (Admin) สามารถเพิ่มและลบสาขาที่ต้องการได้ทันทีผ่านเมนู **"เพิ่มสาขา" (Admin Branches)**
- เมื่อเพิ่มสาขาใหม่ ระบบจะอัปเดตตัวเลือกสาขาในทุกฟอร์ม รายงาน และแดชบอร์ดโดยอัตโนมัติ

