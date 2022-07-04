import requests

def runcmd(command):
    resp = requests.post("http://localhost:5000/service", data={"auth": "0b845a09dd890f71bd8f6ae99a74573f", "command": command})
    if resp.json().get("status", "error") == "success":
        print(str(resp.json()["output"]))

command1 = 'login:"tom.barnes1_","qdh5ykmtDrpjf4phPskLnx4k"'
command2 = 'get_following:"tom.barnes1_"'
runcmd(command1)
runcmd(command2)