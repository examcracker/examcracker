from __future__ import print_function
import os
import sys
import jwplatform
import requests
import logger

# Log file
LOG = logger.getLogFile(__name__)

class uploadVideo:
	def __init__(self, clientId):
		self.clientId = clientId
		api_key = r'03IfLqqB'
		api_secret = r'AK6y0bBoyEOHASfYwE5xUnWw'
		#api_key = r'avfMTzPK'
		#api_secret = r'k7HIvXAueCNF0G7I8A88Ecor'
		# Setup API client
		self.jwplatform_client = jwplatform.Client(api_key, api_secret)
		
	def uploadVideoJW(self, local_video_path, **kwargs):
		"""
		Function which creates new video object via s3 upload method.
		:param api_key: <string> JWPlatform api-key
		:param api_secret: <string> JWPlatform shared-secret
		:param local_video_path: <string> Path to media on local machine.
		:param kwargs: Arguments conforming to standards found @ https://developer.jwplayer.com/jw-platform/reference/v1/methods/videos/create.html
		:return:
		"""
		filename = os.path.basename(local_video_path)
		try:
			response = self.jwplatform_client.videos.create(upload_method='s3', **kwargs)
		except jwplatform.errors.JWPlatformError as e:
			LOG.error("Encountered an error creating a video\n{}".format(e))
			sys.exit(e.message)

		# Construct base url for upload
		upload_url = '{}://{}{}'.format(
			response['link']['protocol'],
			response['link']['address'],
			response['link']['path']
		)

		# Query parameters for the upload
		query_parameters = response['link']['query']
		
		uploadedVideoKey = response['media']['key']
		responseCode = '404'
		res = 'NA'

		# HTTP PUT upload using requests
		headers = {'Content-Disposition': 'attachment; filename="{}"'.format(filename)}
		with open(local_video_path, 'rb') as f:
			res = requests.put(upload_url, params=query_parameters, headers=headers, data=f)
			LOG.debug('uploading file {} to url {}'.format(local_video_path, res.url))
			LOG.debug('upload response: {}'.format(res.text))
			responseCode = res.status_code
			
		return {'responseCode': responseCode, 'videoKey': uploadedVideoKey, 'completeResponse': res}
		
		

def test():
	upload = uploadVideo('testID')
	upload.uploadVideoJW(r"C:\Users\Hemant\Videos\Funny_clips_1.mp4")