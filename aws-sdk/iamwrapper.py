import boto3

class iamwrapper:
    def __init__(self, accesskeyid, secretkey):
        self.accesskeyid = accesskeyid
        self.secretkey = secretkey

