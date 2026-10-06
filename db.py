import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_NAME = os.getenv("DB_NAME", "mydb")

def get_db_connection():
    """Create and return a MySQL connection to the configured database."""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def init_db():
    """
    Initialize MySQL database, users, and inspections tables.
    Creates default user 'ADMIN' with password '123456' and role 'ADMIN'.
    """
    try:
        # Step 1: Attempt to create database if permitted
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                charset="utf8mb4",
                autocommit=True
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()
        except Exception:
            pass

        # Step 2: Connect to the specific database and create tables
        db_conn = get_db_connection()
        with db_conn.cursor() as cursor:
            # Users table with password_changed_at for 3-month expiration policy and is_first_login
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `users` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `username` VARCHAR(50) NOT NULL UNIQUE,
                    `password_hash` VARCHAR(255) NOT NULL,
                    `role` VARCHAR(20) NOT NULL DEFAULT 'USER',
                    `password_changed_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    `is_first_login` TINYINT(1) NOT NULL DEFAULT 1,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # Ensure role column exists if table existed previously without it
            try:
                cursor.execute("ALTER TABLE `users` ADD COLUMN `role` VARCHAR(20) NOT NULL DEFAULT 'USER' AFTER `password_hash`;")
            except Exception:
                pass

            # Ensure branch column exists for branch assignment
            try:
                cursor.execute("ALTER TABLE `users` ADD COLUMN `branch` VARCHAR(100) NULL DEFAULT NULL AFTER `role`;")
            except Exception:
                pass

            # Ensure password_changed_at column exists if table existed previously without it
            try:
                cursor.execute("ALTER TABLE `users` ADD COLUMN `password_changed_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER `role`;")
            except Exception:
                pass

            # Ensure is_first_login column exists
            try:
                cursor.execute("ALTER TABLE `users` ADD COLUMN `is_first_login` TINYINT(1) NOT NULL DEFAULT 1 AFTER `password_changed_at`;")
            except Exception:
                pass

            # Set default password_changed_at for any records where it is NULL
            try:
                cursor.execute("UPDATE `users` SET `password_changed_at` = `created_at` WHERE `password_changed_at` IS NULL;")
            except Exception:
                pass

            # Inspections / Items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `inspections` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `item_code` VARCHAR(50) NOT NULL,
                    `item_name` VARCHAR(255) NOT NULL,
                    `category` VARCHAR(100) NOT NULL,
                    `quantity` INT NOT NULL DEFAULT 1,
                    `submitted_by` VARCHAR(50) NOT NULL,
                    `status` VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                    `inspector_notes` TEXT NULL,
                    `inspected_by` VARCHAR(50) NULL,
                    `inspected_at` TIMESTAMP NULL,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # Morning Audits table (FM-MS-007)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `morning_audits` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `branch` VARCHAR(100) NOT NULL,
                    `audit_date` DATE NOT NULL,
                    `submitted_by` VARCHAR(50) NOT NULL,
                    `total_items` INT NOT NULL DEFAULT 36,
                    `passed_items` INT NOT NULL DEFAULT 0,
                    `failed_items` INT NOT NULL DEFAULT 0,
                    `material_room_note` TEXT NULL,
                    `audit_data` LONGTEXT NOT NULL,
                    `ai_analysis` LONGTEXT NULL,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # Ensure ai_analysis column exists if table existed previously without it
            try:
                cursor.execute("ALTER TABLE `morning_audits` ADD COLUMN `ai_analysis` LONGTEXT NULL AFTER `audit_data`;")
            except Exception:
                pass

            # Ensure verification and AI staff analysis columns exist in morning_audits
            for col_sql in [
                "ALTER TABLE `morning_audits` ADD COLUMN `is_verified` TINYINT(1) NOT NULL DEFAULT 0;",
                "ALTER TABLE `morning_audits` ADD COLUMN `headcount_checked` TINYINT(1) NOT NULL DEFAULT 0;",
                "ALTER TABLE `morning_audits` ADD COLUMN `dress_code_checked` TINYINT(1) NOT NULL DEFAULT 0;",
                "ALTER TABLE `morning_audits` ADD COLUMN `verified_by` VARCHAR(50) NULL;",
                "ALTER TABLE `morning_audits` ADD COLUMN `verified_at` TIMESTAMP NULL;",
                "ALTER TABLE `morning_audits` ADD COLUMN `ai_staff_analysis` LONGTEXT NULL;"
            ]:
                try:
                    cursor.execute(col_sql)
                except Exception:
                    pass

            # Daily Operation Reports table (FM-MS-224)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `daily_operation_reports` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `branch` VARCHAR(100) NOT NULL,
                    `team` VARCHAR(100) NULL,
                    `report_date` DATE NOT NULL,
                    `submitted_by` VARCHAR(50) NOT NULL,
                    `morning_brief` LONGTEXT NULL,
                    `daily_summary` LONGTEXT NULL,
                    `additional_tasks` TEXT NULL,
                    `manpower_data` LONGTEXT NULL,
                    `customer_stats` LONGTEXT NULL,
                    `team_staff` LONGTEXT NULL,
                    `report_photos` LONGTEXT NULL,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # Ensure report_photos column exists if table existed previously without it
            try:
                cursor.execute("ALTER TABLE `daily_operation_reports` ADD COLUMN `report_photos` LONGTEXT NULL AFTER `team_staff`;")
            except Exception:
                pass

            # Ensure verification and AI staff analysis columns exist in daily_operation_reports
            for col_sql in [
                "ALTER TABLE `daily_operation_reports` ADD COLUMN `is_verified` TINYINT(1) NOT NULL DEFAULT 0;",
                "ALTER TABLE `daily_operation_reports` ADD COLUMN `headcount_checked` TINYINT(1) NOT NULL DEFAULT 0;",
                "ALTER TABLE `daily_operation_reports` ADD COLUMN `dress_code_checked` TINYINT(1) NOT NULL DEFAULT 0;",
                "ALTER TABLE `daily_operation_reports` ADD COLUMN `verified_by` VARCHAR(50) NULL;",
                "ALTER TABLE `daily_operation_reports` ADD COLUMN `verified_at` TIMESTAMP NULL;",
                "ALTER TABLE `daily_operation_reports` ADD COLUMN `ai_staff_analysis` LONGTEXT NULL;"
            ]:
                try:
                    cursor.execute(col_sql)
                except Exception:
                    pass

            # Maid Work Schedules table (ตารางการทำงานแม่บ้าน สำนักงานขายประจำวัน / ประจำสัปดาห์)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `maid_schedules` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `branch` VARCHAR(100) NOT NULL,
                    `month_year` VARCHAR(7) NOT NULL,
                    `submitted_by` VARCHAR(50) NOT NULL,
                    `data_json` LONGTEXT NOT NULL,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY `uq_branch_month` (`branch`, `month_year`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # Branches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `branches` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `name` VARCHAR(100) NOT NULL UNIQUE,
                    `is_active` TINYINT(1) DEFAULT 1,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # Branches table is created clean without hardcoded branches, ready for new entries via Admin menu
            # (No initial branches seeded)

            # Seed default 3-letter uppercase accounts with initial default password Test*123
            default_init_hash = generate_password_hash("Test*123")

            # Default ADM (Role: ADMIN, Default Password: Test*123, is_first_login: 1)
            cursor.execute("SELECT id, role, is_first_login FROM users WHERE username = %s", ("ADM",))
            adm_user = cursor.fetchone()
            if not adm_user:
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, password_changed_at, is_first_login) VALUES (%s, %s, %s, NOW(), 1)",
                    ("ADM", default_init_hash, "ADMIN")
                )
                print("[DB INIT] Created default admin user: ADM (Role: ADMIN, Initial Password: Test*123)")
            else:
                # Update to ensure role and password can be used with Test*123
                cursor.execute("UPDATE users SET password_hash = %s, role = 'ADMIN', is_first_login = 1 WHERE username = 'ADM'", (default_init_hash,))

            # Default USR (Role: USER, Default Password: Test*123, is_first_login: 1)
            cursor.execute("SELECT id FROM users WHERE username = %s", ("USR",))
            usr_user = cursor.fetchone()
            if not usr_user:
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, password_changed_at, is_first_login) VALUES (%s, %s, %s, NOW(), 1)",
                    ("USR", default_init_hash, "USER")
                )
                print("[DB INIT] Created default user: USR (Role: USER, Initial Password: Test*123)")
            else:
                cursor.execute("UPDATE users SET password_hash = %s, role = 'USER', is_first_login = 1 WHERE username = 'USR'", (default_init_hash,))

            # Sample demo data is not auto-inserted to preserve clean state after clearing history

        db_conn.close()
        print(f"[DB INIT] Successfully initialized database '{DB_NAME}' with role, expiration tracking, and inspection structures.")
        return True, "Database initialized successfully"
    except Exception as e:
        print(f"[DB INIT ERROR] Could not initialize database: {e}")
        return False, str(e)

def clear_all_report_data():
    """Truncate morning_audits, daily_operation_reports, maid_schedules, and inspections tables and clear uploaded files."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE morning_audits;")
            cursor.execute("TRUNCATE TABLE daily_operation_reports;")
            cursor.execute("TRUNCATE TABLE maid_schedules;")
            cursor.execute("TRUNCATE TABLE inspections;")
        conn.close()
        
        # Clear uploaded photo files on disk
        import glob
        upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'daily_reports')
        if os.path.exists(upload_dir):
            for f in glob.glob(os.path.join(upload_dir, '*')):
                try:
                    if os.path.isfile(f):
                        os.remove(f)
                except Exception:
                    pass
        print("[DB CLEANUP] Cleared all morning_audits, daily_operation_reports, maid_schedules, and inspections records and uploaded photo files.")
        return True, "ล้างข้อมูลประวัติและรูปภาพทั้งหมดเรียบร้อยแล้ว"
    except Exception as e:
        print(f"[DB CLEANUP ERROR] Could not clear report data: {e}")
        return False, str(e)
