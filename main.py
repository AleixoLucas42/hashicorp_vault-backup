#!/bin/python
import requests, time, os, json
from tabulate import tabulate
from datetime import datetime
requests.packages.urllib3.disable_warnings()

# variables #
base_url=os.environ["VAULT_ADDR"]
vault_token=os.environ["VAULT_TOKEN"]
black_path_list=["cubbyhole/", "sys/", "identity/"]
backup_file_name=os.getenv("VAULT_BACKUP_FILE", "vault-backup.json")
payload = {}
headers = {
'Authorization': f"Bearer {vault_token}"
}
date_format = "%Y-%m-%d %H:%M:%S"
resume = [
    ("Vault address", os.environ["VAULT_ADDR"]),
    ("Blacklist path list", black_path_list),
    ("Backup filename", backup_file_name),
    ("Backup start time", datetime.now().strftime(date_format))
]
secret_list = {}

def send_get(api):
    return requests.request("GET", api, headers=headers, data=payload, verify=False)

def save_file_backup(path, secret):
    path=path.replace("metadata", "").replace("//", "/")
    print(f"[+] backing up item {path}")
    secret_list[path] = secret
    try:
        resume_bkp = open(backup_file_name, 'r').read()
    except:
        with open(backup_file_name, 'w') as bkp_file:
            bkp_file.close()
            resume_bkp = open(backup_file_name, 'r').read()
    with open(backup_file_name, 'w') as bkp_file:
        bkp_file.write(json.dumps(secret_list))

def get_secret_version(value):
    time.sleep(3)
    api = f"{base_url}/v1/{value}"
    response = send_get(api)
    get_secret_data(value, response.json()['data']['current_version'])

def get_secret_data(value, version):
    time.sleep(3)
    new_value = value.replace("meta", "")
    api = f"{base_url}/v1/{new_value}?version={version}"
    response = send_get(api)
    save_file_backup(value, response.json()['data']['data'])

def get_root_paths():
    root_paths=[]
    api = f"{base_url}/v1/sys/internal/ui/mounts"
    response = send_get(api)
    data = response.json()['data']['secret']
    for key in data.keys():
        if key not in black_path_list:
            root_paths.append(key)
    return root_paths

def is_dir(value):
    return "/" in value[len(value) - 1]

def get_sub_folder(value, is_root):
    time.sleep(3)
    if is_root:
        value=value+"metadata"
    api = f"{base_url}/v1/{value}?list=true"
    response = send_get(api)
    data = response.json()['data']['keys']
    for item in data:
        if is_dir(item):
            get_sub_folder(f"{value}/{item}", False)
        else:
            get_secret_version(f"{value}/{item}")

def main():
    print(tabulate(resume, tablefmt="fancy_grid"))
    if os.path.isfile(backup_file_name):
        print(f"[!] removing old file {backup_file_name}")
        os.remove(backup_file_name)
    for path in get_root_paths():
        print (f"[*] looking for secret in {path}")
        get_sub_folder(path, True)
    print(f"[*] backup finished at {datetime.now().strftime(date_format)}")

if __name__ == "__main__":
    main()