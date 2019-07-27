from __future__ import print_function
from Crypto.Cipher import AES
import captureFeed
import uploadVideo
import uploadVideoDO
import configparser
import os
import sys
import websocket
import pysher
import pusher
import time
import api
import base64
import json
import signal
import httpReq
import platform
import logger
import psutil
from collections import deque
import glob
import socket
import sendMail
import subprocess
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from pymediainfo import MediaInfo
import threading
import clientUploadApp
from functools import partial

# schedule states
STOPPED = 0
RUNNING = 1
UPLOADING = 2

try:
    import thread
except ImportError:
    import _thread as thread

aes_key = base64.b64decode("iUmAAGnhWZZ75Nq38hG76w==")
aes_iv = base64.b64decode("rgMzT3a413fIAvESuQjt1Q==")

KEY_ID = "a7e61c373e219033c21091fa607bf3b8"
KEY = "76a6c65c5ea762046bd749a2e632ccbb"

# Log file
LOG = logger.getLogFile(__name__)

bitRateAndResolutionList = ['600 Kbps (1280x720)', '512 Kbps (1280x720)', '350 Kbps (720x406)']


class WindowsInhibitor:
    '''Prevent OS sleep/hibernate in windows; code from:
    https://github.com/h3llrais3r/Deluge-PreventSuspendPlus/blob/master/preventsuspendplus/core.py
    API documentation:
    https://msdn.microsoft.com/en-us/library/windows/desktop/aa373208(v=vs.85).aspx'''
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __init__(self):
        pass

    def inhibit(self):
        import ctypes
        LOG.info("Preventing Windows from going to sleep")
        ctypes.windll.kernel32.SetThreadExecutionState(WindowsInhibitor.ES_CONTINUOUS | WindowsInhibitor.ES_SYSTEM_REQUIRED)

    def uninhibit(self):
        import ctypes
        LOG.info("Allowing Windows to go to sleep")
        ctypes.windll.kernel32.SetThreadExecutionState(WindowsInhibitor.ES_CONTINUOUS)

serviceObj = None
systemname = platform.node()

def getProviderDetails(username,password,debug=False):
    url = "https://www.gyaanhive.com"
    if debug == True:
        url = "http://127.0.0.1:8000"
    cipher = AES.new(aes_key, AES.MODE_CFB, aes_iv)
    encPassword = cipher.encrypt(password.encode())
    encPasswordDecode = base64.b64encode(encPassword).decode()
    blankDict = {}
    blankDict['email'] = username
    response = httpReq.send(url, "/provider/getProviderProfile/" + str(username) + '/'+ str(encPasswordDecode), json.dumps(blankDict))
    #print(response.json())
    return response

def getDuration(inputfile):
	media_info = MediaInfo.parse(inputfile)
	for track in media_info.tracks:
		if track.track_type.lower() == 'general':
			return (track.duration/1000)

def getmp4CoversionCommand(inputfile, outputfile):
    command = 'captureApp -i "'+inputfile + '" -vcodec '
    vcodec = 'copy'
    acodec = 'copy'
    media_info = MediaInfo.parse(inputfile)
    for track in media_info.tracks:
        if track.track_type.lower() == 'video' and 'avc' not in track.format.lower():
            vcodec = 'libx264'
        elif track.track_type.lower() == 'audio' and 'aac' not in track.format.lower():
            acodec = 'aac'
    if vcodec == 'copy' and acodec == 'copy':
        return 'false'
    command = command + vcodec + ' -acodec ' + acodec + ' "' + outputfile + '"'
    return command

def sendCaptureResponse(state, id, streamName=None):
    global serviceObj
    data = {}
    data["state"] = state
    data["id"] = id
    if streamName != None:
        data["streamName"] = streamName
    httpReq.send(serviceObj.url, "/schedule/captureState/" + str(serviceObj.scheduleid), json.dumps(data))

def on_message(message):
    #LOG.info(str(message))
    global serviceObj
    responseDict = {}
    # always add encrypted provider id in response
    responseDict["id"] = serviceObj.encryptedid
    messageDict = json.loads(message)

    if "command" in messageDict.keys():
        machine = messageDict["machine"]
        # check if this client is intended recipient
        if machine != systemname:
            LOG.error("Mismatch in the machine name, input name: " + str(machine) + " actual name is: " + str(systemname))
            return
        command = messageDict["command"]
        LOG.info("Command recieved: " + str(command))
        if command == api.command_start:
            if serviceObj.capturing:
                responseDict["result"] = api.status_capture_started
            else:
                responseDict["result"] = api.status_start_success
                serviceObj.scheduleid = messageDict["id"]
                serviceObj.chapterid = messageDict["chapterid"]
                serviceObj.publish = messageDict["publish"]
                serviceObj.encrypted = messageDict["encrypted"]
                serviceObj.drmkeyid = messageDict["drmkeyid"]
                serviceObj.drmkey = messageDict["drmkey"]
                serviceObj.mediaServer = messageDict["mediaServer"]
                serviceObj.mediaServerApp = messageDict["mediaServerApp"]
                serviceObj.live = messageDict["live"]
                serviceObj.timeout = int(messageDict["duration"])*60
                serviceObj.dokey = messageDict["dokey"]
                serviceObj.dokeysecret = messageDict["dokeysecret"]
                serviceObj.bucketname = messageDict["bucketname"]
                serviceObj.multiBitRate = messageDict["multiBitRate"]
                serviceObj.liveStreamName = str(serviceObj.clientid)+'__'+str(serviceObj.scheduleid) + '__' + str(serviceObj.chapterid)
                serviceObj.capture.fillMediaServerSettings(serviceObj.mediaServer, serviceObj.mediaServerApp, serviceObj.live,serviceObj.liveStreamName)
                sendCaptureResponse(RUNNING, serviceObj.encryptedid,serviceObj.liveStreamName)
                serviceObj.startCapture()
        elif command == api.command_stop:
            if not serviceObj.capturing:
                responseDict["result"] = api.status_no_capture_started
                serviceObj.scheduleid = messageDict["id"]
                sendCaptureResponse(STOPPED, serviceObj.encryptedid)
                #res = serviceObj.stopCapture(responseDict)
                serviceObj.stopCapture(responseDict)
            else:
                sendCaptureResponse(UPLOADING, serviceObj.encryptedid)
                serviceObj.stopCapture(responseDict)
                """ res = serviceObj.stopCapture(responseDict)
                if 'videoKey' in res.keys():
                    responseDict["result"] = api.status_stop_success
                    responseDict["videokey"] = res["videoKey"]
                    responseDict["duration"] = serviceObj.duration
                    responseDict["sessionName"] = res["sessionName"]
                else:
                    responseDict["result"] = api.status_upload_fail
                    responseDict["fail_response"] = res
                    
                responseDict["chapterid"] = serviceObj.chapterid
                responseDict["publish"] = serviceObj.publish
                responseDict["encrypted"] = serviceObj.encrypted
                responseDict["drmkeyid"] = serviceObj.drmkeyid
                responseDict["drmkey"] = serviceObj.drmkey

                responseDict["id"] = serviceObj.clientid
                #import pdb; pdb.set_trace()
                apiResponse = httpReq.send(serviceObj.url, "/cdn/saveClientSession/", json.dumps(responseDict))
                retryCount = 0
                while apiResponse.status_code != 200:
                    LOG.error("Retrying the save client sesion, last error code: " + str(apiResponse.status_code))
                    time.sleep(10)
                    apiResponse = httpReq.send(serviceObj.url, "/cdn/saveClientSession/", json.dumps(responseDict))
                    retryCount += 1
                    if retryCount > 10:
                        LOG.error("Failed to update the save client session, error code: " + str(apiResponse.status_code))
                        break

                serviceObj.uploadOriginalFileToCDN(serviceObj.capture.outputFileName) """

                #LOG.info ("Stop command completed")

        elif command == api.command_upload_logs:
            lineCount = 50
            if 'lineCount' in messageDict.keys():
                lineCount = messageDict["lineCount"]
            logData = ""
            with open(logger.logFileName) as fin:
                logData = fin.readlines()[-lineCount:]
            responseDict["logs"] = logData
            httpReq.send(serviceObj.url, "/cdn/logData/", json.dumps(responseDict))
        elif command == api.command_get_recent_capture_file_details:
            if serviceObj.capture.outputFileName != "":
                responseDict['filePath'] = str(serviceObj.capture.outputFileName)
            else:
                list_of_files = glob.glob( serviceObj.capture.outputFolder + r'\*.mp4')
                responseDict['filePath'] = max(list_of_files, key=os.path.getctime)

            responseDict["scheduleid"] = serviceObj.scheduleid
            responseDict["chapterid"] = serviceObj.chapterid
            responseDict["publish"] = serviceObj.publish
            httpReq.send(serviceObj.url, "/cdn/getFileDetails/", json.dumps(responseDict))
        elif command == api.command_upload_file:
            filePath = messageDict["filePath"]
            
            serviceObj.uploadFileToCDN(filePath, responseDict)
            """ res = serviceObj.uploadFileToCDN(filePath, responseDict)
            if 'videoKey' in res.keys():
                responseDict["result"] = api.status_upload_sucess
                responseDict["videokey"] = res["videoKey"]
                responseDict["sessionName"] = res["sessionName"]
                httpReq.send(serviceObj.url, "/cdn/saveClientSession/", json.dumps(responseDict))
            else:
                responseDict["result"] = api.status_upload_fail
                responseDict["fail_response"] = res

            responseDict["chapterid"] = messageDict["chapterid"]
            responseDict["publish"] = messageDict["publish"]
            responseDict["id"] = messageDict["id"]
            httpReq.send(serviceObj.url, "/cdn/uploadFileStatus/", json.dumps(responseDict))

            serviceObj.uploadOriginalFileToCDN(filePath) """
            
        elif command == api.command_check_client_active:
            responseDict['result'] = api.status_client_active
            httpReq.send(serviceObj.url, "/cdn/clientState/", json.dumps(responseDict))
    else:
        LOG.warn("Unhandled command: " + str(messageDict.keys()))

def connect_handler(data):
    #print(data)
    global serviceObj
    channel = serviceObj.pusherobj.subscribe(str(serviceObj.clientid))
    channel.bind(str(serviceObj.clientid), on_message)

def checkInternetConnection(hostname):
	try:
		# see if we can resolve the host name -- tells us if there is
		# a DNS listening
		host = socket.gethostbyname(hostname)
		# connect to the host -- tells us if the host is actually
		# reachable
		s = socket.create_connection((host, 80), 2)
		return True
	except:
		pass
		
	return False

class ClientService(object):

    wsclient = None
    capturing = False
    chapterid = None
    publish = False
    encrypted = False
    drmkeyid = ''
    drmkey = ''
    debug = False
    encryptedid = None
    clientid = None
    pusherobj = None
    url = None
    scheduleid = None
    mediaServer = None
    mediaServerApp = None
    live = False
    liveStreamName = ''
    mp4fragpath = ''
    mp4encryptpath = ''
    mp4dashpath = ''
    dokey = ''
    dokeysecret = ''
    bucketname = ''
    duration = 0
    tmpFiles = []
    
    def __init__(self):
        websocket.enableTrace(True)

        dir_path = os.path.dirname(os.path.realpath(__file__))
        if getattr(sys, 'frozen', False):
            dir_path = os.path.dirname(sys.executable)

        config = configparser.ConfigParser()
        configPath = os.path.join(dir_path, "arguments.cfg")
        config.readfp(open(configPath))

        self.encryptedid = config.get("config", "clientId")
        self.decodeClientId()

        self.capture = captureFeed.captureFeed(self.clientid, configPath, os.path.join(dir_path, "captureApp.exe"))
        self.mp4fragpath = os.path.join(dir_path, "bin", "doFragment.exe")
        self.mp4encryptpath = os.path.join(dir_path, "bin", "doEncrypt.exe")
        self.mp4dashpath = os.path.join(dir_path ,"bin", "convertToDash.bat")

        self.uploadJW = uploadVideo.uploadVideo(self.clientid)
        self.upload = uploadVideoDO.uploadVideoDO(self.clientid)
        self.timeout = 0
        self.captureStartTime = -1
        self.captureAppProcName = "captureApp.exe"

        self.uploadRetryCount = 5

        self.internetCheckTimeout = 10*60 # 30 mins
       
        self.checkFolderInterval = 60*60*1 # 1 hours

        self.TEST_REMOTE_SERVER = "www.google.com"

        self.osleep = WindowsInhibitor()

        self.tmpfolder = 'tmp'

        self.loopCount = 0
        self.uploadThread = None
        self.loglevel = config.get("config","loglevel")

        self.multiBitRateList = ['Default', '350 Kbps (720x406)']
        self.resolutionBitRateMap = {'Default': {'bitrate':'512k', 'bufsize': '512k', 'maxrate': '750k'}, '600 Kbps (1280x720)': {'bitrate':'600k', 'bufsize': '600k', 'maxrate': '1000k', 'resolution': '1280x720'}, '512 Kbps (1280x720)': {'bitrate':'512k', 'bufsize': '512k', 'maxrate': '750k', 'resolution': '1280x720'}, '350 Kbps (720x406)': {'bitrate':'350k', 'bufsize': '350k', 'maxrate': '600k', 'resolution': '720x406'}}

        try:
            self.deleteContent = config.getboolean("config", "deleteContent")
            self.waitBeforeDelete = int(config.get("config", "waitBeforeDelete"))
            self.outputFolder = config.get("config","outputFolder")

            self.debug = bool(int(config.get("config", "debug")))
        except:
            pass

        self.url = "https://www.gyaanhive.com"
        if self.debug:
            self.url = "http://127.0.0.1:8000"

    def decodeClientId(self):
        decipher = AES.new(aes_key, AES.MODE_CFB, aes_iv)
        self.clientid = decipher.decrypt(base64.b64decode(self.encryptedid)).decode()

    def close(self):
        self.wsclient.close()

    def checkAndCleanCapturedData(self):
        time_in_secs = time.time() - (self.waitBeforeDelete * 24 * 60 * 60)
        for root, dirs, files in os.walk(self.outputFolder):
            for file_ in files:
                try:
                    extension = file_.split('.')[-1]
                    if extension != 'mp4':
                        LOG.debug ("Skipping delete since file is not mp4: " + str(file_))
                        continue
                    full_path = os.path.join(root, file_)
                    stat = os.stat(full_path)
                    if stat.st_mtime <= time_in_secs:
                        os.remove(full_path)
                except Exception as ex:
                    LOG.error("Exception in cleaning up the output folder: " + str(ex))
                    pass

    def checkAndKillProcess(self):
        self.osleep.uninhibit()
        for proc in psutil.process_iter():
            # check whether the process name matches
            if proc.name() == self.captureAppProcName:
                proc.kill()

    def startCapture(self):
        if self.capturing:
            LOG.warn ("Already capturing")
            return

        # disable sleep
        self.osleep.inhibit()
        self.loopCount = 0

        self.capturing = True
        self.captureStartTime = int(round(time.time()))
        self.capture.startCapturing()

    

    def upload_directory_to_DO(self,path,bucketname):
        # Initialize a session using DigitalOcean Spaces.
        LOG.info ("Uploading mpd file to Digital ocean space")
        client = self.getUploadClient()

        for root, dirs, files in os.walk(path):
            nested_dir = root.replace(path, '')
            if nested_dir:
                nested_dir = nested_dir.replace('/','',1) + '/'
            nested_dir = nested_dir.replace('\\','/')
            if nested_dir.startswith('/'):
                nested_dir = nested_dir[1:]
            for file in files:
                complete_file_path = os.path.join(root, file)
                file = nested_dir + file if nested_dir else file
                #print ("[S3_UPLOAD] Going to upload {complete_file_path} to s3 bucket {s3_bucket} as {file}"\
                #    .format(complete_file_path=complete_file_path, s3_bucket=bucketname, file=file))
                client.upload_file(complete_file_path, bucketname, file,ExtraArgs={'ACL':'public-read'})

    def removeTempFiles(self,tmpfiles):
        import shutil
        for fileDir in tmpfiles:
            if os.path.isfile(fileDir):
                os.remove(fileDir)
            else:
                shutil.rmtree(fileDir)

    def uploadFileToJWCDN(self, filePath):
        # Stopping windows to go in sleep mode while we upload a file
        try:
            self.osleep.inhibit()
            LOG.info ("Uploading file to server: " + str(filePath))
            retryCount = 0
            uploadResponse = {}
            if not os.path.isfile(filePath):
                uploadResponse['fail_reason'] = "Invalid file path : " + str(filePath)
                return uploadResponse 

            if os.stat(filePath).st_size == 0:
                uploadResponse['fail_reason'] = "File size is 0 bytes: " + str(filePath)
                return uploadResponse

            while retryCount < self.uploadRetryCount:
                try:
                    uploadResponse = self.uploadJW.uploadVideoJW(filePath)
                    LOG.info ("Uploading done")
                    LOG.debug("Video Server response: " + str(uploadResponse))
                    break
                except Exception as ex:
                    retryCount += 1
                    if retryCount < self.uploadRetryCount:
                        internetCheckWait = 5
                        loopCount = self.internetCheckTimeout/internetCheckWait
                        status = checkInternetConnection(self.TEST_REMOTE_SERVER)
                        while loopCount > 0 and status == False:
                            time.sleep(internetCheckWait) 
                            loopCount = loopCount - 1
                            status = checkInternetConnection(self.TEST_REMOTE_SERVER)

                        LOG.info("Internet conectivity status: " + str(status))

                    LOG.error("Exception in uploading the file: " + str(ex))
                    uploadResponse['fail_reason'] = str(ex)
                    continue
                
            return uploadResponse
        except Exception as ex:
             LOG.error("Exception in uploading the file: " + str(ex))
             uploadResponse['fail_reason'] = str(ex)
             return uploadResponse

        finally:
            self.osleep.uninhibit()

    '''
        originalCommand
        captureApp.exe -i inputFile -strict experimental -codec:a aac -ac 2 -ab 128k -preset slow -map_metadata -1 -codec:v libx264 -profile:v baseline -map 0 -force_key_frames "expr:eq(mod(n,30),0)" -bufsize 500k -maxrate 750k -x264opts rc-lookahead=300 -s 708x480 -f mp4 video_00500.mp4
    '''

    def resizeMediaFile(self, resolution):
        filePath = self.resizeBaseFilePath
        fileNameDetails = os.path.splitext(filePath)
        outputFilePath = fileNameDetails[0] + '_' + resolution + fileNameDetails[1]
        if resolution != 'Default' and resolution in self.resolutionBitRateMap:
            commandToResize = str(self.captureAppProcName) + ' -i "' + str(filePath) +'" -codec:a aac -ac 2 -ab 128k -preset slow -map_metadata -1 -codec:v libx264 -map 0 -force_key_frames "expr:eq(mod(n,60),0)" -b:v ' + self.resolutionBitRateMap[resolution]['bitrate'] + ' -bufsize '+ self.resolutionBitRateMap[resolution]['bufsize'] + ' -maxrate ' + self.resolutionBitRateMap[resolution]['maxrate'] + ' -x264opts rc-lookahead=300 -s '+ self.resolutionBitRateMap[resolution]['resolution'] + ' -loglevel ' + self.loglevel + ' "' + str(outputFilePath) + '"'
        else:
            commandToResize = str(self.captureAppProcName) + ' -i "' + str(filePath) +'" -codec:a aac -ac 2 -ab 128k -preset slow -map_metadata -1 -codec:v libx264 -map 0 -force_key_frames "expr:eq(mod(n,60),0)" -b:v ' + self.resolutionBitRateMap['Default']['bitrate'] + ' -bufsize '+ self.resolutionBitRateMap['Default']['bufsize'] + ' -maxrate ' + self.resolutionBitRateMap['Default']['maxrate'] + ' -x264opts rc-lookahead=300 -loglevel ' + self.loglevel + ' "' + str(outputFilePath) + '"'

        try:
            os.system(commandToResize)
            LOG.info ("Resizing of the video is successful")

        except Exception as ex:
             LOG.error("Exception in resizing the file: " + str(ex))

        return outputFilePath

    def fragmentAndEncFile(self, filePath):
        dirname = os.path.dirname(filePath)
        fragfilepath = os.path.join(dirname, os.path.basename(filePath).split(".mp4")[0] + "_frag.mp4")
        self.tmpFiles.append(fragfilepath)
        mp4fragmentProc = subprocess.Popen([self.mp4fragpath,'--fragment-duration' ,'10000',filePath, fragfilepath])
        mp4fragmentProc.communicate()

        encfilepath = os.path.join(dirname, os.path.basename(fragfilepath).split("_frag.mp4")[0] + "_enc.mp4")
        self.tmpFiles.append(encfilepath)
        mp4encryptProc = subprocess.Popen([self.mp4encryptpath, "--method", "MPEG-CENC",
                                        "--key", "1:" + self.drmkey + ":0000000000000000", "--property", "1:KID:" + self.drmkeyid,
                                        "--global-option", "mpeg-cenc.eme-pssh:true",
                                        "--key", "2:" + self.drmkey + ":0000000000000000", "--property", "2:KID:" + self.drmkeyid,
                                        fragfilepath, encfilepath])
        mp4encryptProc.communicate() 
        return encfilepath


    def encryptTheContent(self, filePath, resizeFilePath = ''):
        resizeEncPath = ''
        if os.path.isfile(resizeFilePath):
            resizeEncPath = self.fragmentAndEncFile(resizeFilePath)

        
        encfilepath = self.fragmentAndEncFile(filePath)
        LOG.info ("Create encrypted mpd file and upload to CDN")
        self.videoKey = str(time.strftime("%c").replace(':', '_').replace(' ','_')) + "_" + str(self.clientid)
        # create temporary directory and create mpd file in tmp directory
        dirname = os.path.dirname(filePath)
        self.tmpdir = os.path.join(dirname,self.tmpfolder)
        if not os.path.isdir(self.tmpdir):
            os.mkdir(self.tmpdir)
        
        self.mpdoutpath = os.path.join(self.tmpdir,self.videoKey)
        self.tmpFiles.append(self.mpdoutpath)
        mpdfilename = self.videoKey+'.mpd'
        if os.path.isfile(resizeEncPath):
            mp4dashProc = subprocess.call([self.mp4dashpath, '-o', self.mpdoutpath,'--mpd-name',mpdfilename,encfilepath,resizeEncPath])
        else:
            mp4dashProc = subprocess.call([self.mp4dashpath, '-o', self.mpdoutpath,'--mpd-name',mpdfilename,encfilepath])
        #mp4dashProc.communicate()

    def uploadOriginalFileToCDN(self, filePath):
        # Stopping windows to go in sleep mode while we upload a file
        try:
            self.osleep.inhibit()
            self.upload.uploadOriginalVideo(self.bucketname, self.dokey, self.dokeysecret, filePath, self.videoKey)
        except Exception as ex:
             LOG.error("Exception in uploading the original file: " + str(ex))

        finally:
            self.osleep.uninhibit()

    def uploadFileToCDNThreaded(self, filePath, sendResponse, uploaderInstance = None):
        # Stopping windows to go in sleep mode while we upload a file
        uploadResponse = {}
        try:
            self.osleep.inhibit()
            LOG.info ("Uploading file to server: " + str(filePath))
            if not os.path.isfile(filePath):
                LOG.error ("Invalid file path : " + str(filePath))
                uploadResponse['fail_reason'] = "Invalid file path : " + str(filePath)
                return uploadResponse 

            if os.stat(filePath).st_size == 0:
                LOG.error ("File size is 0 bytes: " + str(filePath))
                uploadResponse['fail_reason'] = "File size is 0 bytes: " + str(filePath)
                return uploadResponse

            self.upload.alreadyUploadedList = []

            try:
                self.tmpFiles = []
                # Start encryption
                self.duration = getDuration(filePath)
                uploadResponse["duration"] = self.duration
                if self.multiBitRate:
                    if uploaderInstance:
                        uploaderInstance.uploadUpdateMsg("Creating multi bitrate files. Please wait...")

                    pool = ThreadPool(len(self.multiBitRateList))

                    self.resizeBaseFilePath = filePath

                    listOfResizeFiles = pool.map(self.resizeMediaFile,self.multiBitRateList)
                    
                    self.tmpFiles.extend(listOfResizeFiles)

                    '''for resolution in self.multiBitRateList:
                        listOfResizeFiles.append(resizeFilePath)
                        self.tmpFiles.append(resizeFilePath)'''

                    '''resolution = '350 Kbps (720x406)'
                    resizeFilePath_480 = self.resizeMediaFile(filePath, resolution)
                    self.tmpFiles.append(resizeFilePath_480)'''

                    self.encryptTheContent(listOfResizeFiles[0], listOfResizeFiles[1])
                else:
                    self.encryptTheContent(filePath)
                
                filename = os.path.basename(filePath)
                # upload mpd file to digital ocean
                self.upload.uploadVideoDO(self.mpdoutpath,self.bucketname, self.dokey, self.dokeysecret, uploaderInstance)
                uploadResponse = {'responseCode': '200', 'videoKey': self.videoKey, 'completeResponse': 'success', 'sessionName': filename}
                LOG.info ("Uploading done")
                LOG.info("Video Server response: " + str(uploadResponse))

            except Exception as ex:
                LOG.error("Exception in uploading the file: " + str(ex))
                uploadResponse['fail_reason'] = str(ex)
                
        except Exception as ex:
             LOG.error("Exception in uploading the file: " + str(ex))
             uploadResponse['fail_reason'] = str(ex)
             return uploadResponse

        finally:
            # Now remove all temporary files created
            if sendResponse:
                sendCaptureResponse(STOPPED, self.encryptedid)
            self.removeTempFiles(self.tmpFiles)
            self.osleep.uninhibit()

        return uploadResponse

    def uploadAndUpdateDB(self, filePath, responseDict, sendResponse):
        responseDict["chapterid"] = self.chapterid
        responseDict["publish"] = self.publish
        responseDict["encrypted"] = self.encrypted
        responseDict["drmkeyid"] = self.drmkeyid
        responseDict["drmkey"] = self.drmkey
        responseDict["bucketname"] = self.bucketname
        responseDict["dokey"] = self.dokey
        responseDict["dokeysecret"] = self.dokeysecret
        responseDict["multiBitRate"] = self.multiBitRate

        res = self.uploadFileToCDNThreaded(filePath, sendResponse)
        if 'videoKey' in res.keys():
            responseDict["result"] = api.status_stop_success
            responseDict["videokey"] = res["videoKey"]
            responseDict["sessionName"] = res["sessionName"]
            if 'duration' in res.keys():
                responseDict["duration"] = res["duration"]
            else:
                responseDict["duration"] = self.duration
        else:
            responseDict["result"] = api.status_upload_fail
            responseDict["fail_response"] = res

        apiResponse = httpReq.send(self.url, "/cdn/saveClientSession/", json.dumps(responseDict))
        retryCount = 0
        while apiResponse.status_code != 200:
            LOG.error("Retrying the save client sesion, last error code: " + str(apiResponse.status_code))
            time.sleep(10)
            apiResponse = httpReq.send(self.url, "/cdn/saveClientSession/", json.dumps(responseDict))
            retryCount += 1
            if retryCount > 10:
                LOG.error("Failed to update the save client session, error code: " + str(apiResponse.status_code))
                break

        #self.uploadOriginalFileToCDN(self.capture.outputFileName)


    def uploadFileToCDN(self, filePath, responseDict, sendResponse = True):
        '''LOG.info ("Uploading task in thread")
        if self.uploadThread and self.uploadThread.isAlive():
            LOG.warn ("Upload threading is already uploading hence waiting for upload to finish")
            self.uploadThread.join()

        self.uploadThread = threading.Thread(target=self.uploadAndUpdateDB, args=(filePath, responseDict, sendResponse))
        self.uploadThread.start()'''

        self.uploadAndUpdateDB(filePath, responseDict, sendResponse)
        
    def stopCapture(self, responseDict):
        if not self.capturing:
            self.checkAndKillProcess()
            LOG.warn ("No active capturing")
            return {"videoKey": None}

        self.capturing = False
        self.timeout = 0
        self.capture.stopCapturing()
        time.sleep(5)

        toAddr = ['heman.t021@gmail.com', 'kunaldceit@gmail.com', 'kghoshnitk@gmail.com']
        fromAddr = 'mygyaanhive@yahoo.com'
        pwd = 'examcracker2018'
        subject = 'Client Logs'
        mailBody = 'Client logs are attached with this mail'
        attachmentPath = self.capture.captureAppLogPath
                
        #uploadResponse = self.uploadFileToCDN(self.capture.outputFileName, responseDict)
        self.uploadFileToCDN(self.capture.outputFileName, responseDict)
        
        try:
            sendMail.sendEmail(toAddr, fromAddr, pwd, attachmentPath, subject, mailBody)
            attachmentPath = logger.logFileName
            sendMail.sendEmail(toAddr, fromAddr, pwd, attachmentPath, subject, mailBody)
        except Exception as ex:
            LOG.error("Exception in sending mail: " + str(ex))


        #return uploadResponse

    def run(self):
        
        LOG.info(self.url)

        self.pusherobj = pysher.Pusher("3ff394e3371be28d8abd", "ap2")
        self.pusherobj.connection.bind('pusher:connection_established', connect_handler)
        self.pusherobj.connect()

        global systemname
        initDict = {}
        initDict["id"] = self.encryptedid
        initDict["system"] = systemname
        httpReq.send(self.url, "/schedule/systemName", json.dumps(initDict))

        waitCounterForCleaningFiles = self.checkFolderInterval
        
        while True:
            time.sleep(1)
            self.loopCount += 1
            if (self.loopCount % 900) ==  1:
                status = checkInternetConnection(self.TEST_REMOTE_SERVER)
                if self.capturing and status == False:
                    LOG.info ("Client internet connection status: " + str(status))
            if self.loopCount > 1800:
                if self.capturing:
                    LOG.info ("Client is running")
                self.loopCount = 0

            if self.capturing:
                timeDiff = int(round(time.time())) - self.captureStartTime
                if timeDiff < 600 and timeDiff > 30 and (self.loopCount % 60) == 0:
                    if not self.capture.checkCapturedFileExist():
                        LOG.error ("Captured file not exist restarting the capture process")
                        self.capture.stopCapturing()
                        self.capture.startCapturing()


            if self.capturing and self.timeout > 0:
                timeDiff = int(round(time.time())) - self.captureStartTime
                if timeDiff >= self.timeout:
                    responseDict = {}    
                    responseDict["id"] = self.encryptedid                                                  
                    LOG.info ("Timeout stopping the capturing")
                    sendCaptureResponse(UPLOADING, self.encryptedid)
                    self.stopCapture(responseDict)
                    """ res = self.stopCapture(responseDict)
                    if 'videoKey' in res.keys():
                        responseDict["result"] = api.status_stop_success
                        responseDict["videokey"] = res["videoKey"]
                        responseDict["sessionName"] = res["sessionName"]
                    else:
                        responseDict["result"] = api.status_upload_fail
                        responseDict["fail_response"] = res

                    responseDict["chapterid"] = self.chapterid
                    responseDict["publish"] = self.publish
                    responseDict["encrypted"] = self.encrypted
                    responseDict["drmkeyid"] = self.drmkeyid
                    responseDict["drmkey"] = self.drmkey
                    responseDict["duration"] = self.duration
                    httpReq.send(self.url, "/cdn/saveClientSession/", json.dumps(responseDict))
                    self.uploadOriginalFileToCDN(self.capture.outputFileName) """
            
            waitCounterForCleaningFiles += 1
            if waitCounterForCleaningFiles > self.checkFolderInterval:
                waitCounterForCleaningFiles = 0
                if self.deleteContent:
                    self.checkAndCleanCapturedData()

				

def main():
    global serviceObj
    while True:
        try:
            serviceObj = ClientService()
            serviceObj.run()
        except Exception as ex:
            LOG.error("Exception in main function: " + str(ex))
            serviceObj.osleep.uninhibit()
            time.sleep(60)
            continue

if __name__ == "__main__":
    main()

