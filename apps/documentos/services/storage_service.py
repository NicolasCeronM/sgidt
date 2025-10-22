# apps/documentos/services/storage_service.py
def make_presigned_url(user, filename, content_type):
    """
    Genera datos para URL firmada (S3/MinIO). Implementa con boto3/minio cuando quieras.
    """
    object_key = f"uploads/{user.id}/{filename}"
    upload_url = "https://presigned-url-pendiente"  # TODO: reemplazar
    return {"upload_url": upload_url, "object_key": object_key, "finalize_url": "/api/v1/documentos/"}
