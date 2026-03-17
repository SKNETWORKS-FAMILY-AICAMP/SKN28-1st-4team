USE `app_db`;

CREATE TABLE IF NOT EXISTS `vehicle_model_image` (
    `brand_key` VARCHAR(50) NOT NULL,
    `model_name` VARCHAR(255) NOT NULL,
    `source_filename` VARCHAR(255) NOT NULL,
    `mime_type` VARCHAR(50) NOT NULL DEFAULT 'image/jpeg',
    `image_blob` MEDIUMBLOB NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`brand_key`, `model_name`)
) ENGINE=InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;
