# Import library MQTT client untuk MicroPython (umqtt.simple)
from umqtt.simple import MQTTClient
import ujson           # Library JSON untuk MicroPython
import time            # Modul waktu
import machine         # Akses hardware (reset, penyebab reboot)
import gc              # Garbage collector
import socket          # Untuk resolusi DNS

import config          # File konfigurasi lokal

# Ambil konstanta dari file config
from config import (
    MQTT_BROKER,
    NODE_ID,
    HEARTBEAT_INTERVAL
)

# Fungsi untuk menjalankan tugas yang diterima dari cluster
from worker import run_task
# Fungsi untuk mengirim status sistem (RAM, uptime, dll.)
from system_monitor import send_system_status

# Modul koneksi WiFi
from connectionwifi import (
    connect_wifi,
    ensure_connection
)

# Modul pembaruan OTA (Over-The-Air)
import ota

# Coba impor modul LED; jika tidak ada, set flag LED_AVAILABLE = False
try:
    import led
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


# -------------------- Variabel Global --------------------
client = None             # Objek MQTTClient
last_heartbeat = 0        # Waktu terakhir heartbeat dikirim
last_gc = 0               # Waktu terakhir garbage collection dijalankan
GC_INTERVAL = config.GC_INTERVAL   # Interval GC dari config
mqtt_fail_count = 0       # Penghitung kegagalan koneksi MQTT berturut-turut


# =========================
# SAFE PUBLISH
# =========================

def safe_publish(topic, payload):
    """
    Melakukan publish MQTT dengan penanganan error.
    Jika publish gagal, exception akan diteruskan ke pemanggil
    agar loop utama bisa menangani (misalnya reconnect).
    """
    global client

    try:
        # Kirim pesan ke topik yang ditentukan
        client.publish(topic, payload)
    except Exception as e:
        print("Publish failed:", e)
        raise   # Lempar kembali exception agar ditangani di tempat lain


# =========================
# DNS RESOLVE SERVER
# =========================

def resolve_server():
    """
    Melakukan resolusi DNS untuk mendapatkan alamat IP server MQTT.
    Jika gagal sampai DNS_RESOLVE_RETRY kali, akan menggunakan fallback IP
    (jika disediakan) atau melemparkan RuntimeError.
    """
    for _ in range(config.DNS_RESOLVE_RETRY):
        try:
            # Dapatkan alamat IP dari nama host broker MQTT
            addr = socket.getaddrinfo(
                config.MQTT_BROKER,
                config.MQTT_PORT
            )[0][-1][0]
            print("Resolved server:", addr)
            return addr
        except Exception as e:
            print("DNS resolve failed:", e)
            # Jika ada IP fallback, langsung gunakan
            if config.SERVER_FALLBACK_IP:
                print("Using fallback IP")
                return config.SERVER_FALLBACK_IP
            time.sleep(config.DNS_RESOLVE_DELAY)

    # Semua upaya gagal, hentikan dengan error
    raise RuntimeError("Server resolve failed")


# =========================
# SAFE RESULT SEND
# =========================

def send_result(result):
    """
    Mengirim hasil eksekusi tugas ke topik cluster/result/<NODE_ID>.
    Jika payload terlalu besar, akan dipotong menjadi pesan error.
    """
    try:
        topic = "cluster/result/" + NODE_ID
        payload = ujson.dumps({
            "node": NODE_ID,
            "result": result
        })

        # Batasi ukuran payload sesuai konfigurasi
        if len(payload) > config.MQTT_MAX_PAYLOAD:
            print("Result too large")
            payload = ujson.dumps({
                "node": NODE_ID,
                "result": {
                    "status": "error",
                    "message": "result too large"
                }
            })

        safe_publish(topic, payload)

    except Exception as e:
        print("Send result error:", e)


# =========================
# TASK STATUS
# =========================

def send_task_status(task_id, status):
    """
    Mengirim status terbaru dari suatu tugas (task) ke topik
    cluster/task_status/<NODE_ID>.
    """
    try:
        payload = ujson.dumps({
            "node": NODE_ID,
            "task_id": task_id,
            "status": status,
            "timestamp": time.time()
        })
        topic = "cluster/task_status/" + NODE_ID
        safe_publish(topic, payload)
    except Exception as e:
        print("Task status error:", e)


# =========================
# READY STATE
# =========================

def set_ready_state():
    """
    Menandakan bahwa node siap menerima tugas baru.
    Mengirim status 'ready' ke topik cluster/status/<NODE_ID>
    dan menyalakan LED indikator jika tersedia.
    """
    try:
        payload = ujson.dumps({
            "node": NODE_ID,
            "status": "ready"
        })
        safe_publish("cluster/status/" + NODE_ID, payload)

        if LED_AVAILABLE:
            led.set_state(led.STATE_READY)   # LED mode siap

        print("Node READY")
    except Exception as e:
        print("Ready error:", e)


# =========================
# OTA UPDATE
# =========================

def handle_ota_command():
    """
    Menangani perintah pembaruan firmware OTA.
    Mode LED diubah ke STATE_OTA (jika ada) lalu memanggil ota.perform_update().
    """
    print("OTA command received")
    if LED_AVAILABLE:
        led.set_state(led.STATE_OTA)
    ota.perform_update()


# =========================
# MESSAGE CALLBACK
# =========================

def on_message(topic, msg):
    """
    Callback yang dipanggil setiap kali ada pesan MQTT masuk.
    Memeriksa topik: jika 'cluster/ota/update' -> jalankan OTA,
    jika 'cluster/task/<NODE_ID>' -> eksekusi tugas.
    Alur tugas: update status 'received', 'running', lalu jalankan run_task,
    kirim hasilnya, dan akhiri dengan status final. Setelah selesai,
    node kembali ke status 'ready'.
    """
    try:
        topic = topic.decode()

        # Cek apakah ini perintah OTA
        if topic == "cluster/ota/update":
            handle_ota_command()
            return

        # Cek apakah tugas untuk node ini
        if topic == "cluster/task/" + NODE_ID:
            print("Task received")
            data = ujson.loads(msg)
            task_id = data.get("task_id", "unknown")

            # Laporkan status 'received'
            send_task_status(task_id, "received")

            if LED_AVAILABLE:
                led.set_state(led.STATE_RUNNING)

            # Laporkan status 'running'
            send_task_status(task_id, "running")

            try:
                # Jalankan tugas yang diterima
                result = run_task(data)
            except Exception as e:
                # Jika tugas crash, tangkap dan buat pesan error
                print("Task crash:", e)
                result = {
                    "status": "error",
                    "message": str(e)
                }

            # Kirim hasil tugas
            send_result(result)

            # Tentukan status akhir (biasanya 'done' atau 'error')
            final_status = result.get("status", "done")
            send_task_status(task_id, final_status)

            # Kembalikan node ke status siap
            set_ready_state()

    except Exception as e:
        print("Task error:", e)
        send_task_status("unknown", "error")


# =========================
# REGISTER NODE
# =========================

def register_node():
    """
    Mendaftarkan node ke cluster dengan mengirim pesan ke topik
    'cluster/register'. Menandakan node online dan siap.
    """
    payload = ujson.dumps({
        "node": NODE_ID,
        "status": "online"
    })
    safe_publish("cluster/register", payload)


# =========================
# PERIODIC GC
# =========================

def periodic_gc():
    """
    Menjalankan pembersihan memori (garbage collection) secara berkala.
    Interval diatur oleh GC_INTERVAL. Menampilkan memori sebelum dan sesudah GC.
    """
    global last_gc

    now = time.time()
    if now - last_gc < GC_INTERVAL:
        return        # Belum waktunya GC

    last_gc = now

    try:
        before = gc.mem_free()
        gc.collect()
        after = gc.mem_free()
        print("GC:", before, "->", after)
    except Exception as e:
        print("GC error:", e)


# =========================
# MQTT CONNECT
# =========================

def connect_mqtt():
    """
    Menghubungkan ke broker MQTT. Jika gagal, mencoba kembali sesuai
    MQTT_RECONNECT_DELAY. Setelah berhasil, mengatur Last Will,
    subscribe topik tugas dan OTA, lalu mendaftarkan node sebagai online.
    Jika jumlah kegagalan mencapai MQTT_MAX_FAILURE, node akan reboot.
    """
    global client
    global mqtt_fail_count

    while True:
        try:
            print("Connecting MQTT...")
            server_ip = resolve_server()

            # Jika sudah ada koneksi sebelumnya, putuskan
            if client:
                try:
                    client.disconnect()
                except:
                    pass
                client = None

            gc.collect()

            # Buat objek MQTTClient
            client = MQTTClient(
                client_id=NODE_ID,
                server=server_ip,
                port=config.MQTT_PORT,
                keepalive=config.MQTT_KEEPALIVE
            )

            # Atur Last Will: jika koneksi terputus, node dilaporkan offline
            client.set_last_will(
                "cluster/status/" + NODE_ID,
                ujson.dumps({
                    "node": NODE_ID,
                    "status": "offline"
                }),
                retain=False,
                qos=0
            )

            client.set_callback(on_message)
            client.connect()

            # Subscribe topik perintah tugas & OTA
            client.subscribe("cluster/task/" + NODE_ID)
            client.subscribe("cluster/ota/update")

            print("MQTT connected:", server_ip)
            mqtt_fail_count = 0  # Reset penghitung kegagalan

            # Daftarkan node dan nyatakan siap
            register_node()
            set_ready_state()
            return

        except Exception as e:
            mqtt_fail_count += 1
            print("MQTT failed:", e)
            print("MQTT failure count:", mqtt_fail_count)

            # Jika terlalu banyak kegagalan, reboot
            if mqtt_fail_count >= config.MQTT_MAX_FAILURE:
                print("Too many MQTT failures — rebooting")
                time.sleep(config.REBOOT_DELAY)
                machine.reset()

            time.sleep(config.MQTT_RECONNECT_DELAY)


# =========================
# HEARTBEAT
# =========================

def send_heartbeat():
    """
    Mengirim heartbeat secara periodik sesuai HEARTBEAT_INTERVAL.
    Heartbeat berisi status 'online' node ke topik cluster/status/<NODE_ID>.
    Jika publish gagal, exception dilempar agar loop utama melakukan reconnect.
    """
    global last_heartbeat

    now = time.time()
    if now - last_heartbeat < HEARTBEAT_INTERVAL:
        return

    last_heartbeat = now

    try:
        payload = ujson.dumps({
            "node": NODE_ID,
            "status": "online"
        })
        safe_publish("cluster/status/" + NODE_ID, payload)
    except Exception as e:
        print("Heartbeat error:", e)
        raise


# =========================
# MAIN LOOP
# =========================

def main():
    """
    Fungsi utama yang dijalankan saat node dinyalakan.
    - Menampilkan penyebab reboot.
    - Menyalakan LED WiFi (jika ada) dan menghubungkan WiFi.
    - Mencoba update OTA di awal.
    - Menghubungkan ke MQTT.
    - Loop utama: jaga koneksi WiFi, ping MQTT, cek pesan masuk,
      kirim heartbeat, status sistem, dan lakukan GC periodik.
    """
    print("Booting node:", NODE_ID)

    try:
        cause = machine.reset_cause()
        print("Reset cause:", cause)
    except:
        pass

    if LED_AVAILABLE:
        led.set_state(led.STATE_WIFI)

    # Hubungkan ke WiFi
    connect_wifi()
    time.sleep(2)

    # Coba lakukan OTA update saat booting
    try:
        ota.perform_update()
    except Exception as e:
        print("OTA error:", e)

    # Koneksi awal ke MQTT
    connect_mqtt()

    # Loop utama
    while True:
        try:
            ensure_connection()          # Pastikan WiFi tetap terhubung
            client.ping()                # Jaga keep-alive MQTT
            client.check_msg()           # Proses pesan masuk (callback on_message)

            send_heartbeat()             # Kirim heartbeat berkala
            send_system_status(client)   # Kirim status sistem ke cluster
            periodic_gc()                # Pembersihan memori periodik

        except Exception as e:
            print("MQTT error:", e)
            time.sleep(2)
            connect_mqtt()               # Jika error, coba sambung ulang

        time.sleep(0.1)                  # Jeda kecil agar tidak membebani CPU

# Jalankan program utama
main()