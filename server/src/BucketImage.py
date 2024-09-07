import hashlib
import boto3
from src.Env import Env


env = Env()

class BucketImage:
    BUCKET_NAME = "syncframe"

    def __init__(self):
        self.client = boto3.client(
            service_name ="s3",
            endpoint_url = env.cf_endpoint,
            aws_access_key_id = env.cf_access_key_id,
            aws_secret_access_key = env.cf_secret_access_key,
            region_name="auto")
        self.SEED = env.seed

    def _gen_hash(self, s: str) -> str:
        return hashlib.md5(s.encode("utf-8")).hexdigest()
    
    def get_owner_dir(self, owner) -> str:
        return self._gen_hash(owner + self.SEED)
    def get_key_dir(self, key, worksheet) -> str:
        return self._gen_hash(key + self.SEED + worksheet)
    def get_work_dir(self, owner, key, worksheet) -> str:
        return "/".join([self.get_owner_dir(owner),
                        self.get_key_dir(key, worksheet)])

    def count_owner_objects(self, owner):
        prefix = "images/" + self.get_owner_dir(owner) + "/"
        response = self.client.list_objects_v2(Bucket=self.BUCKET_NAME, Prefix=prefix)
        if 'Contents' not in response:
            return 0
        return len(response['Contents'])
    
    def count_work_objects(self, owner, key, worksheet):
        prefix = "images/" + self.get_work_dir(owner, key, worksheet) + "/"
        response = self.client.list_objects_v2(Bucket=self.BUCKET_NAME, Prefix=prefix)
        if 'Contents' not in response:
            return 0
        return len(response['Contents'])    

    def delete_work_objects(self, owner, key, worksheet):
        prefix = "images/" + self.get_work_dir(owner, key, worksheet) + "/"
        response = self.client.list_objects_v2(Bucket=self.BUCKET_NAME, Prefix=prefix)
        for c in response['Contents']:
            self.client.delete_object(Bucket=self.BUCKET_NAME, Key=c['Key'])
    def delete_object(self, owner, key, worksheet, id):
        workdir = self.get_work_dir(owner, key, worksheet)
        path = f"images/{workdir}/{id}"
        self.client.delete_object(Bucket=self.BUCKET_NAME, Key=path)

    def upload(self, owner, key, worksheet, id, bytes) -> str:
        workdir = self.get_work_dir(owner, key, worksheet)
        path = f"images/{workdir}/{id}"
        self.client.upload_fileobj(Fileobj=bytes, Bucket=self.BUCKET_NAME, Key=path)
        return workdir
