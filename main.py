import api
import sys

if __name__ == "__main__" and "--local" in sys.argv:
    username = input("Enter username: ")
    pwd = input("Enter password: ")
    resp = api.execute_via_proxy({"function": "login", "kwargs": {"username": username, "pwd": pwd}})
    print(resp)

    #resp = execute({"function": "userinfo", "kwargs": {"username": "tom.barnes1_"}, "fields": ["is_private"]})
    #pprint(resp, indent=2)
