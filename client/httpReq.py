import requests
  
def send(myurl, endpoint, jsonObj):
    myurl = myurl + endpoint
    print(myurl)
    print(jsonObj)
    r = requests.get(myurl, data = jsonObj)
    print(r.status_code, r.reason)
    return r

def post(myurl, endpoint, jsonObj):
    myurl = myurl + endpoint
    print(myurl)
    print(jsonObj)
    r = requests.post(url = myurl, data = jsonObj)
    print(r.status_code, r.reason)
    return r

