import os
import subprocess
import boto3
import datetime
import gzip
from dotenv import load_dotenv

# Load environment variable.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
ENV_PATH = os.path.join(PARENT_DIR, ".env")

# Load .env from the parent directory
load_dotenv(ENV_PATH, override=True)
# Database Credentials
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")


# Backup Directory
BACKUP_DIR = os.path.join(SCRIPT_DIR, "backups")
S3_BUCKET = os.getenv("DB_S3_BUCKET")
S3_FOLDER = "mysql-backups"

# print("=====================> env = ",DB_NAME, DB_PASS, " and env path = ",ENV_PATH)

# Date Format
DATE = datetime.datetime.now().strftime("%Y-%m-%d")
# DATE = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime("%Y-%m-%d")

BACKUP_FILE = os.path.join(BACKUP_DIR, f"{DB_NAME}-{DATE}.sql")
COMPRESSED_FILE = BACKUP_FILE + ".gz"

# Ensure Backup Directory Exists
os.makedirs(BACKUP_DIR, exist_ok=True)

# Perform MySQL Dump
with open(BACKUP_FILE, "w") as f:
    dump_command = ["mysqldump", "-u", DB_USER, f"-p{DB_PASS}", DB_NAME]
    subprocess.run(dump_command, stdout=f, check=True)

# Compress the Backup File Using Python
with open(BACKUP_FILE, "rb") as f_in:
    with gzip.open(COMPRESSED_FILE, "wb") as f_out:
        f_out.writelines(f_in)

# Remove the uncompressed SQL file
os.remove(BACKUP_FILE)

print(f"Backup completed and compressed: {COMPRESSED_FILE}")

# Delete Local Backups Older Than 7 Days
for file in os.listdir(BACKUP_DIR):
    file_path = os.path.join(BACKUP_DIR, file)
    if file.endswith(".gz"):
        file_date_str = file.replace(f"{DB_NAME}-", "").replace(".sql.gz", "")
        try:
            file_date = datetime.datetime.strptime(file_date_str, "%Y-%m-%d")
            if (datetime.datetime.now() - file_date).days > 7:
                os.remove(file_path)
                print(f"Deleted old local backup: {file_path}")
        except ValueError:
            continue  # Ignore files that don't match the date format

# Upload to S3
s3_client = boto3.client(
    "s3", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_DEFAULT_REGION
)
s3_key = f"{S3_FOLDER}/{DB_NAME}-{DATE}.sql.gz"
s3_client.upload_file(COMPRESSED_FILE, S3_BUCKET, s3_key)
print(f"Uploaded to S3: s3://{S3_BUCKET}/{s3_key}")

# Delete Old S3 Backups
response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_FOLDER + "/")
if "Contents" in response:
    for obj in response["Contents"]:
        file_name = obj["Key"].split("/")[-1]
        try:
            file_date_str = file_name.replace(f"{DB_NAME}-", "").replace(".sql.gz", "")
            file_date = datetime.datetime.strptime(file_date_str, "%Y-%m-%d")
            if (datetime.datetime.now() - file_date).days > 7:
                s3_client.delete_object(Bucket=S3_BUCKET, Key=obj["Key"])
                print(f"Deleted old backup from S3: {obj['Key']}")
        except ValueError:
            continue  # Ignore files that don't match the date format