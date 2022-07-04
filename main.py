import requests
import api

def run_with_proxy(command):
    resp = requests.post("https://instagram-automation-sand.vercel.app/service", data={"auth": "0b845a09dd890f71bd8f6ae99a74573f", "command": command})
    if resp.json().get("status", "error") == "success":
        print(str(resp.json()["stdout"]))

username = "igapitest1"
pwd = "0x369CF"

command1 = {
    "function": "login", 
    "kwargs": {"username": username, "pwd": pwd}
}
command2 = {
    "function": "get_followers", 
    "kwargs": {"username": "tom.barnes1_"}
}

api.execute(command1)
#proxy.execute()