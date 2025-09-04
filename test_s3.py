import boto3
import os
from botocore.exceptions import ClientError
from django.contrib.staticfiles.storage import staticfiles_storage

# Set up AWS credentials
# Replace these with your actual credentials or set environment variables
# aws_access_key = input("Enter AWS Access Key: ")
# aws_secret_key = input("Enter AWS Secret Key: ")
# bucket_name = input("Enter S3 Bucket Name (default: logo-replacement-saas-bucket): ") or "logo-replacement-saas-bucket"
# region_name = input("Enter AWS Region (default: us-east-1): ") or "us-east-1"

aws_access_key = "AKIAQ3CUC44HCIIW4UC4"
aws_secret_key = "8l4sYfzgrXcebJF+XpPDcR1M40wWdWDqQSrPl0dd"
bucket_name = "logo-replacement-assets"
region_name = "eu-central-1"

# Create S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region_name
)

print("\nTesting S3 connection...")

# Test 1: List buckets
try:
    response = s3.list_buckets()
    print(f"SUCCESS: Connected to AWS S3. Available buckets:")
    for bucket in response['Buckets']:
        print(f"  - {bucket['Name']}")
except ClientError as e:
    print(f"ERROR: Could not list buckets: {e}")

# Test 2: Check if bucket exists
try:
    s3.head_bucket(Bucket=bucket_name)
    print(f"\nSUCCESS: Bucket '{bucket_name}' exists")
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == '404':
        print(f"\nERROR: Bucket '{bucket_name}' does not exist")
    elif error_code == '403':
        print(f"\nERROR: Access denied to bucket '{bucket_name}'. Check permissions")
    else:
        print(f"\nERROR: Error checking bucket: {e}")

# Test 3: Check if we can upload a file
test_file_name = "test_file.txt"
with open(test_file_name, "w") as f:
    f.write("This is a test file for S3 upload")

try:
    s3.upload_file(
        test_file_name,
        bucket_name,
        "static/test_file.txt"
    )
    print(f"\nSUCCESS: Test file uploaded to static/test_file.txt")
except ClientError as e:
    print(f"\nERROR: Could not upload public file: {e}")

try:
    s3.upload_file(
        test_file_name,
        bucket_name,
        "media/test_file.txt"
    )
    print(f"SUCCESS: Test file uploaded to media/test_file.txt")
except ClientError as e:
    print(f"ERROR: Could not upload private file: {e}")

# Test 4: Check bucket policy and ACLs
try:
    policy = s3.get_bucket_policy(Bucket=bucket_name)
    print(f"\nSUCCESS: Bucket has a policy: {policy['Policy']}")
except ClientError as e:
    if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
        print(f"\nWARNING: Bucket '{bucket_name}' has no policy defined")
    else:
        print(f"\nERROR: Could not retrieve bucket policy: {e}")

# Test 5: Check if Block Public Access settings are enabled
try:
    bpa = s3.get_public_access_block(Bucket=bucket_name)
    print("\nBlock Public Access settings:")
    for setting, value in bpa['PublicAccessBlockConfiguration'].items():
        print(f"  - {setting}: {value}")
    
    if bpa['PublicAccessBlockConfiguration'].get('BlockPublicAcls', False):
        print("\nWARNING: BlockPublicAcls is enabled, which may prevent public-read ACLs")
    if bpa['PublicAccessBlockConfiguration'].get('BlockPublicPolicy', False):
        print("WARNING: BlockPublicPolicy is enabled, which may prevent public bucket policies")
except ClientError as e:
    print(f"\nNOTE: Could not retrieve Block Public Access settings: {e}")

# Clean up
os.remove(test_file_name)
print("\nTest completed") 