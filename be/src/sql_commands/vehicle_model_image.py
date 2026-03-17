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


def build_select_vehicle_model_image_meta_by_models_sql(model_count: int) -> str:
    if model_count <= 0:
        raise ValueError("model_count must be positive")
    placeholders = ", ".join(["%s"] * model_count)
    return f"""
SELECT
    `brand_key`,
    `model_name`,
    `source_filename`,
    `mime_type`
FROM `vehicle_model_image`
WHERE BINARY `brand_key` = BINARY %s
  AND BINARY `model_name` IN ({placeholders})
""".strip()
