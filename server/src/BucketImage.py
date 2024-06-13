import hashlib
import boto3
from src.Config import Config

class BucketImage:
    BUCKET_NAME = "vphotoframe"

    def __init__(self, c: Config):
        self.s3 = boto3.client(
            service_name ="s3",
            endpoint_url = c.get("endpoint"),
            aws_access_key_id = c.get("access_key_id"),
            aws_secret_access_key = c.get("secret_access_key"),
            region_name="auto")
        self.SEED = c.get("seed", "HOGE")
    
    def get_workdir(self, key, worksheet) -> str:
        s = (key + self.SEED + worksheet).encode("utf-8")
        return hashlib.md5(s).hexdigest()

    def upload(self, key, worksheet, id, bytes) -> str:
        workdir = self.get_workdir(key, worksheet)
        path = f"images/{workdir}/{id}"
        self.s3.upload_fileobj(bytes, self.BUCKET_NAME, path)
        return workdir

    def delete(self, key, worksheet, id):
        workdir = self.get_workdir(key, worksheet)
        path = f"images/{workdir}/{id}"
        self.s3.delete_object(self.BUCKET_NAME, path)
