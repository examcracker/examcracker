import requests
endpoint = "/cdn/saveClientSession/"
  
def send(myurl, jsonObj):
    myurl = myurl + endpoint
    print(myurl)
    print(jsonObj)
    r = requests.get(url = myurl, data = jsonObj)
    #print(r.text)
