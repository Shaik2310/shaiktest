import boto3

# Replace with your desired bucket name and region
bucket_name = 'shaik-test-code1'
region = 'us-east-1'  # Change if needed

# Create an S3 client
s3_client = boto3.client('s3', region_name=region)

try:
    # Create the S3 bucket
    response = s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={
            'LocationConstraint': region
        }
    )
    print(f"Bucket '{bucket_name}' created successfully!")
except s3_client.exceptions.BucketAlreadyOwnedByYou:
    print(f"Bucket '{bucket_name}' already exists and is owned by you.")
except s3_client.exceptions.BucketAlreadyExists:
    print(f"Bucket name '{bucket_name}' is already taken.")
except Exception as e:
    print(f"Error: {e}")

    #changes need update 
    # if i have changes 