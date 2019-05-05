from __future__ import print_function
import os
import sys
import boto3
from botocore.client import Config
import logger
from boto3.s3.transfer import TransferConfig
import threading
import time
import socket

# Log file
LOG = logger.getLogFile(__name__)

class uploadVideoDO:
	def __init__(self, clientId):
		self.clientId = clientId
		self.alreadyUploadedList = []
		self.uploadRetryCount = 5
		self.TEST_REMOTE_SERVER = "www.google.com"
		self.internetCheckTimeout = 10*60 # 30 mins

	def getUploadClient(self, dokey, dokeysecret):
		session = boto3.session.Session()
		client = session.client('s3',
                        region_name='sgp1',
                        endpoint_url='https://sgp1.digitaloceanspaces.com',
                        aws_access_key_id=dokey,
                        aws_secret_access_key=dokeysecret)
		return client

	def checkInternetConnection(self):
		try:
			# see if we can resolve the host name -- tells us if there is
			# a DNS listening
			host = socket.gethostbyname(self.TEST_REMOTE_SERVER)
			# connect to the host -- tells us if the host is actually
			# reachable
			s = socket.create_connection((host, 80), 2)
			return True
		except:
			pass
			
		return False

	def uploadOriginalVideo(self, bucketname, dokey, dokeysecret, originalFile, videoKey):
		LOG.info ("Uploading original file to CDN: "+str(originalFile))
		client = self.getUploadClient(dokey, dokeysecret)
		file = videoKey + '/' + os.path.basename(originalFile)
		try:
			config = TransferConfig(multipart_threshold=1024 * 25, max_concurrency=10, multipart_chunksize=1024 * 25, use_threads=True)
			client.upload_file(originalFile, bucketname, file,ExtraArgs={'ACL':'public-read'}, Config=config)
		except Exception as ex:
			LOG.error("Exception in uploading the original file: " + str(ex) + ' file name: ' + str(file))
			retryCount = 0
			while retryCount < self.uploadRetryCount:
				LOG.info ("Retrying the upload: " + str(file))
				try:
					config = TransferConfig(multipart_threshold=1024 * 25, max_concurrency=10, multipart_chunksize=1024 * 25, use_threads=True)
					client.upload_file(originalFile, bucketname, file,ExtraArgs={'ACL':'public-read'}, Config=config)
					LOG.info ("Uploading success for the original file: " + str(file))
					break
				except Exception as ex:
					LOG.error("Exception in uploading the original file: " + str(ex) + ' file name: ' + str(file))
					retryCount += 1
					if retryCount < self.uploadRetryCount:
						internetCheckWait = 5
						loopCount = self.internetCheckTimeout/internetCheckWait
						status = self.checkInternetConnection()
						while loopCount > 0 and status == False:
							LOG.info("Waiting for internet connection")
							time.sleep(internetCheckWait) 
							loopCount = loopCount - 1
							status = self.checkInternetConnection()


						LOG.info("Internet conectivity status: " + str(status))


	def uploadVideoDO(self, local_folder_path, bucketname, dokey, dokeysecret):
		# Initialize a session using DigitalOcean Spaces.
		LOG.info ("Uploading mpd folder to CDN: "+str(local_folder_path))
		client = self.getUploadClient(dokey, dokeysecret)
		parentFolder = os.path.dirname(local_folder_path)
		for root, dirs, files in os.walk(local_folder_path):
			nested_dir = root.replace(parentFolder, '')
			if nested_dir:
				nested_dir = nested_dir.replace('/','',1) + '/'
			nested_dir = nested_dir.replace('\\','/')
			if nested_dir.startswith('/'):
				nested_dir = nested_dir[1:]
			for file in files:
				try:
					complete_file_path = os.path.join(root, file)
					if complete_file_path in self.alreadyUploadedList:
						continue

					file = nested_dir + file if nested_dir else file
					#print ("[S3_UPLOAD] Going to upload {complete_file_path} to s3 bucket {s3_bucket} as {file}"\
					#    .format(complete_file_path=complete_file_path, s3_bucket=bucketname, file=file))
					client.upload_file(complete_file_path, bucketname, file,ExtraArgs={'ACL':'public-read','CacheControl':'max-age=3600'})
					self.alreadyUploadedList.append(complete_file_path)
				except Exception as ex:
					LOG.error("Exception in uploading the file: " + str(ex) + ' file name: ' + str(file))
					retryCount = 0
					while retryCount < self.uploadRetryCount:
						LOG.info ("Retrying the upload: " + str(file))
						try:
							client.upload_file(complete_file_path, bucketname, file,ExtraArgs={'ACL':'public-read'})
							self.alreadyUploadedList.append(complete_file_path)
							LOG.info ("Uploading success for file: " + str(file))
							break
						except Exception as ex:
							LOG.error("Exception in uploading the file: " + str(ex) + ' file name: ' + str(file))
							retryCount += 1
							if retryCount < self.uploadRetryCount:
								internetCheckWait = 5
								loopCount = self.internetCheckTimeout/internetCheckWait
								status = self.checkInternetConnection()
								while loopCount > 0 and status == False:
									LOG.info("Waiting for internet connection")
									time.sleep(internetCheckWait) 
									loopCount = loopCount - 1
									status = self.checkInternetConnection()


								LOG.info("Internet conectivity status: " + str(status))