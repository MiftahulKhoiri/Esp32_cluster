## ESP32 CLUSTER SERVER — README

Panduan lengkap menjalankan Server Cluster ESP32.

Dokumen ini disusun untuk penggunaan nyata sehari-hari.

Anda bisa langsung:

- install
- start server
- connect node
- upload program
- upload dataset
- start training
- mendapatkan hasil

Tanpa perlu coding tambahan.

---

Arsitektur Sistem

ESP32 Node
     │
     ▼
MQTT Broker (Mosquitto)
     │
     ▼
Cluster Server
     │
 ┌───────────────┬───────────────┐
 │               │               │
Coordinator   OTA Server     Database

---

Requirement

Minimal:

Python 3.8+

Support:

Linux
Raspberry Pi
Termux

---

STEP 1 — Install Dependency

Linux / Raspberry

sudo apt update
sudo apt upgrade

sudo apt install python3
sudo apt install python3-pip
sudo apt install mosquitto
sudo apt install avahi-daemon

---

Termux

pkg update
pkg upgrade

pkg install python
pkg install mosquitto
pkg install avahi

---

STEP 2 — Install Python Library

Masuk ke folder project:

cd cluster

Install dependency:

pip install -r requirements.txt

Dependency yang digunakan:

- paho-mqtt
- flask

Sesuai file requirements server Anda.

---

STEP 3 — Set Hostname Server

Hostname wajib:

cluster-server

Linux / Raspberry:

sudo hostnamectl set-hostname cluster-server

---

STEP 4 — Jalankan mDNS

Agar node bisa connect menggunakan:

cluster-server.local

Start:

avahi-daemon --daemonize

Test:

ping cluster-server.local

Jika berhasil:

192.168.x.x

---

STEP 5 — Jalankan MQTT Broker

Terminal 1:

mosquitto -v

Output normal:

Opening ipv4 listen socket on port 1883

---

STEP 6 — Jalankan Server

Terminal 2:

python server_start.py

Service yang akan otomatis berjalan:

- OTA server
- Coordinator
- Database
- MQTT client
- Watchdog

Karena launcher server memang menjalankan OTA dan coordinator dalam thread terpisah.

---

Output Normal Saat Server Start

=== CLUSTER SERVER START ===

Starting OTA server...
Starting coordinator...

Database initialized
Coordinator started

All services started

Server akan menampilkan banner status sistem saat start.

---

STEP 7 — Nyalakan Node ESP32

Saat node berhasil connect:

Node ready: node1
Node ready: node2

---

Cek Node Aktif

Di terminal server:

nodes

Output:

Nodes:
  - node1
  - node2

Command ini tersedia di CLI server.

---

STEP 8 — Upload Program ke Node

Di terminal server:

1

Artinya:

upload_program

Server akan:

menampilkan daftar file program

Contoh:

1. train.py
2. inference.py

Pilih nomor:

1

Server akan mengirim program ke semua node.

---

Folder Program

Letakkan file program di:

programs/

Contoh:

programs/
   train.py

---

STEP 9 — Upload Dataset

Di terminal server:

2

Artinya:

upload_file

Server akan:

split dataset
kirim ke setiap node

Karena sistem membagi file otomatis per node.

---

Folder Dataset

Letakkan dataset di:

data/

Contoh:

data/
   dataset.csv

---

STEP 10 — Training Otomatis Dimulai

Setelah dataset selesai dikirim:

Node otomatis training

Tidak perlu command tambahan.

---

Manual Start Training

Jika ingin manual:

3

Artinya:

start_train

Server akan membuat task training baru.

---

Monitor Progress

Server akan menampilkan:

Progress node1: 10%
Progress node1: 20%
Progress node2: 30%

---

STEP 11 — Hasil Training

File hasil otomatis disimpan di:

cli/hasil/

Contoh:

final_result.csv

Karena server akan merge semua result dari node.

---

COMMAND LIST

Di terminal server:

help

Output:

[0] exit
[1] upload_program
[2] upload_file
[3] start_train
[4] ota
[5] status
[6] nodes
[7] tasks

Semua command ini memang tersedia di command listener server.

---

COMMAND PALING SERING DIPAKAI

1  upload program
2  upload dataset
3  start training
6  lihat node
7  lihat task
0  exit

---

OTA Update Firmware

Command:

4

Server akan:

kirim OTA command
node download firmware
node restart

---

Shutdown Server

Tekan:

CTRL + C

Server akan:

stop service
disconnect MQTT
shutdown clean

Karena server menggunakan signal handler untuk shutdown.

---

Workflow Harian (Singkat)

Start MQTT
Start Server
Nyalakan Node
Upload Program
Upload Dataset
Training
Result

---

Workflow Real Example

mosquitto -v

python server_start.py

Kemudian:

nodes

1
pilih train.py

2
pilih dataset.csv

Tunggu:

Training selesai

Hasil:

cli/hasil/final_result.csv

---

Debug Jika Node Tidak Connect

Cek hostname:

ping cluster-server.local

Cek MQTT:

netstat -tulnp | grep 1883

Cek OTA:

netstat -tulnp | grep 8000

---

Status Sistem

Cluster ready
Auto training ready
OTA ready
Production ready