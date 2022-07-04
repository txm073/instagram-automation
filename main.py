import requests

def runcmd(command):
    resp = requests.post("https://instagram-automation-sand.vercel.app/service", data={"auth": "0b845a09dd890f71bd8f6ae99a74573f", "command": command})
    print(resp.json())
    if resp.json().get("status", "error") == "success":
        print(str(resp.json()["stdout"]))

command1 = "login:igapitest1,0x369CF"
runcmd(command1)