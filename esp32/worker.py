import time
import os
import sys
import ujson
import machine
import gc

# =========================
# BASE64 COMPAT
# =========================

# Dekoder Base64 yang kompatibel: mendukung ubinascii (MicroPython) atau base64 standar
try:
    import ubinascii as _b64
    def b64decode(data):
        """Decode string Base64 menjadi bytes menggunakan ubinascii (MicroPython)."""
        return _b64.a2b_base64(data)
except ImportError:
    import base64 as _b64
    def b64decode(data):
        """Decode string Base64 menjadi bytes menggunakan modul base64 standar."""
        return _b64.b64decode(data)


# Coba impor modul LED, jika gagal set LED_AVAILABLE = False
try:
    import led
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False


# =========================
# CONFIG
# =========================

# Direktori untuk menyimpan program (skrip Python)
PROGRAM_DIR = "programs"
# Direktori untuk menyimpan data (dataset, file chunk, dll.)
DATA_DIR = "data"

# Timeout default untuk request (detik)
DEFAULT_TIMEOUT = 10
# Timeout untuk proses training yang lebih lama (detik)
TRAINING_TIMEOUT = 300

# Ambang batas minimum ruang kosong flash (KB) sebelum menolak penulisan
MIN_FREE_SPACE_KB = 100


# =========================
# DISK SPACE CHECK
# =========================

def get_free_space_kb():
    """
    Mengecek ruang kosong pada filesystem root ('/') dalam satuan KB.
    Mengembalikan jumlah KB bebas, atau 0 jika gagal.
    """
    try:
        stat = os.statvfs("/")
        block_size = stat[0]        # Ukuran blok
        free_blocks = stat[3]       # Jumlah blok bebas
        free_bytes = block_size * free_blocks
        return free_bytes // 1024   # Konversi ke KB
    except Exception as e:
        print("Disk check error:", e)
        return 0


# =========================
# ATOMIC WRITE
# =========================

def atomic_write(path, data, mode="wb"):
    """
    Menulis data ke file secara atomik menggunakan file temporer.
    Pertama data ditulis ke path + ".tmp", lalu jika berhasil file asli diganti.
    Ini mencegah kerusakan file jika terjadi kegagalan di tengah penulisan.
    Mengembalikan True jika berhasil, False jika gagal.
    """
    temp_path = path + ".tmp"

    try:
        with open(temp_path, mode) as f:
            f.write(data)
            try:
                f.flush()           # Pastikan tertulis ke flash
            except:
                pass

        # Jika file asli sudah ada, hapus dulu
        if path in os.listdir():
            os.remove(path)

        # Ganti nama file temporer menjadi file asli
        os.rename(temp_path, path)
        return True

    except Exception as e:
        print("Atomic write error:", e)
        # Bersihkan file temporer jika ada
        try:
            if temp_path in os.listdir():
                os.remove(temp_path)
        except:
            pass
        return False


# =========================
# INIT DIRECTORIES
# =========================

def init_directories():
    """
    Memastikan direktori PROGRAM_DIR dan DATA_DIR sudah ada.
    Jika belum, buat direktori tersebut.
    """
    if PROGRAM_DIR not in os.listdir():
        os.mkdir(PROGRAM_DIR)
    if DATA_DIR not in os.listdir():
        os.mkdir(DATA_DIR)


# =========================
# PROGRESS
# =========================

def send_progress(stage, percent):
    """
    Mengirim laporan progres task ke broker MQTT pada topik 'cluster/progress/<NODE_ID>'.
    Tidak melakukan apa-apa jika client MQTT belum tersedia (import dari main).
    """
    try:
        from config import NODE_ID
        from main import client

        if client is None:
            return

        payload = {
            "node": NODE_ID,
            "stage": stage,
            "progress": percent
        }

        client.publish(
            "cluster/progress/" + NODE_ID,
            ujson.dumps(payload)
        )
    except Exception as e:
        print("Progress error:", e)


# =========================
# MODULE RELOAD
# =========================

def reload_module(module_name):
    """
    Memuat ulang modul Python dengan menghapusnya dari sys.modules
    dan menjalankan garbage collector. Berguna untuk menerapkan
    program yang baru diunggah tanpa restart.
    """
    if module_name in sys.modules:
        print("Reloading:", module_name)
        del sys.modules[module_name]
        gc.collect()


# =========================
# META FILE
# =========================

def get_meta_filename(filename):
    """
    Membentuk nama file meta untuk upload chunked: <filename>.meta
    """
    return filename + ".meta"


def get_meta_path(filename):
    """
    Mengembalikan path lengkap file meta di dalam DATA_DIR.
    """
    return DATA_DIR + "/" + get_meta_filename(filename)


def load_last_chunk(filename):
    """
    Membaca indeks chunk terakhir yang sudah diterima dari file meta.
    Jika file meta tidak ada, kembalikan 0.
    """
    meta_file = get_meta_filename(filename)

    if meta_file not in os.listdir(DATA_DIR):
        return 0

    path = get_meta_path(filename)
    try:
        with open(path, "r") as f:
            meta = ujson.loads(f.read())
            return meta.get("last_chunk", 0)
    except Exception as e:
        print("Meta load error:", e)
        return 0


def save_last_chunk(filename, chunk):
    """
    Menyimpan indeks chunk terakhir yang berhasil diterima ke file meta.
    """
    path = get_meta_path(filename)
    data = ujson.dumps({
        "last_chunk": chunk
    })
    atomic_write(path, data)


def clear_meta(filename):
    """
    Menghapus file meta setelah semua chunk berhasil diterima.
    """
    meta_file = get_meta_filename(filename)
    try:
        if meta_file in os.listdir(DATA_DIR):
            os.remove(get_meta_path(filename))
    except Exception as e:
        print("Meta clear error:", e)


# =========================
# WATCHDOG
# =========================

def start_watchdog():
    """
    Menginisialisasi hardware watchdog timer (WDT) dengan timeout
    sesuai TRAINING_TIMEOUT. Jika gagal (misal tidak mendukung),
    fallback ke timeout 120 detik. Mengembalikan objek WDT.
    """
    try:
        timeout_ms = TRAINING_TIMEOUT * 1000
        return machine.WDT(timeout=timeout_ms)
    except Exception:
        print("WDT fallback to 120s")
        return machine.WDT(timeout=120000)


# =========================
# MAIN TASK
# =========================

def run_task(data):
    """
    Fungsi utama yang dipanggil saat node menerima tugas dari cluster.
    Memeriksa tipe tugas (upload_program, upload_chunk, atau train)
    dan mendelegasikan ke handler yang sesuai.
    Mengembalikan dictionary hasil eksekusi.
    """
    init_directories()

    try:
        if LED_AVAILABLE:
            led.set_state(led.STATE_RUNNING)

        task_type = data.get("type")

        if task_type == "upload_program":
            return handle_upload_program(data)
        elif task_type == "upload_chunk":
            return handle_upload_chunk(data)
        elif task_type == "train":
            return handle_training(data)
        else:
            return {
                "status": "error",
                "message": "Unknown task"
            }

    except Exception as e:
        print("Task error:", e)
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        if LED_AVAILABLE:
            led.set_state(led.STATE_READY)


# =========================
# UPLOAD PROGRAM
# =========================

def handle_upload_program(task):
    """
    Menangani unggahan program Python lengkap (bukan chunked).
    Mendecode data Base64, memeriksa ruang disk,
    menulis file ke PROGRAM_DIR, lalu memuat ulang modul.
    """
    filename = task.get("filename")
    data_base64 = task.get("data")

    send_progress("upload_program", 0)

    path = PROGRAM_DIR + "/" + filename

    # Decode base64
    try:
        data = b64decode(data_base64)
    except Exception as e:
        print("Decode error:", e)
        return {
            "status": "error",
            "message": "decode failed"
        }

    # Periksa ketersediaan ruang (sediakan margin 10 KB)
    free_kb = get_free_space_kb()
    required_kb = len(data) // 1024 + 10
    if free_kb < required_kb or free_kb < MIN_FREE_SPACE_KB:
        print("Disk full")
        return {
            "status": "error",
            "message": "disk full"
        }

    # Tulis file secara atomik
    if not atomic_write(path, data):
        return {
            "status": "error",
            "message": "write failed"
        }

    # Muat ulang modul jika sebelumnya pernah diimpor
    module_name = filename.replace(".py", "")
    reload_module(module_name)

    send_progress("upload_program", 100)
    print("Program saved:", filename)

    return {
        "status": "program_updated"
    }


# =========================
# UPLOAD CHUNK
# =========================

def handle_upload_chunk(task):
    """
    Menangani unggahan file potongan (chunk) untuk file besar.
    Setiap chunk memiliki indeks, dan total chunk. Menyimpan data
    ke DATA_DIR, melacak progres di file meta. Jika chunk terakhir
    dan auto_train=True, langsung panggil handle_training.
    """
    filename = task.get("filename")
    chunk_index = task.get("chunk_index")
    total_chunks = task.get("total_chunks")
    auto_train = task.get("auto_train", False)

    # Baca indeks chunk terakhir yang sudah ada
    last_chunk = load_last_chunk(filename)

    # Jika chunk ini sudah pernah diterima, lewati (idempotent)
    if chunk_index <= last_chunk:
        print("Skip chunk", chunk_index)
        return {
            "status": "skip"
        }

    # Decode data Base64
    try:
        data = b64decode(task.get("data"))
    except Exception as e:
        print("Decode error:", e)
        return {
            "status": "error"
        }

    # Periksa ruang disk
    free_kb = get_free_space_kb()
    required_kb = len(data) // 1024 + 10
    if free_kb < required_kb or free_kb < MIN_FREE_SPACE_KB:
        print("Disk full during chunk")
        return {
            "status": "error",
            "message": "disk full"
        }

    path = DATA_DIR + "/" + filename

    try:
        # Chunk pertama: tulis ulang file (mode wb)
        if chunk_index == 1:
            atomic_write(path, data)
        else:
            # Chunk berikutnya: tambahkan ke akhir file (mode ab)
            with open(path, "ab") as f:
                f.write(data)
    except Exception as e:
        print("Chunk write error:", e)
        return {
            "status": "error",
            "message": "write failed"
        }

    # Simpan progres chunk terbaru
    save_last_chunk(filename, chunk_index)

    # Hitung persentase progres
    percent = int((chunk_index / total_chunks) * 100)
    send_progress("upload", percent)

    print("Chunk", chunk_index, "/", total_chunks)

    # Jika ini chunk terakhir
    if chunk_index == total_chunks:
        clear_meta(filename)          # Hapus file meta
        print("File complete")

        # Jika diminta langsung training
        if auto_train:
            return handle_training({
                "program": "train_model.py"
            })

    return {
        "status": "chunk_received"
    }


# =========================
# TRAINING
# =========================

def handle_training(task):
    """
    Menjalankan program training yang ada di PROGRAM_DIR.
    Mengimpor modul, menjalankan fungsi run(), dan mengirim progres
    via send_progress. Watchdog timer di-feed secara berkala.
    Mengembalikan hasil training atau pesan error.
    """
    program = task.get("program", "train_model.py")
    module_name = program.replace(".py", "")

    # Pastikan direktori program ada di sys.path
    if PROGRAM_DIR not in sys.path:
        sys.path.append(PROGRAM_DIR)

    # Muat ulang modul agar mendapatkan versi terbaru
    reload_module(module_name)

    # Aktifkan watchdog
    wdt = start_watchdog()

    send_progress("training", 10)

    try:
        # Impor modul training
        module = __import__(module_name)

        send_progress("training", 40)

        start_time = time.time()
        wdt.feed()

        # Jalankan fungsi run() dari modul training
        result = module.run()

        wdt.feed()
        duration = time.time() - start_time

        send_progress("training", 100)
        print("Training done", duration)

        return {
            "status": "training_done",
            "result": result
        }

    except Exception as e:
        print("Training error:", e)
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        gc.collect()