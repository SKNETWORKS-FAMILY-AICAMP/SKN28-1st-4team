SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `app_db`;

SELECT COUNT(*) AS `total_image_rows`
FROM `vehicle_model_image`;

SELECT
    `brand_key`,
    COUNT(*) AS `image_rows`
FROM `vehicle_model_image`
GROUP BY `brand_key`
ORDER BY `brand_key`;
