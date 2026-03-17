SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `app_db`;

SET @brand_key = 'hyundai';
SET @model_name = '쏘나타 디 엣지';

SELECT
    `brand_key`,
    `model_name`,
    `source_filename`,
    `mime_type`,
    `image_blob`
FROM `vehicle_model_image`
WHERE BINARY `brand_key` = BINARY @brand_key
  AND BINARY `model_name` = BINARY @model_name;
