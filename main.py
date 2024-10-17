#!/bin/python
import requests, time, os, json
from tabulate import tabulate
from datetime import datetime

requests.packages.urllib3.disable_warnings()

# variables #
base_url = os.environ["VAULT_ADDR"]
vault_token = os.environ["VAULT_TOKEN"]
black_path_list = ["cubbyhole/", "sys/", "identity/"]
backup_file_name = os.getenv("VAULT_BACKUP_FILE", "vault-backup.json")
payload = {}
headers = {"Authorization": f"Bearer {vault_token}"}
date_format = "%Y-%m-%d %H:%M:%S"
resume = [
    ("Vault address", os.environ["VAULT_ADDR"]),
    ("Blacklist path list", black_path_list),
    ("Backup filename", backup_file_name),
    ("Restore filename", os.getenv("VAULT_RESTORE_FILE", "None")),
    ("Start time", datetime.now().strftime(date_format)),
]
secret_list = {}


def send_get(api):
    return requests.request("GET", api, headers=headers, data=payload, verify=False)


def save_file_backup(path, secret):
    path = path.replace("metadata", "").replace("//", "/")
    print(f"[+] backing up item {path}")
    secret_list[path] = secret
    try:
        resume_bkp = open(backup_file_name, "r").read()
    except:
        with open(backup_file_name, "w") as bkp_file:
            bkp_file.close()
            resume_bkp = open(backup_file_name, "r").read()
    with open(backup_file_name, "w") as bkp_file:
        bkp_file.write(json.dumps(secret_list, indent=4))


def get_secret_version(value):
    time.sleep(3)
    api = f"{base_url}/v1/{value}"
    response = send_get(api)
    get_secret_data(value, response.json()["data"]["current_version"])


def get_secret_data(value, version):
    time.sleep(3)
    new_value = value.replace("meta", "")
    api = f"{base_url}/v1/{new_value}?version={version}"
    response = send_get(api)
    save_file_backup(value, response.json()["data"]["data"])


def get_root_paths():
    root_paths = []
    api = f"{base_url}/v1/sys/internal/ui/mounts"
    response = send_get(api)
    data = response.json()["data"]["secret"]
    for key in data.keys():
        if key not in black_path_list:
            root_paths.append(key)
    return root_paths


def is_dir(value):
    return "/" in value[len(value) - 1]


def get_sub_folder(value, is_root):
    time.sleep(3)
    if is_root:
        value = value + "metadata"
    api = f"{base_url}/v1/{value}?list=true"
    response = send_get(api)
    data = response.json()["data"]["keys"]
    for item in data:
        if is_dir(item):
            get_sub_folder(f"{value}/{item}", False)
        else:
            get_secret_version(f"{value}/{item}")


def create_secret(kv_path, kv_value):
    url = f"{base_url}/v1/kv/data/{kv_path}"
    payload = json.dumps({"data": kv_value})
    try:
        print(f"[+] restoring {kv_path}")
        requests.request("POST", url, headers=headers, data=payload)
    except Exception as e:
        print(f"[!] some error ocurred while processing {kv_path}")
        print(e)


def restore():
    print(tabulate(resume, tablefmt="fancy_grid"))
    restore_file = os.environ["VAULT_RESTORE_FILE"]
    with open(restore_file, "r") as file:
        passwords = json.load(file)
        for key, value in passwords.items():
            create_secret(key.replace("kv/", ""), value)
    print("[*] restoring done")
    exit(0)


def main():
    print(tabulate(resume, tablefmt="fancy_grid"))
    if os.path.isfile(backup_file_name):
        print(f"[!] removing old file {backup_file_name}")
        os.remove(backup_file_name)
    for path in get_root_paths():
        print(f"[*] looking for secret in {path}")
        get_sub_folder(path, True)
    os.chmod(backup_file_name, 0o400)
    print(f"[*] backup finished at {datetime.now().strftime(date_format)}")


if __name__ == "__main__":
    if "VAULT_RESTORE_FILE" in os.environ:
        restore()
    main()
