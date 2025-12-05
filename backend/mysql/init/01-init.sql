-- Initial database setup (runs once on first container startup)
-- Database and user are created via environment variables in docker-compose.dev.yml
-- This file configures the database character set

USE server_dashboard_dev;

-- Set default character set
ALTER DATABASE server_dashboard_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
