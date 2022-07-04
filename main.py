import requests

def runcmd(command):
    resp = requests.post("https://ig-api-proxy.herokuapp.com/service", data={"auth": "0b845a09dd890f71bd8f6ae99a74573f", "command": command})
    if resp.json().get("status", "error") == "success":
        print(str(resp.json()["output"]))

command1 = "login:igapitest1,0x369CF"
runcmd(command1)