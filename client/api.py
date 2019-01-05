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
command_upload_logs = 2
command_get_recent_capture_file_details = 3
command_upload_file = 4
command_check_client_active = 5

# Status
status_start_success = 0
status_capture_started = 1
status_no_capture_started = 2
status_camera_not_detected = 3
status_stop_success = 4
status_upload_sucess = 5
status_upload_fail = 6
status_client_active = 7
