# Ransomware Simulation with Detection and Response

A cybersecurity project that simulates ransomware effects with implementation of a detection system and automated response measures.

## Description

This project was developed for educational purposes to demonstrate how a ransomware typically behaves and how it can be detected and contained through automated network-monitoring systems. It includes files encryption and exfiltration and anomaly detection capabilities.

## Main Scripts

#### `httpGen.py`
It generates HTTP requests to simulate client-server communications seen as standard traffic. Given the server URL it starts generating requests, with an interval between requests equalt to a random value between 80% and 120% of the interval parameter, for the entire duration value. 

It takes the following parameters as input:
- Server URL
- Duration of the script execution (in seconds, default value = 60 seconds)
- Interval between requests (in seconds, default value = 4)

#### `fakeFilesGen.py`
Fake file generator to create a safe testing environment. 
Given the folder path, it generates a given number of files of random extensions between .txt, .csv, .pdf, .png, .jpg. The .pdf, .png, .jpg have random dimensions between 256 bytes and 10MB while the other have just random content.

It takes the following parameters as input:
- Folder's path
- Number of files (default value = 20)

#### `server.py`
Local server on port 8080 that, once started, opens the endpoint "/status" waiting for file exfiltration. The received files are stored inside the /upload/agent-id folder. 

#### `ransomware.py`
Main script that simulates ransomware behavior. Given the target folder's path, it generates a secretkey for the file encryption and for each file executes the two operations of exfiltration and encryption following this specific order.
The secretkey used for encrypting the files is also exfiltrated to the attacker.

It takes the following parameter as input:
- Target folder's path

Its functionalities include:
- File encryption of a target directory
- File exfiltration to the attacker server

### Cloud Functions

The `Cloud Functions` folder contains the Python script used on the GPC cloud function `firewall_automation` for the detection & response system.

It executes the BigQuery SQL query to detect any anomaly was found. It scans the last 4 minutes logs, grouped in 1-minute windows by source VM, destination VM and destination port, and if any log is detected more than the threshold value of 5 times, it returns the identied anomaly.

Once anomalies are detected, a deny egress firewall rules is created along with the identified source instance shutdown for each of them.

Its functionalities include:
- Monitoring suspicious activities
- Detection of file exfiltration
- Automated threat response measures

## Configuration

For this project 5 virtual machines instances of Google Cloud Platform were used:
- bastion-vm (entry point)
- victim-vm
- attacker-vm
- client1-vm
- client2-vm

`httpGen.py` script on client1-vm, client2-vm, victim-vm

`server.py` script on attacker-vm

`fakeFilesGen.py` script on victim-vm

`ransomware.py` script on victim-vm

## Usage

1. **Generate 250 fake files for testing:**

On victim-vm:
```bash
mkdir files
python3 fakeFilesGen.py --target files --amount 250
```

2. **Generate Standard Traffic**

Start a server in backgroud and logs the output into the http.log file on both client1-vm and client2-vm:

```bash
nohup python3 -m http.server 8080 > http.log 2>&1 &
```
Run the generator script in background on client1-vm, client2-vm, victim-vm.

From x to y:
```bash
nohup python3 -u httpGen.py --url [server-url-of-y] --interval 10.0 --duration 1200 >
http.log 2>&1 &
```

3. **Run the exfiltration server:**
On attacker-vm install a Python virtual environment:
```bash
sudo apt install -y python3-pip python3-venv
```
Activate it and install the required dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install flask
```
Run the script in background:
```bash
nohup python3 server.py > http.log 2>&1 &
```

4. **Execute the ransomware:**
On victim-vm install a Python virtual environment:
```bash
sudo apt install -y python3-pip python3-venv
```
Activate it and install the required dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install cryptography requests
```
Run the script:
```bash
python3 ransomware.py --target files
```

## 📝 License

This project is distributed under the MIT License. See the `LICENSE` file for more details.

## 👨‍💻 Author

**Alessandro Modelli**
- GitHub: [@alessandromodelli](https://github.com/alessandromodelli)

## ⚖️ Legal Disclaimer

This software is provided exclusively for educational and cybersecurity research purposes. The author assumes no responsibility for the improper, illegal, or harmful use of this code. It is the user's responsibility to ensure they have all necessary permissions before using this software and to comply with all applicable cybersecurity laws.

The use of this software for illegal activities is strictly prohibited and may result in serious legal consequences.
