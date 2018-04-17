import boto3
import iamwrapper

class s3wrapper:
    location = 'ap-south-1'

    def __init__(self, iamwrapper):
        self.client = boto3.resource('s3', aws_access_key_id = iamwrapper.accesskeyid, aws_secret_access_key = iamwrapper.secretkey)

    def createbucket(bucketname):
        try:
            results = self.client.create_bucket(Bucket = bucketname, CreateBucketConfiguration = {'LocationConstraint' : self.location})
            return results
        except:
            return None

    def listbucket():
        return self.client.list_buckets()

    def deletebucket(bucketname):
        self.client.delete_bucket(Bucket = bucketname)

