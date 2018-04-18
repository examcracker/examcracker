import s3wrapper
import iamwrapper

accesskeyid = 'AKIAJGYWWGWRCJMQYMXQ'
secretkey = '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'

def createbucket(bucketname):
    iamwrapperobj = iamwrapper.iamwrapper(accesskeyid, secretkey)
    s3wrapperobj = s3wrapper.s3wrapper(iamwrapperobj)
    s3wrapperobj.createbucket(bucketname)

def deletebucket(bucketname):
    iamwrapperobj = iamwrapper.iamwrapper(accesskeyid, secretkey)
    s3wrapperobj = s3wrapper.s3wrapper(iamwrapperobj)
    s3wrapperobj.deletebucket(bucketname)


createbucket('testingkushal')
deletebucket('testingkushal')


