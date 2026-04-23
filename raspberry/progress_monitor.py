import time
import threading

from toolsupdate.logger import get_logger

log = get_logger("PROGRESS")

# =========================
# STATE
# =========================

# Dictionary untuk menyimpan progres terbaru dari setiap node.
# Struktur: { node_id: { stage, progress, memory_free_kb, ... } }
node_progress = {}

# Dictionary untuk menyimpan data terakhir yang dicetak per node,
# digunakan untuk deteksi perubahan agar tidak spam log.
last_printed = {}

lock = threading.Lock()

# Ambang batas kenaikan progress (dalam persen) untuk memicu pencetakan.
PROGRESS_STEP = 10


# =========================
# UPDATE
# =========================

def update_progress(
    node,
    payload
):
    """
    Memperbarui data progres untuk sebuah node.

    Fungsi ini dipanggil setiap kali ada informasi baru dari node (payload).
    Data yang disimpan meliputi tahapan (stage), persentase progres,
    penggunaan memori, CPU, flash, suhu, serta timestamp.
    Semua operasi dilindungi lock untuk keamanan thread.
    """
    with lock:
        # Membangun dictionary info node dari payload yang diterima
        node_progress[node] = {
            "stage": payload.get(
                "stage",
                "unknown"
            ),
            "progress": payload.get(
                "progress",
                0
            ),
            "memory_free_kb":
                payload.get(
                    "memory_free_kb"
                ),
            "memory_used_kb":
                payload.get(
                    "memory_used_kb"
                ),
            "cpu_percent":
                payload.get(
                    "cpu_percent"
                ),
            "flash_free_kb":
                payload.get(
                    "flash_free_kb"
                ),
            "flash_percent":
                payload.get(
                    "flash_percent"
                ),
            "temperature":
                payload.get(
                    "temperature"
                ),
            "time":
                time.strftime(
                    "%H:%M:%S"
                )
        }


# =========================
# CHANGE DETECTION
# =========================

def should_print(
    node,
    info
):
    """
    Menentukan apakah informasi progres node saat ini perlu dicetak ke log.

    Keputusan diambil berdasarkan perubahan yang signifikan:
    - Pencetakan pertama kali untuk node tersebut.
    - Kenaikan progress mencapai kelipatan PROGRESS_STEP.
    - Perubahan tahapan (stage).
    - Perubahan penggunaan CPU.
    - Perubahan suhu.
    Informasi terakhir yang dicetak disimpan di `last_printed` untuk pembandingan.
    """
    last = last_printed.get(node)

    # Jika belum pernah dicetak, langsung cetak
    if last is None:
        last_printed[node] = info
        return True

    # Jika progress naik melebihi atau sama dengan ambang langkah
    if info["progress"] >= last["progress"] + PROGRESS_STEP:
        last_printed[node] = info
        return True

    # Jika stage (tahapan) berubah
    if info["stage"] != last["stage"]:
        last_printed[node] = info
        return True

    # Jika CPU usage berubah
    if info["cpu_percent"] != last["cpu_percent"]:
        last_printed[node] = info
        return True

    # Jika suhu berubah
    if info["temperature"] != last["temperature"]:
        last_printed[node] = info
        return True

    # Tidak ada perubahan yang signifikan, tidak perlu cetak
    return False


# =========================
# PRINT EVENT
# =========================

def print_progress():
    """
    Mencetak progres node yang mengalami perubahan signifikan ke log.

    Fungsi ini melakukan iterasi pada semua node yang memiliki data progres,
    memeriksa dengan `should_print()` apakah perlu dicetak,
    dan kemudian mencatat informasi node (node ID, stage, progress, CPU, suhu)
    menggunakan logger `log.info`.
    """
    with lock:
        if not node_progress:
            return

        for node, info in node_progress.items():
            if not should_print(node, info):
                continue

            log.info(
                "Node update",
                extra={
                    "node": node,
                    "stage": info["stage"],
                    "progress": info["progress"],
                    "cpu": info["cpu_percent"],
                    "temp": info["temperature"]
                }
            )