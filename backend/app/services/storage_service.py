"""
S3/MinIO storage service
"""
import boto3
from botocore.exceptions import ClientError
from io import BytesIO
from pathlib import Path
import uuid

from app.core.config import settings


class StorageService:
    """Service for managing file storage in S3/MinIO"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION
        )
        self.bucket = settings.S3_BUCKET
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create the bucket if it doesn't already exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.s3_client.create_bucket(Bucket=self.bucket)
    
    async def upload_receipt_image(self, file_content: bytes, filename: str, user_id: str, content_type: str = None) -> tuple[str, str]:
        """
        Upload receipt image to S3
        Returns: (storage_path, thumbnail_path)
        """
        # Generate unique filename
        file_ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{file_ext}"
        
        # Create storage path
        storage_path = f"receipts/{user_id}/{unique_name}"
        
        # Upload original file
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=storage_path,
            Body=file_content,
            ContentType=content_type or self._get_mime_type(filename)
        )
        
        # TODO: Generate and upload thumbnail
        # For now, just return same path
        thumbnail_path = storage_path
        
        return storage_path, thumbnail_path
    
    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Get signed URL for accessing file"""
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': storage_path},
            ExpiresIn=expires_in
        )
    
    def delete_receipt_images(self, storage_paths: list[str]):
        """Delete receipt images from storage"""
        if not storage_paths:
            return
        
        delete_objects = [{'Key': path} for path in storage_paths]
        self.s3_client.delete_objects(
            Bucket=self.bucket,
            Delete={'Objects': delete_objects}
        )
    
    @staticmethod
    def _get_mime_type(filename: str) -> str:
        """Get MIME type from filename"""
        ext = Path(filename).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.heic': 'image/heic',
            '.pdf': 'application/pdf'
        }
        return mime_types.get(ext, 'application/octet-stream')
