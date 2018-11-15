import enum

'''
JSON structure of request/response

Start Request
{
    "command" : start,
    "chapterid" : chapter_id
}

Response
{
    "status" : success
}

Stop Request
{
    "command" : stop,
}

Response
{
    "command" : success
}
'''

class Command(enum.Enum):
    start = 0
    stop = 1

class Status(enum.Enum):
    success = 0
    capture_started = 1
    no_capture_started = 2
    camera_not_detected = 3
