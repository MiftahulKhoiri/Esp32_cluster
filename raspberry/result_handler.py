"""
Modul penanganan hasil (result handler) untuk cluster Raspberry Pi.
Menyimpan hasil dari node, memverifikasi checksum,
menggabungkan hasil, dan membersihkan file sementara.
Semua komentar dalam bahasa Indonesia.
"""

import os
import base64
import threading
import hashlib

from toolsupdate.logger import get_logger

logger = get_logger("result_handler")

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

TEMP_DIR = os.path.join(
    BASE_DIR,
    "cli",
    "temp"
)   # Direktori sementara untuk menyimpan hasil per node

HASIL_DIR = os.path.join(
    BASE_DIR,
    "cli",
    "hasil"
)   # Direktori penyimpanan hasil akhir gabungan

lock = threading.Lock()   # Mengamankan operasi file agar tidak terjadi race condition


# =========================
# INISIALISASI DIREKTORI
# =========================

def ensure_directories():
    """
    Memastikan direktori TEMP_DIR dan HASIL_DIR sudah ada.
    Jika belum, direktori akan dibuat.
    """
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(HASIL_DIR, exist_ok=True)


# =========================
# PEMERIKSAAN INTEGRITAS DATA
# =========================

def calculate_checksum(data):
    """
    Menghitung checksum SHA-256 dari data biner.

    Parameter:
        data (bytes): Data yang akan dihitung checksum-nya.

    Mengembalikan:
        str: Checksum heksadesimal.
    """
    sha = hashlib.sha256()
    sha.update(data)
    return sha.hexdigest()


def verify_checksum(data, expected):
    """
    Memverifikasi apakah checksum data sesuai dengan yang diharapkan.
    Jika checksum tidak cocok, pesan error akan dicatat.

    Parameter:
        data (bytes): Data yang akan diperiksa.
        expected (str): Checksum yang diharapkan (heksadesimal).

    Mengembalikan:
        bool: True jika cocok atau expected kosong, False jika tidak cocok.
    """
    if not expected:
        # Jika tidak ada checksum pembanding, dianggap valid
        return True

    actual = calculate_checksum(data)
    if actual != expected:
        logger.error(
            "Checksum mismatch",
            extra={
                "expected": expected,
                "actual": actual
            }
        )
        return False
    return True


# =========================
# PENULISAN FILE SECARA ATOMIK
# =========================

def atomic_write(file_path, data):
    """
    Menulis data ke file secara atomik: tulis ke file sementara,
    lalu ganti file tujuan. Mencegah file rusak jika terjadi crash.

    Parameter:
        file_path (str): Path file tujuan.
        data (bytes): Data yang akan ditulis.

    Mengembalikan:
        bool: True jika berhasil, False jika gagal.
    """
    temp_path = file_path + ".tmp"

    try:
        # Tulis ke file sementara
        with open(temp_path, "wb") as f:
            f.write(data)
            try:
                f.flush()    # Pastikan data tertulis ke disk
            except:
                pass

        # Hapus file asli jika sudah ada
        if os.path.exists(file_path):
            os.remove(file_path)

        # Ganti file sementara menjadi file tujuan
        os.rename(temp_path, file_path)
        return True

    except Exception:
        logger.exception("Atomic write failed")
        # Bersihkan file sementara jika proses gagal
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass
        return False


# =========================
# MENYIMPAN HASIL DARI NODE
# =========================

def save_node_result(node, filename, data_base64, checksum=None):
    """
    Mendekode data base64 dari node, memverifikasi checksum (jika ada),
    dan menyimpannya ke TEMP_DIR dengan nama file: {node}_{filename}.
    Operasi penulisan dilakukan secara atomik.

    Parameter:
        node (str): ID node pengirim.
        filename (str): Nama file hasil.
        data_base64 (str atau bytes): Data dalam format base64.
        checksum (str, opsional): Checksum SHA-256 untuk verifikasi.

    Mengembalikan:
        bool: True jika berhasil disimpan, False jika gagal.
    """
    ensure_directories()

    if not data_base64:
        logger.warning(
            "Result data kosong",
            extra={"node": node}
        )
        return False

    # Dekode base64
    try:
        if isinstance(data_base64, str):
            data_base64 = data_base64.encode()
        data = base64.b64decode(data_base64)
    except Exception as e:
        logger.error(
            "Base64 decode gagal",
            extra={
                "node": node,
                "error": str(e)
            }
        )
        return False

    # Verifikasi checksum jika disediakan
    if not verify_checksum(data, checksum):
        return False

    file_path = os.path.join(TEMP_DIR, f"{node}_{filename}")

    try:
        with lock:
            success = atomic_write(file_path, data)
            if not success:
                return False

        print(f"Result saved: {file_path}")
        return True

    except Exception:
        logger.exception("Gagal menyimpan result")
        return False


# =========================
# MEMERIKSA KESIAPAN HASIL
# =========================

def all_results_received():
    """
    Memeriksa apakah sudah ada file hasil dari minimal satu node di TEMP_DIR.
    (Fungsi sederhana; dapat diperluas sesuai jumlah node yang diharapkan).

    Mengembalikan:
        bool: True jika setidaknya ada satu file hasil, False jika kosong.
    """
    ensure_directories()

    files = os.listdir(TEMP_DIR)
    if not files:
        return False

    nodes = set()
    for file in files:
        node = file.split("_")[0]
        nodes.add(node)

    # Minimal ada satu node yang sudah mengirimkan hasil
    return len(nodes) > 0


# =========================
# MENGGABUNGKAN HASIL
# =========================

def merge_results(output_name="final_result.csv"):
    """
    Menggabungkan semua file hasil di TEMP_DIR menjadi satu file di HASIL_DIR.
    File digabung dalam urutan alfabet setelah dikunci (lock).
    Penulisan juga dilakukan secara atomik ke file sementara lalu diganti.

    Parameter:
        output_name (str): Nama file hasil gabungan (default: final_result.csv).
    """
    ensure_directories()

    output_path = os.path.join(HASIL_DIR, output_name)
    temp_output = output_path + ".tmp"   # File sementara untuk penulisan atomik

    files = sorted(os.listdir(TEMP_DIR))
    if not files:
        logger.warning("Tidak ada result untuk merge")
        return

    try:
        with lock:
            # Tulis semua isi file dari TEMP_DIR ke file sementara
            with open(temp_output, "wb") as outfile:
                for file in files:
                    file_path = os.path.join(TEMP_DIR, file)
                    with open(file_path, "rb") as infile:
                        outfile.write(infile.read())

            # Ganti file tujuan dengan file sementara
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_output, output_path)

        print(f"Final result created: {output_path}")

    except Exception:
        logger.exception("Merge result gagal")
        # Bersihkan file sementara jika terjadi error
        try:
            if os.path.exists(temp_output):
                os.remove(temp_output)
        except:
            pass


# =========================
# MEMBERSIHKAN DIREKTORI SEMENTARA
# =========================

def clear_temp():
    """
    Menghapus semua file di dalam TEMP_DIR dengan aman (menggunakan lock).
    Digunakan setelah hasil berhasil digabung.
    """
    ensure_directories()

    with lock:
        for file in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, file)
            try:
                os.remove(file_path)
            except Exception:
                logger.exception("Failed removing temp file")


# =========================
# PENANGAN UTAMA HASIL
# =========================

def handle_result(node, filename, data_base64, checksum=None):
    """
    Fungsi utama yang dipanggil saat koordinator menerima hasil dari node.
    Alur:
      1. Simpan hasil node ke TEMP_DIR.
      2. Jika semua hasil telah diterima, gabungkan dan bersihkan.

    Parameter:
        node (str): ID node pengirim.
        filename (str): Nama file hasil.
        data_base64 (str atau bytes): Data base64 dari node.
        checksum (str, opsional): Checksum untuk verifikasi.
    """
    # Simpan hasil sementara
    success = save_node_result(node, filename, data_base64, checksum)
    if not success:
        return

    # Periksa apakah semua node sudah mengirimkan hasil
    if all_results_received():
        print("All node results received")
        merge_results()
        clear_temp()