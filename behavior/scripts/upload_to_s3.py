#!/usr/bin/env python3
"""
Upload fine-tuned Granite model to MinIO S3 on OpenShift.
Uses the Data Connection credentials from RHOAI.
"""

import os
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
import sys
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(InsecureRequestWarning)

# S3/MinIO Configuration from RHOAI Data Connection
S3_ENDPOINT = "https://minio-s3-white-hat.apps.cluster-xdhbp.xdhbp.sandbox1403.opentlc.com"
S3_ACCESS_KEY = "MTACUex9XotZ2PBj"
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")  # Set as environment variable
BUCKET_NAME = "my-storage"
REGION = "us-east-1"

def create_s3_client():
    """Create S3 client with MinIO endpoint."""
    if not S3_SECRET_KEY:
        print("❌ Error: S3_SECRET_KEY environment variable not set")
        print("\nTo set it, run:")
        print('export S3_SECRET_KEY="your-secret-key-here"')
        sys.exit(1)
    
    return boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=REGION,
        verify=False  # Disable SSL verification for self-signed certs
    )

def upload_directory(s3_client, local_path, s3_prefix):
    """Upload entire directory to S3."""
    local_path = Path(local_path)
    
    if not local_path.exists():
        print(f"❌ Error: Path not found: {local_path}")
        sys.exit(1)
    
    print(f"\n📦 Uploading model from: {local_path}")
    print(f"📍 Destination: s3://{BUCKET_NAME}/{s3_prefix}/")
    print("-" * 70)
    
    files_uploaded = 0
    total_size = 0
    
    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(local_path)
            s3_key = f"{s3_prefix}/{relative_path}".replace('\\', '/')
            
            file_size = file_path.stat().st_size
            total_size += file_size
            
            size_mb = file_size / 1024 / 1024
            print(f"⬆️  {relative_path:60s} {size_mb:>8.2f} MB")
            
            try:
                s3_client.upload_file(
                    str(file_path),
                    BUCKET_NAME,
                    s3_key
                )
                files_uploaded += 1
            except ClientError as e:
                print(f"❌ Error uploading {relative_path}: {e}")
                return False
    
    print("-" * 70)
    print(f"✅ Successfully uploaded {files_uploaded} files")
    print(f"📊 Total size: {total_size / 1024 / 1024:.2f} MB")
    print(f"\n📍 Model location: s3://{BUCKET_NAME}/{s3_prefix}/")
    
    return True

def list_uploaded_files(s3_client, s3_prefix):
    """List files in S3 to verify upload."""
    print(f"\n📋 Verifying uploaded files in s3://{BUCKET_NAME}/{s3_prefix}/")
    print("-" * 70)
    
    try:
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=s3_prefix
        )
        
        if 'Contents' in response:
            for obj in response['Contents']:
                size_mb = obj['Size'] / 1024 / 1024
                print(f"  {obj['Key']:60s} {size_mb:>8.2f} MB")
            print(f"\nTotal files: {len(response['Contents'])}")
        else:
            print("  (no files found)")
            
    except ClientError as e:
        print(f"❌ Error listing files: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Upload fine-tuned Granite model to MinIO S3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  export S3_SECRET_KEY="your-secret-key"
  python upload_to_s3.py --model-path models/granite-multitask-finetuned
  
Environment variables:
  S3_SECRET_KEY    Required. Your S3 secret access key.
        """
    )
    
    parser.add_argument(
        '--model-path',
        default='models/granite-multitask-finetuned',
        help='Path to fine-tuned model directory (default: models/granite-multitask-finetuned)'
    )
    parser.add_argument(
        '--prefix',
        default='granite-multitask-finetuned',
        help='S3 prefix/folder name (default: granite-multitask-finetuned)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify upload by listing files after upload'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 GRANITE MODEL UPLOAD TO MINIO S3")
    print("=" * 70)
    print(f"Endpoint:     {S3_ENDPOINT}")
    print(f"Bucket:       {BUCKET_NAME}")
    print(f"Prefix:       {args.prefix}")
    print(f"Local path:   {args.model_path}")
    print("=" * 70)
    
    # Create S3 client
    print("\n🔗 Connecting to MinIO...")
    s3_client = create_s3_client()
    print("✅ Connected successfully")
    
    # Upload model
    success = upload_directory(s3_client, args.model_path, args.prefix)
    
    if not success:
        sys.exit(1)
    
    # Verify upload if requested
    if args.verify:
        list_uploaded_files(s3_client, args.prefix)
    
    print("\n" + "=" * 70)
    print("✅ UPLOAD COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Create InferenceService in RHOAI")
    print("2. Point storage.path to:", args.prefix)
    print("3. Deploy with vLLM runtime")
    print("=" * 70)

if __name__ == "__main__":
    main()
