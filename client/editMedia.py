# Options editMedia -operation <cut/merge> -start <0/start time in seconds> -end <o/end time> -i <files>
# For cut : -i <files> --> should be single file
# http://www.markbuckler.com/post/cutting-ffmpeg/
import argparse
import sys
import os
parser = argparse.ArgumentParser(                                           
    description='File edit tool')
                                   
parser.add_argument('-operation',                                   
                    help = "operation cut/merge.",                                    
                    default = 'cut')
parser.add_argument('-start', help="Cut start time in seconds.",                                    
                    default=0, type=int)
parser.add_argument('-duration', help="Duration from start in seconds.",                                    
                    default=0, type=int)
parser.add_argument('-file', action='append',           
                    help="List of files to cut or merge.",                                    
                    default=[])
parser.add_argument('-output',                                   
                    help = "output file name",                                    
                    default = 'out.mp4')

def editMedia (parser):
    app = 'captureApp.exe'
    if parser.operation == 'cut':
        cmd = app + ' -ss ' + str(parser.start) + ' -i ' + parser.file[0] + ' -c copy'
        if parser.duration != 0:
            cmd = cmd + ' -t ' + str(parser.duration)
        cmd = cmd + ' ' + parser.output
        # execute command
        os.system(cmd)
    elif parser.operation == 'merge':
        # first convert them to mpegts
        i = 0
        tempFiles = []
        for f in parser.file:
            cmd = app + ' '
            tmpFile = 'temp' + str(i) + '.ts'
            tempFiles.append(tmpFile)
            cmd = cmd + '-i ' + f + ' -c copy -bsf:v h264_mp4toannexb -f mpegts ' + tmpFile
            os.system(cmd)
            print(cmd)
            i=i+1
        cmd = app + ' -i \"concat:' + tempFiles[0]
        i = 1
        while i< len(tempFiles):
            cmd = cmd + '|' + tempFiles[i]
            i=i+1
        cmd = cmd + '\"' + ' -c copy -bsf:a aac_adtstoasc ' + parser.output
        os.system(cmd)
        i=0
        while i< len(tempFiles):
            os.remove(tempFiles[i])
            i=i+1
        print(cmd)  
    else:
        print('Wrong operation. Valid operation is either cut/Merge')
args = parser.parse_args()
editMedia(args)
#print(args.file)