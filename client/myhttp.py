import pycurl
from io import BytesIO
import json

def get(url):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEFUNCTION, buffer.write)
    c.perform()
    status = c.getinfo(pycurl.HTTP_CODE)
    c.close()
    return (status, buffer.getvalue().decode())
