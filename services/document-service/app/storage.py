"""
Storage Service - S3/MinIO/GCS abstraction
Handles file upload, download, and deletion
"""
from typing import Optional
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
import io

load_dotenv()

class StorageService:
    """
    Abstract storage service supporting:
    - MinIO (for local development)
    - AWS S3 (for production)
    - Google Cloud Storage (for production)
    """
    
    def __init__(self):
        self.provider = os.getenv("STORAGE_PROVIDER", "minio").lower()
        
        if self.provider in ["minio", "s3"]:
            # S3-compatible storage (MinIO or AWS S3)
            self.s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv("STORAGE_ENDPOINT"),  # For MinIO
                aws_access_key_id=os.getenv("STORAGE_ACCESS_KEY"),
                aws_secret_access_key=os.getenv("STORAGE_SECRET_KEY"),
                region_name=os.getenv("STORAGE_REGION", "us-east-1")
            )
            self.bucket_name = os.getenv("STORAGE_BUCKET", "analyticaloan-documents")
            
            # Ensure bucket exists
            self._ensure_bucket_exists()
        
        elif self.provider == "gcs":
            # Google Cloud Storage
            from google.cloud import storage
            self.gcs_client = storage.Client()
            self.bucket_name = os.getenv("GCS_BUCKET_NAME", "analyticaloan-documents")
        
        else:
            raise ValueError(f"Unsupported storage provider: {self.provider}")
    
    def _ensure_bucket_exists(self):
        """Ensure S3/MinIO bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            # Bucket doesn't exist, create it
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
            except Exception as e:
                print(f"Warning: Could not create bucket: {e}")
    
    async def upload(
        self, 
        file_content: bytes, 
        storage_path: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload file to storage
        
        Args:
            file_content: File bytes
            storage_path: Path in storage (e.g., "applications/xxx/document.pdf")
            content_type: MIME type
        
        Returns:
            Storage path
        """
        if self.provider in ["minio", "s3"]:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_path,
                Body=file_content,
                ContentType=content_type
            )
        
        elif self.provider == "gcs":
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(storage_path)
            blob.upload_from_string(file_content, content_type=content_type)
        
        return storage_path
    
    async def download(self, storage_path: str) -> bytes:
        """
        Download file from storage
        
        Args:
            storage_path: Path in storage
        
        Returns:
            File bytes
        """
        if self.provider in ["minio", "s3"]:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return response['Body'].read()
        
        elif self.provider == "gcs":
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(storage_path)
            return blob.download_as_bytes()
        
        raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def delete(self, storage_path: str) -> None:
        """
        Delete file from storage
        
        Args:
            storage_path: Path in storage
        """
        if self.provider in ["minio", "s3"]:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
        
        elif self.provider == "gcs":
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(storage_path)
            blob.delete()
    
    async def get_presigned_url(
        self, 
        storage_path: str, 
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for downloading file
        
        Args:
            storage_path: Path in storage
            expiration: URL expiration in seconds (default 1 hour)
        
        Returns:
            Presigned URL
        """
        if self.provider in ["minio", "s3"]:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_path
                },
                ExpiresIn=expiration
            )
            return url
        
        elif self.provider == "gcs":
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(storage_path)
            url = blob.generate_signed_url(expiration=expiration)
            return url
        
        raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def health_check(self) -> bool:
        """
        Check if storage is accessible
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if self.provider in ["minio", "s3"]:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                return True
            
            elif self.provider == "gcs":
                bucket = self.gcs_client.bucket(self.bucket_name)
                bucket.exists()
                return True
            
        except Exception as e:
            print(f"Storage health check failed: {e}")
            return False
        
        return False
