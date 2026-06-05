# HASHICORP VAULT BACKUP
This script back up the **key value (Kv)** in hashicorp vault to a txt file

## Software Validation
| Vault version | Docker version | Python version | Operational system | Test result        |
|---------------|----------------|----------------| -------------------|--------------------|
| 1.15.6        | 25.0.3         | 3.11.8         | Arch linux         | :white_check_mark: |
| 1.15.6        | 24.0.5         | 3.8.10         | Ubuntu 22.04       | :white_check_mark: |

## Environment variables
| Name | Example | Description |
|-------------------|--------------------------------|------------------|
| VAULT_ADDR        | https://vault.yourinstance.lab | Vault address    |
| VAULT_TOKEN       | hvs.qwertyqwertyqwertyqwerty   | Your vault token |
| VAULT_BACKUP_FILE | vault-file-backup.json         | Output file name (optional)|
| VAULT_RESTORE_FILE| vault-file-backup.json         | File to restore (mandatory if you are restoring) |
| VAULT_BLACKLIST_PATHS | cubbyhole/,sys/,identity/ | Paths to ignore during backup (optional, comma-separated) |
| VAULT_SLEEP_SECONDS | 1.0 | Sleep interval used in the backup flow (optional) |

## Example backup with docker
This will create the output file on your actual directory
```bash
docker run \
    -v $PWD:/opt/vaultbackup \
    -e VAULT_ADDR="https://vault.yourinstance.lab" \
    -e VAULT_TOKEN="hvs.qwertyqwertyqwerty" \
    aleixolucas/hashicorpvault-backup
```
## Example restore with docker
You must enable kv engine first
```bash
docker run \
    -v $PWD:/opt/vaultbackup \
    -e VAULT_ADDR="https://vault.yourinstance.lab" \
    -e VAULT_TOKEN="hvs.qwertyqwertyqwerty" \
    -e VAULT_RESTORE_FILE="vault-file-backup.json"
    aleixolucas/hashicorpvault-backup
```

## Run script with python3
```bash
pip3 install -r requirements.txt
export VAULT_ADDR=https://vault.yourinstance.lab
export VAULT_TOKEN=hvs.qwertyqwertyqwerty
# export VAULT_RESTORE_FILE=vault-file-backup.json
python3 main.py
```

## Run in Kubernetes
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: vault-backup
  namespace: hashicorp-vault
spec:
  schedule: "0 3 * * *"
  concurrencyPolicy: Forbid
  startingDeadlineSeconds: 300
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: vault-backup
              image: aleixolucas/hashicorpvault-backup:latest
              imagePullPolicy: IfNotPresent
              env:
                - name: VAULT_ADDR
                  value: "https://vault.yourinstance.lab/"
                - name: VAULT_TOKEN
                  value: "hvs.qwertyqwertyqwerty"
                - name: VAULT_SLEEP_SECONDS
                  value: "5"
                - name: VAULT_BACKUP_FILE
                  value: "/app/backups/vault-backup.json"
              volumeMounts:
                - name: backup-storage
                  mountPath: /app/backups
          volumes:
            - name: backup-storage
              hostPath:
                path: /mnt/vault-backups
                type: DirectoryOrCreate
```

## FAQ
- You can make the script place the back up file to a specific folder, but make sure this folder already exists.
- Some environment variables are required.
- The environment where you are running the backup must to have access on your vault address.
- The script will only back up the key values that your token have access.
- If you are runnig with docker, you shall have docker installed.
- If you are running with python, make sure you have python3 installed.
- You can modify the source and rebuild the docker image as you need.
- The script changes the file permission to 400, so if you are runnig with cronjob, pay attention on the file owner.
