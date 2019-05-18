import os
import subprocess
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtGui
import httpReq
import httpReq
import service
import api
import json
import time
		
class worker(QThread):
	threadOutput = pyqtSignal('QString')

	def __init__(self, mediaFilePath, folderPath, userInfo, chapterid):
		QThread.__init__(self, None)
		self.mediaFilePath = mediaFilePath
		self.mediaFolderPath = folderPath
		self.serviceObj = service.ClientService()
		self.serviceObj.chapterid = chapterid
		self.userInfo = userInfo
		print("chapterId: ", chapterid)

		self.updateUserDetails()

	def updateUserDetails(self):
		self.serviceObj.encryptedid = self.userInfo['clientid']
		self.serviceObj.decodeClientId()

		self.serviceObj.publish = True
		self.serviceObj.encrypted = True
		self.serviceObj.drmkeyid = self.userInfo["drmkeyid"]
		self.serviceObj.drmkey = self.userInfo["drmkey"]
		self.serviceObj.dokey = self.userInfo["dokey"]
		self.serviceObj.dokeysecret = self.userInfo["dosecret"]
		self.serviceObj.bucketname = self.userInfo["bucketname"]

	def updateUploadStatus(self, res):
		responseDict = {}
		if 'videoKey' in res.keys():
			responseDict["result"] = api.status_stop_success
			responseDict["videokey"] = res["videoKey"]
			responseDict["duration"] = self.serviceObj.duration
			responseDict["sessionName"] = res["sessionName"]
		else:
			responseDict["result"] = api.status_upload_fail
			responseDict["fail_response"] = res
			
		responseDict["chapterid"] = self.serviceObj.chapterid
		responseDict["publish"] = self.serviceObj.publish
		responseDict["encrypted"] = self.serviceObj.encrypted
		responseDict["drmkeyid"] = self.serviceObj.drmkeyid
		responseDict["drmkey"] = self.serviceObj.drmkey

		responseDict["id"] = self.serviceObj.clientid
		httpReq.send(self.serviceObj.url, "/cdn/saveClientSession/", json.dumps(responseDict))

	def run(self):
		if os.path.exists(self.mediaFolderPath):
			listOfMp4Files = []
			for root, dirs, files in os.walk(self.mediaFolderPath):
				for file in files:
					if file.endswith('.mp4') or file.endswith('.mov'):
						listOfMp4Files.append(os.path.join(root, file))

			listOfMp4Files.sort(key=lambda x: os.path.getmtime(x))
			print ()
			self.totalFileCount = len(listOfMp4Files)
			doneMsg = "Total lectures found: " + str(self.totalFileCount) + "\n"
			self.threadOutput.emit(doneMsg)
			uploadCount = 0
			for item in listOfMp4Files:
				try:
					fileInfo = os.path.splitext(item)
					outputFile = fileInfo[0] + '_conv' + fileInfo[1]
					conversionState = service.getmp4CoversionCommand(item, outputFile)
					if conversionState != 'false':
						doneMsg = "Converting file: " + str(item) + "\n"
						self.threadOutput.emit(doneMsg)
						os.system(conversionState)
						item = outputFile

					res = self.serviceObj.uploadFileToCDN(item, False)
					
					if conversionState != 'false':
						os.remove(outputFile)
				
					self.updateUploadStatus(res)
					uploadCount += 1
					doneMsg = "Upload done for : " + str(item) + " (" + str(uploadCount) + "/" + str(self.totalFileCount) + ")\n"
					self.threadOutput.emit(doneMsg)
				except Exception as ex:
					doneMsg = "Upload fail : " + str(item) + " Error: " + str(ex) + "\n"
					self.threadOutput.emit(doneMsg)

			doneMsg = "\nDone!!\n\n"
			self.threadOutput.emit(doneMsg)
		else:
			try:
				fileInfo = os.path.splitext(self.mediaFilePath)
				outputFile = fileInfo[0] + '_conv' + fileInfo[1]
				conversionState = service.getmp4CoversionCommand(self.mediaFilePath, outputFile)
				if conversionState != 'false':
					doneMsg = "Converting file: " + str(self.mediaFilePath) + "\n"
					self.threadOutput.emit(doneMsg)
					os.system(conversionState)
					self.mediaFilePath = outputFile

				doneMsg = "Uploading lecture: " + str(self.mediaFilePath) + "\n"
				self.threadOutput.emit(doneMsg)
				res = self.serviceObj.uploadFileToCDN(self.mediaFilePath, False)
				if conversionState != 'false':
					os.remove(outputFile)

				self.updateUploadStatus(res)
				doneMsg = "Upload successful: " + str(self.mediaFilePath) + "\n\nDone!!\n"
				self.threadOutput.emit(doneMsg)
			except Exception as ex:
				doneMsg = "Upload fail error: " + str(ex) + "\n"
				self.threadOutput.emit(doneMsg)

class filedialogdemo(QFrame):
	def __init__(self):
		super(filedialogdemo, self).__init__()
		
		self.thread = None
		
		self.initWidget()
		self.initStyle()

	def dailogStylesheet(self):
		self.loginDialog.setStyleSheet("""
		.QLabel{color: #000000; font: \"Arial Regular\"; font-weight: Bold; font-size: 9pt;}
		.QLabel#title{color: #000000; font: \"Arial Regular\"; font-weight: Bold; font-size: 10pt;}
		.QLabel#dur{color: #000000; font: \"Arial Regular\"; font-weight: Bold; font-size: 9pt;}
		.QLineEdit{background-color: transparent; color: #000000; font: \"Arial Regular\"; font-size: 9pt;border-style: solid; border-width: 1px; border-color: #999999; padding: 4px;}
		.QLineEdit:focus {border-color: #00ccff;}
		.QLineEdit:edit-focus {border-color: #00ccff;}
		.QTextEdit{background-color: transparent; color: #000000; font: \"Arial Regular\"; font-size: 9pt;border-style: solid; border-width: 1px; border-color: #999999; padding: 4px;}
		.QTextEdit:focus {border-color: #00ccff;}
		.QTextEdit:edit-focus {border-color: #00ccff;}
		.QPushButton{color: #ffffff;background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #4e4e4e, stop:1 #2e2e2e);border-style: outset; border-width: 1px; border-radius: 4px; border-color: #000000; font: bold 9pt;}
		.QPushButton:hover {border-color: #00ccff;}
		.QPushButton:pressed {color: #00ccff; background-color: #000000; border-color: #00ccff;}
		.QScrollBar:vertical {background-color: rgb(17,17,17);width: 8px;margin: 0px 0px 0px 0px;}
		.QScrollBar::handle:vertical {background-color: #cdcdcd;border-radius: 2px;border-color: black;border-width: 1px;border-style: solid;margin: 0px 0px 0px 0px;image: url(:/scrollbar_handle_v);}
		.QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {background: none;}
		.QScrollBar::add-line:vertical {border-left: 0px solid black;border-top: 0px solid black;background-color: transparent;height: 0px;subcontrol-position: bottom;subcontrol-origin: margin;}
		.QScrollBar::sub-line:vertical {border-left: 0px solid black;border-bottom: 0px solid black;background-color: transparent;height: 0px;subcontrol-position: top;subcontrol-origin: margin;}
		 """)


	def createLoginDialog(self):
		self.loginDialog  = QDialog(self)

		self.errorMsg = QLabel("Login failed, please try again!")
		self.errorMsg.hide()

		self.userNameInput = QLineEdit()
		self.userNameInput.setPlaceholderText("Username")

		self.passwordInput = QLineEdit()
		self.passwordInput.setPlaceholderText("Password")
		self.passwordInput.setEchoMode(QLineEdit.Password)

		self.loginBtn = QPushButton('Login')
		self.loginBtn.setMinimumSize( 130,40)

		self.closeBtn = QPushButton('Close')
		self.closeBtn.setMinimumSize( 130,40)


		self.closeBtn.clicked.connect(self.loginDialog.close)
		self.loginBtn.clicked.connect(self.checkLogin)

		layoutVDialog = QVBoxLayout()
		layoutHDialog = QHBoxLayout()

		layoutVDialog.addWidget(self.errorMsg)
		layoutVDialog.addWidget(self.userNameInput)
		layoutVDialog.addWidget(self.passwordInput)
		layoutHDialog.addWidget(self.closeBtn)
		layoutHDialog.addWidget(self.loginBtn)

		layoutVDialog.addLayout(layoutHDialog)
		self.loginDialog.setMinimumHeight(200)

		self.loginDialog.setLayout(layoutVDialog)
		self.dailogStylesheet()
		self.loginDialog.setWindowTitle("Login")

		scriptDir = os.path.dirname(os.path.realpath(__file__))
		self.loginDialog.setWindowIcon(QtGui.QIcon(os.path.join(scriptDir, 'application.ico')))

		self.loginDialog.exec_()

	def checkLogin(self):

		self.errorMsg.hide()
		self.username = self.userNameInput.text()
		self.password = self.passwordInput.text()

		self.settings.setValue('username', self.username)
		self.settings.setValue('password', self.password)


		try:
			response = service.getProviderDetails(self.username, self.password)
			self.userDetails = response.json()
			if self.userDetails['result'] == False:
				self.errorMsg.show()
			else:
				self.loginDialog.close()
		except:
			self.errorMsg.show()

	def populateCourseOptions(self):
		index = 0
		for course in self.userDetails['courses']:
			self.comboBoxCourse.addItem(course['name'])
			self.comboBoxCourse.setItemData(index, course['id'], Qt.UserRole + 1)
			index +=  1

		self.onCourseSelection(0)

	def onCourseSelection(self, index):
		courseId = self.comboBoxCourse.itemData(index, Qt.UserRole + 1)
		self.comboBoxChapter.clear() 

		for course in self.userDetails['courses']:
			if courseId == course['id']:
				index = 0
				for chapter in course['chapters']:
					self.comboBoxChapter.addItem(chapter['name'])
					self.comboBoxChapter.setItemData(index, chapter['id'], Qt.UserRole + 1)
					index += 1


	def initWidget(self):
		
		self.setMinimumWidth(700)
		self.setMinimumHeight(400)

		self.settings = QSettings("GyaanHive", "UserDetails")

		self.username = self.settings.value('username', "")
		self.password = self.settings.value('password', "")

		if self.username == "" or self.password == "":
			self.createLoginDialog()
		else:
			try:
				response = service.getProviderDetails(self.username, self.password)
				self.userDetails = response.json()
				if self.userDetails['result'] == False:
					self.createLoginDialog()
			except:
				self.createLoginDialog()
		
		self.labelFilePath = QLineEdit()
		self.labelFilePath.setPlaceholderText("Provide lecture file path")
		self.labelFilePath.setReadOnly(True)

		self.btnBrowse = QPushButton('Browse File', self)
		self.btnBrowse.clicked.connect(self.getMediaFile)
		self.btnBrowse.setMinimumSize( 130,40)

		self.labelFilePath2 = QLineEdit()
		self.labelFilePath2.setPlaceholderText("Provide directory contains all the lectures")
		self.labelFilePath2.setReadOnly(True)

		self.btnBrowse2 = QPushButton('Browse folder', self)
		self.btnBrowse2.clicked.connect(self.getfolder)
		self.btnBrowse2.setMinimumSize( 130,40)

		self.courseLabel =  QLabel('Select Course:')
		self.comboBoxCourse = QComboBox()
		self.comboBoxCourse.setMinimumHeight(30)

		self.chapterLabel =  QLabel('Select Chapter:')
		self.comboBoxChapter = QComboBox()
		self.comboBoxChapter.setMinimumHeight(30)

		self.comboBoxCourse.currentIndexChanged.connect(self.onCourseSelection) 

		layoutV = QVBoxLayout()
		layoutH = QHBoxLayout()
		layoutH2 = QHBoxLayout()
		layoutH3 = QHBoxLayout()
		
		layoutH.addWidget(self.labelFilePath)
		layoutH.addWidget(self.btnBrowse)

		layoutH2.addWidget(self.labelFilePath2)
		layoutH2.addWidget(self.btnBrowse2)
		
		layoutH3.addWidget(self.courseLabel, 0, Qt.AlignLeft)
		layoutH3.addWidget(self.comboBoxCourse, 0, Qt.AlignLeft)
		layoutH3.addWidget(self.chapterLabel, 0, Qt.AlignRight)
		layoutH3.addWidget(self.comboBoxChapter, 0, Qt.AlignRight)
		
		self.line = QFrame();
		self.line.setFrameShape(QFrame.HLine);
		self.line.setFrameShadow(QFrame.Sunken);

		self.line2 = QFrame();
		self.line2.setFrameShape(QFrame.HLine);
		self.line2.setFrameShadow(QFrame.Sunken);
		
		layoutV.addLayout(layoutH)
		layoutV.addLayout(layoutH2)
		layoutV.addWidget(self.line, 1)

		layoutV.addLayout(layoutH3)
		layoutV.addWidget(self.line2, 1)

		self.btnConvert = QPushButton('Start Upload', self)
		self.btnConvert.setMinimumSize( 130,40)
		self.btnConvert.clicked.connect(self.startProcess)
		layoutV.addWidget(self.btnConvert)

		self.outputLabel =  QLabel('Upload process details:')
		self.output = QTextEdit()
		self.output.setReadOnly(True)
		layoutV.addWidget(self.outputLabel)
		layoutV.addWidget(self.output)
		
		self.setLayout(layoutV)
		self.setWindowTitle("GyaanHive upload application")
		
		scriptDir = os.path.dirname(os.path.realpath(__file__))
		self.setWindowIcon(QtGui.QIcon(os.path.join(scriptDir, 'application.ico')))

		self.populateCourseOptions()
		
	def initStyle(self):
		self.setStyleSheet("""
		.QLabel{color: #000000; font: \"Arial Regular\"; font-weight: Bold; font-size: 9pt;}
		.QLabel#title{color: #000000; font: \"Arial Regular\"; font-weight: Bold; font-size: 10pt;}
		.QLabel#dur{color: #000000; font: \"Arial Regular\"; font-weight: Bold; font-size: 9pt;}
		.QLineEdit{background-color: transparent; color: #000000; font: \"Arial Regular\"; font-size: 9pt;border-style: solid; border-width: 1px; border-color: #999999; padding: 4px;}
		.QLineEdit:focus {border-color: #00ccff;}
		.QLineEdit:edit-focus {border-color: #00ccff;}
		.QTextEdit{background-color: transparent; color: #000000; font: \"Arial Regular\"; font-size: 9pt;border-style: solid; border-width: 1px; border-color: #999999; padding: 4px;}
		.QTextEdit:focus {border-color: #00ccff;}
		.QTextEdit:edit-focus {border-color: #00ccff;}
		.QComboBox{color: #000000; font: \"Arial Regular\"; font-weight: Bold; font-size: 9pt;}
		.QPushButton{color: #ffffff;background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #4e4e4e, stop:1 #2e2e2e);border-style: outset; border-width: 1px; border-radius: 4px; border-color: #000000; font: bold 9pt;}
		.QPushButton:hover {border-color: #00ccff;}
		.QPushButton:pressed {color: #00ccff; background-color: #000000; border-color: #00ccff;}
		.QScrollBar:vertical {background-color: rgb(17,17,17);width: 8px;margin: 0px 0px 0px 0px;}
		.QScrollBar::handle:vertical {background-color: #cdcdcd;border-radius: 2px;border-color: black;border-width: 1px;border-style: solid;margin: 0px 0px 0px 0px;image: url(:/scrollbar_handle_v);}
		.QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {background: none;}
		.QScrollBar::add-line:vertical {border-left: 0px solid black;border-top: 0px solid black;background-color: transparent;height: 0px;subcontrol-position: bottom;subcontrol-origin: margin;}
		.QScrollBar::sub-line:vertical {border-left: 0px solid black;border-bottom: 0px solid black;background-color: transparent;height: 0px;subcontrol-position: top;subcontrol-origin: margin;}
		 """)
	
	def getMediaFile(self):
		mediaFilePath, _ = QFileDialog.getOpenFileName(self, 'Open file')
		mediaFilePath = QDir.toNativeSeparators(mediaFilePath)
		self.labelFilePath.setText(mediaFilePath)
		self.labelFilePath2.setText("")
		
	def getfolder(self):
		mediaFolderPath = QFileDialog.getExistingDirectory(self,"Open a folder", "", QFileDialog.ShowDirsOnly)
		mediaFolderPath = QDir.toNativeSeparators(mediaFolderPath)
		self.labelFilePath2.setText(mediaFolderPath)
		self.labelFilePath.setText("")
		
	def startProcess(self):
		mediaFilePath = self.labelFilePath.text()
		mediaFolderPath = self.labelFilePath2.text()

		chapterId = self.comboBoxChapter.itemData(self.comboBoxChapter.currentIndex(), Qt.UserRole + 1)
				
		self.thread = worker(str(mediaFilePath), str(mediaFolderPath), self.userDetails, chapterId)
		self.thread.threadOutput.connect(self.updateOuput)
		self.thread.start()
			
	def updateOuput(self, message):
		self.output.append(message)
		
				
def main():
   app = QApplication(sys.argv)
   ex = filedialogdemo()
   ex.show()
   sys.exit(app.exec_())
	
if __name__ == '__main__':
   main()