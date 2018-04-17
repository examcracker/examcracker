import s3wrapper
import iamwrapper

accesskeyid = 'AKIAJU7Y7BTWIZD2E4VA'
secretkey = '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'

def createbucket(bucketname):
    iamwrapperobj = iamwrapper(accesskeyid, secretkey)
    s3wrapperobj = s3wrapper(iamwrapperobj)
    s3wrapperobj.createbucket()


createbucket('testingkushal')


