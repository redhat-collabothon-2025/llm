import os
import argparse
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
import sys

def setup_s3_client(endpoint_url, access_key, secret_key):
    """
    Initialize S3/MinIO client.
    """
    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='us-east-1'  # MinIO doesn't care about region
    )

def create_bucket_if_not_exists(s3_client, bucket_name):
    """
    Create S3 bucket if it doesn't exist.
    """
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✓ Bucket '{bucket_name}' already exists")
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"✓ Created bucket '{bucket_name}'")
        except ClientError as e:
            print(f"✗ Error creating bucket: {e}")
            sys.exit(1)

def upload_directory(s3_client, local_path, bucket_name, s3_prefix):
    """
    Upload entire directory to S3/MinIO.
    """
    local_path = Path(local_path)
    
    if not local_path.exists():
        print(f"✗ Local path does not exist: {local_path}")
        sys.exit(1)
    
    files_uploaded = 0
    total_size = 0
    
    print(f"\nUploading model files from {local_path}...")
    print("-" * 60)
    
    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            # Calculate relative path
            relative_path = file_path.relative_to(local_path)
            s3_key = f"{s3_prefix}/{relative_path}".replace('\\', '/')
            
            # Get file size
            file_size = file_path.stat().st_size
            total_size += file_size
            
            print(f"Uploading: {relative_path} ({file_size / 1024 / 1024:.2f} MB)")
            
            try:
                s3_client.upload_file(
                    str(file_path),
                    bucket_name,
                    s3_key
                )
                files_uploaded += 1
            except ClientError as e:
                print(f"✗ Error uploading {relative_path}: {e}")
    
    print("-" * 60)
    print(f"✓ Uploaded {files_uploaded} files ({total_size / 1024 / 1024:.2f} MB total)")
    
    return files_uploaded

def list_uploaded_files(s3_client, bucket_name, prefix):
    """
    List files in S3 bucket with given prefix.
    """
    print(f"\nFiles in s3://{bucket_name}/{prefix}:")
    print("-" * 60)
    
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"  {obj['Key']} ({obj['Size'] / 1024 / 1024:.2f} MB)")
        else:
            print("  (empty)")
    except ClientError as e:
        print(f"✗ Error listing files: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Upload fine-tuned Granite model to S3/MinIO for RHOAI'
    )
    parser.add_argument(
        '--model-path',
        required=True,
        help='Path to fine-tuned model directory'
    )
    parser.add_argument(
        '--endpoint-url',
        default=os.getenv('S3_ENDPOINT_URL', 'http://minio.example.com:9000'),
        help='S3/MinIO endpoint URL'
    )
    parser.add_argument(
        '--bucket',
        default='rhoai-models',
        help='S3 bucket name'
    )
    parser.add_argument(
        '--prefix',
        default='granite-security-finetuned',
        help='S3 prefix (folder) for model files'
    )
    parser.add_argument(
        '--access-key',
        default=os.getenv('AWS_ACCESS_KEY_ID'),
        help='S3 access key'
    )
    parser.add_argument(
        '--secret-key',
        default=os.getenv('AWS_SECRET_ACCESS_KEY'),
        help='S3 secret key'
    )
    
    args = parser.parse_args()
    
    # Validate credentials
    if not args.access_key or not args.secret_key:
        print("✗ Error: S3 credentials not provided")
        print("  Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        print("  or use --access-key and --secret-key arguments")
        sys.exit(1)
    
    print("="*60)
    print("UPLOAD MODEL TO S3/MinIO FOR RHOAI")
    print("="*60)
    print(f"Endpoint: {args.endpoint_url}")
    print(f"Bucket: {args.bucket}")
    print(f"Prefix: {args.prefix}")
    print(f"Local path: {args.model_path}")
    print("="*60)
    
    # Initialize S3 client
    print("\nConnecting to S3/MinIO...")
    s3_client = setup_s3_client(
        args.endpoint_url,
        args.access_key,
        args.secret_key
    )
    
    # Create bucket if needed
    create_bucket_if_not_exists(s3_client, args.bucket)
    
    # Upload model
    upload_directory(
        s3_client,
        args.model_path,
        args.bucket,
        args.prefix
    )
    
    # Verify upload
    list_uploaded_files(s3_client, args.bucket, args.prefix)
    
    print("\n" + "="*60)
    print("✓ UPLOAD COMPLETE!")
    print("="*60)
    print(f"\nModel location: s3://{args.bucket}/{args.prefix}/")
    print("\nNext steps:")
    print("1. Create Data Connection in RHOAI pointing to this S3 bucket")
    print("2. Deploy InferenceService using the ServingRuntime")
    print("3. Update GenAI app with inference endpoint URL")

if __name__ == "__main__":
    main()