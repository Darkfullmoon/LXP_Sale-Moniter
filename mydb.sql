-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: mysql:3306
-- Generation Time: Sep 18, 2026 at 08:51 AM
-- Server version: 8.4.11
-- PHP Version: 8.3.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `mydb`
--

-- --------------------------------------------------------

--
-- Table structure for table `branches`
--

CREATE TABLE `branches` (
  `id` int NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `branches`
-- (Empty - ready for new branch entries)


-- --------------------------------------------------------

--
-- Table structure for table `daily_operation_reports`
--

CREATE TABLE `daily_operation_reports` (
  `id` int NOT NULL,
  `branch` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `team` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `report_date` date NOT NULL,
  `submitted_by` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `morning_brief` longtext COLLATE utf8mb4_unicode_ci,
  `daily_summary` longtext COLLATE utf8mb4_unicode_ci,
  `additional_tasks` text COLLATE utf8mb4_unicode_ci,
  `manpower_data` longtext COLLATE utf8mb4_unicode_ci,
  `customer_stats` longtext COLLATE utf8mb4_unicode_ci,
  `team_staff` longtext COLLATE utf8mb4_unicode_ci,
  `report_photos` longtext COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_verified` tinyint(1) NOT NULL DEFAULT '0',
  `headcount_checked` tinyint(1) NOT NULL DEFAULT '0',
  `dress_code_checked` tinyint(1) NOT NULL DEFAULT '0',
  `verified_by` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `verified_at` timestamp NULL DEFAULT NULL,
  `ai_staff_analysis` longtext COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `inspections`
--

CREATE TABLE `inspections` (
  `id` int NOT NULL,
  `item_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `quantity` int NOT NULL DEFAULT '1',
  `submitted_by` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING',
  `inspector_notes` text COLLATE utf8mb4_unicode_ci,
  `inspected_by` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `inspected_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `maid_schedules`
--

CREATE TABLE `maid_schedules` (
  `id` int NOT NULL,
  `branch` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `month_year` varchar(7) COLLATE utf8mb4_unicode_ci NOT NULL,
  `submitted_by` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `data_json` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `morning_audits`
--

CREATE TABLE `morning_audits` (
  `id` int NOT NULL,
  `branch` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `audit_date` date NOT NULL,
  `submitted_by` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `total_items` int NOT NULL DEFAULT '36',
  `passed_items` int NOT NULL DEFAULT '0',
  `failed_items` int NOT NULL DEFAULT '0',
  `material_room_note` text COLLATE utf8mb4_unicode_ci,
  `audit_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `ai_analysis` longtext COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_verified` tinyint(1) NOT NULL DEFAULT '0',
  `headcount_checked` tinyint(1) NOT NULL DEFAULT '0',
  `dress_code_checked` tinyint(1) NOT NULL DEFAULT '0',
  `verified_by` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `verified_at` timestamp NULL DEFAULT NULL,
  `ai_staff_analysis` longtext COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'USER',
  `branch` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password_changed_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_first_login` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `password_hash`, `role`, `branch`, `password_changed_at`, `is_first_login`, `created_at`) VALUES
(1, 'ADMIN', 'scrypt:32768:8:1$wmQwBkVAU3e2ILzj$f6aa764d8a06aabbe10b611a893bccef59de85a625595583428f2f7e923cb9639da796f1a59bc295933c0f6cefbdd5f528d3e17497b97d6e5fdc5eeac595af66', 'ADMIN', NULL, '2026-08-19 08:23:45', 0, '2026-08-17 06:24:48'),
(2, 'STAFF', 'scrypt:32768:8:1$HBc2eLeQxr8p3PGh$b6627e62b1a5849dd4bc375b13b79ce19898136f6c53d9e0f2e92282c853bd459dcaf2522a89b487940b0b4e1103970a9c0f4a4aea7f6a243be185a101949af5', 'USER', NULL, '2026-08-19 04:34:07', 1, '2026-08-17 07:02:57'),
(3, 'USER', 'scrypt:32768:8:1$iC7xJXGHxmGR6ejS$ab587d585ece04ad26ea8245452cdbf2b3774407b3c38fa733bf24d1c87a4622f940e0c89e63cb4f66bc39d726c69b0377e0ce60bdebb49ce5ba2fb5cd0d45b4', 'USER', NULL, '2026-08-19 04:34:07', 1, '2026-08-17 07:03:54'),
(4, 'ADM', 'scrypt:32768:8:1$3xc6VjYrxGMaoOIs$a154d433ddd8be42f80a0dd0407105d92b79ebd7c2158f2dcfd087b035ac8e0268676fc70c8d7a21109c4f0446471981c76a95d4676a4c3e7395d2bc9d925647', 'ADMIN', NULL, '2026-08-19 08:23:45', 1, '2026-08-19 04:34:07'),
(5, 'USR', 'scrypt:32768:8:1$3xc6VjYrxGMaoOIs$a154d433ddd8be42f80a0dd0407105d92b79ebd7c2158f2dcfd087b035ac8e0268676fc70c8d7a21109c4f0446471981c76a95d4676a4c3e7395d2bc9d925647', 'USER', NULL, '2026-08-19 06:53:49', 1, '2026-08-19 04:34:07'),
(6, 'manager_sales', 'scrypt:32768:8:1$wmQwBkVAU3e2ILzj$f6aa764d8a06aabbe10b611a893bccef59de85a625595583428f2f7e923cb9639da796f1a59bc295933c0f6cefbdd5f528d3e17497b97d6e5fdc5eeac595af66', 'ADMIN', NULL, '2026-08-19 08:23:45', 0, '2026-08-19 06:56:27'),
(7, 'KNG', 'scrypt:32768:8:1$KPvyMdTPZUJzjXyc$fff7243f49e6231218221b931bf7a417c8d7291b981c19b8337715c3172bf2845254165e126ec53cf48f7ac9170c0d6e104c87fa5ac066fb0f2f93ac92c0dc59', 'USER', NULL, '2026-08-19 07:01:10', 1, '2026-08-19 07:01:09'),
(8, 'KOL', 'scrypt:32768:8:1$yQ8v4pS5wZENMMNw$324823494c737fb74ad676bcda6ef4cf20240e8db0a32dcb5f1c64842402700c26aa3c5062fcd5a1e5458f3c9c96486ee9b08f365d0bf4b52d58ef1bf76425d7', 'USER', NULL, '2026-08-19 07:09:17', 0, '2026-08-19 07:02:46'),
(9, 'UIO', 'scrypt:32768:8:1$DUWr6GrjLqJrpJsg$c5a87c94e9e68da68ec77f74c8f755b678e163e4a5bc27fb9937aabbf025c3434646ddc37f3bf2561b45174a2d52c0d4846d83cda58eab77521b99df92173175', 'USER', NULL, '2026-09-18 08:35:51', 0, '2026-08-19 07:27:03'),
(10, 'USE', 'scrypt:32768:8:1$Z3f8ZmAzZH1TnJBr$994b53e008b2a13d6afef0f8b87d7af5f0cce04bde3fa10a5954f65375ba23497e6d7e7f14815da3f15c74092a5d8bf848d5f0db118d054a8e811af08f50cc39', 'USER', NULL, '2026-09-01 02:48:01', 1, '2026-09-01 02:48:01');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `branches`
--
ALTER TABLE `branches`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `daily_operation_reports`
--
ALTER TABLE `daily_operation_reports`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `inspections`
--
ALTER TABLE `inspections`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `maid_schedules`
--
ALTER TABLE `maid_schedules`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_branch_month` (`branch`,`month_year`);

--
-- Indexes for table `morning_audits`
--
ALTER TABLE `morning_audits`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `branches`
--
ALTER TABLE `branches`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `daily_operation_reports`
--
ALTER TABLE `daily_operation_reports`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `inspections`
--
ALTER TABLE `inspections`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `maid_schedules`
--
ALTER TABLE `maid_schedules`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `morning_audits`
--
ALTER TABLE `morning_audits`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
