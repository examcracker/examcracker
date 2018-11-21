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

# Commands
command_start = 0
command_stop = 1

# Status
status_start_success = 0
status_capture_started = 1
status_no_capture_started = 2
status_camera_not_detected = 3
status_stop_success = 4
