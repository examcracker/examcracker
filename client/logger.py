import logging

# Log level
logLevel = logging.INFO

def getLogFile(name):
	# create logger
	logger = logging.getLogger(name)
	logger.setLevel(logLevel)

	# create console handler and set level to debug
	fileHandle = logging.FileHandler('client.log')
	fileHandle.setLevel(logLevel)

	# create formatter
	formatter = logging.Formatter("%(asctime)s: [%(name)s] [%(levelname)s]: %(message)s", "%Y-%m-%d %H:%M:%S")

	# add formatter to fileHandle
	fileHandle.setFormatter(formatter)

	# add fileHandle to logger
	logger.addHandler(fileHandle)
	return logger