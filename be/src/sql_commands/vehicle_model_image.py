SELECT_VEHICLE_MODEL_IMAGE_SQL = """
SELECT
    `brand_key`,
    `model_name`,
    `source_filename`,
    `mime_type`,
    `image_blob`
FROM `vehicle_model_image`
WHERE BINARY `brand_key` = BINARY %s
  AND BINARY `model_name` = BINARY %s
LIMIT 1
""".strip()
