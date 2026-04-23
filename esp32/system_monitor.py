# Import modul garbage collector, waktu, sistem file, hardware, dan JSON
import gc
import time
import os
import machine
import ujson

# Ambil ID node dari konfigurasi
from config import NODE_ID


# =========================
# CONFIG
# =========================

# Interval pengiriman laporan status sistem (detik)
MONITOR_INTERVAL = 15

# Ambang batas memori bebas dalam KB untuk peringatan rendah
MEMORY_WARNING_KB = 40
# Ambang batas kritis: jika memori bebas di bawah ini, node akan di-reset
MEMORY_CRITICAL_KB = 20

# Durasi sampling untuk estimasi penggunaan CPU (detik)
CPU_SAMPLE_TIME = 0.2


# Waktu terakhir laporan sistem dikirim (epoch)
last_report = 0


# =========================
# MEMORY
# =========================

def get_memory_info():
    """
    Mengambil informasi penggunaan memori RAM (heap).
    Menjalankan gc.collect() untuk hasil yang lebih akurat, lalu menghitung
    total, bebas, dan persentase penggunaan dalam KB.
    Mengembalikan dictionary dengan kunci free_kb, used_kb, percent.
    """
    gc.collect()                     # Bersihkan memori sebelum pengukuran

    free = gc.mem_free()             # Memori bebas dalam byte
    alloc = gc.mem_alloc()           # Memori terpakai dalam byte
    total = free + alloc

    free_kb = free // 1024           # Konversi ke KB
    used_kb = alloc // 1024
    percent = int((alloc / total) * 100)  # Persentase penggunaan

    return {
        "free_kb": free_kb,
        "used_kb": used_kb,
        "percent": percent
    }


# =========================
# CPU USAGE (approx)
# =========================

def get_cpu_usage():
    """
    Estimasi penggunaan CPU dengan metode loop sibuk:
    Menjalankan loop penghitung selama CPU_SAMPLE_TIME detik,
    lalu menghitung persentase berdasarkan jumlah iterasi vs waktu yang diharapkan.
    Hasil dibatasi maksimal 100%.
    """
    start = time.ticks_ms()
    busy = 0

    end_time = start + int(CPU_SAMPLE_TIME * 1000)   # Batas akhir dalam ms

    while time.ticks_ms() < end_time:
        busy += 1

    elapsed = time.ticks_diff(time.ticks_ms(), start)

    # Estimasi kasar persentase: busier loop = lebih banyak waktu CPU idle
    percent = int((busy / (elapsed * 10)) * 100)
    if percent > 100:
        percent = 100

    return percent


# =========================
# FLASH STORAGE
# =========================

def get_flash_usage():
    """
    Membaca penggunaan penyimpanan flash (filesystem) menggunakan os.statvfs.
    Menghitung total, bebas, dan persentase penggunaan dalam KB.
    Mengembalikan dictionary, atau nilai nol jika terjadi error (misal tidak ada filesystem).
    """
    try:
        stat = os.statvfs("/")
        block_size = stat[0]          # Ukuran blok
        total_blocks = stat[2]        # Total blok
        free_blocks = stat[3]         # Blok bebas

        total = block_size * total_blocks
        free = block_size * free_blocks
        used = total - free

        total_kb = total // 1024
        free_kb = free // 1024
        percent = int((used / total) * 100)

        return {
            "total_kb": total_kb,
            "free_kb": free_kb,
            "percent": percent
        }
    except Exception:
        # Jika statvfs gagal (misal tidak didukung), kembalikan nol
        return {
            "total_kb": 0,
            "free_kb": 0,
            "percent": 0
        }


# =========================
# TEMPERATURE
# =========================

def get_temperature():
    """
    Membaca suhu chip (jika didukung hardware) dalam derajat Celsius.
    Mengembalikan integer, atau -1 jika tidak tersedia.
    """
    try:
        temp = machine.temperature()
        return int(temp)
    except Exception:
        return -1


# =========================
# SYSTEM STATUS
# =========================

def get_system_status():
    """
    Mengumpulkan semua metrik sistem menjadi satu dictionary:
    memori, CPU, penyimpanan flash, dan suhu.
    """
    mem = get_memory_info()
    cpu = get_cpu_usage()
    flash = get_flash_usage()
    temp = get_temperature()

    return {
        "memory_free_kb": mem["free_kb"],
        "memory_used_kb": mem["used_kb"],
        "memory_percent": mem["percent"],

        "cpu_percent": cpu,

        "flash_total_kb": flash["total_kb"],
        "flash_free_kb": flash["free_kb"],
        "flash_percent": flash["percent"],

        "temperature": temp
    }


# =========================
# SEND STATUS
# =========================

def send_system_status(client):
    """
    Mengirim laporan status sistem ke broker MQTT pada topik
    'cluster/progress/<NODE_ID>' jika interval MONITOR_INTERVAL telah terlewati.
    Juga mencetak status ke konsol.
    Memberikan peringatan jika memori bebas rendah, dan me-reset node jika
    memori bebas di bawah MEMORY_CRITICAL_KB.
    """
    global last_report

    now = time.time()
    # Lewati jika belum waktunya mengirim
    if now - last_report < MONITOR_INTERVAL:
        return

    last_report = now

    try:
        status = get_system_status()

        # Susun payload JSON untuk MQTT
        payload = {
            "node": NODE_ID,
            "stage": "system",
            "progress": status["memory_percent"],      # Gunakan persen memori sebagai progress

            "memory_free_kb": status["memory_free_kb"],
            "memory_used_kb": status["memory_used_kb"],
            "cpu_percent": status["cpu_percent"],
            "flash_free_kb": status["flash_free_kb"],
            "flash_percent": status["flash_percent"],
            "temperature": status["temperature"]
        }

        # Hanya publish jika client MQTT tersedia
        if client is not None:
            client.publish(
                "cluster/progress/" + NODE_ID,
                ujson.dumps(payload)
            )

        print("SYSTEM:", payload)

        # Peringatan memori rendah
        if status["memory_free_kb"] < MEMORY_WARNING_KB:
            print("WARNING: Low memory")

        # Jika memori kritis, lakukan reset untuk mencegah crash lebih parah
        if status["memory_free_kb"] < MEMORY_CRITICAL_KB:
            print("CRITICAL: Memory exhausted")
            machine.reset()

    except Exception as e:
        print("System monitor error:", e)