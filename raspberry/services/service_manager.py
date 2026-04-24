# raspberry/services/service_manager.py
"""
Manajer layanan untuk aplikasi Raspberry Pi.
Menjalankan OTA server, coordinator, dan monitor dalam thread terpisah.
Semua komentar dalam bahasa Indonesia.
"""

import threading
import time


def start_ota_server():
    """
    Memulai OTA server dalam thread terpisah.
    Mengimpor dan menjalankan modul OTA server.
    """
    try:
        print("[SERVICE] Starting OTA server")
        from raspberry.ota_server.ota_server import run
        run()
    except Exception as e:
        print("[ERROR] OTA server:", e)


def start_coordinator():
    """
    Memulai coordinator dalam thread terpisah.
    Mengimpor modul coordinator Raspberry Pi.
    """
    try:
        print("[SERVICE] Starting coordinator")
        import raspberry.coordinator
    except Exception as e:
        print("[ERROR] Coordinator:", e)


def monitor():
    """
    Fungsi pemantau sistem sederhana.
    Mencetak status setiap 10 detik untuk memastikan layanan tetap berjalan.
    """
    while True:
        print("[MONITOR] System running")
        time.sleep(10)


def start_services():
    """
    Menjalankan semua layanan (OTA, coordinator, monitor) di thread terpisah.
    OTA server dijalankan terlebih dahulu, coordinator menyusul setelah jeda 1 detik.
    Semua thread dijalankan sebagai daemon.
    """
    # Membuat thread untuk masing-masing layanan
    ota_thread = threading.Thread(
        target=start_ota_server,
        daemon=True
    )

    coordinator_thread = threading.Thread(
        target=start_coordinator,
        daemon=True
    )

    monitor_thread = threading.Thread(
        target=monitor,
        daemon=True
    )

    # Memulai thread
    ota_thread.start()
    time.sleep(1)          # Memberi waktu OTA server untuk siap
    coordinator_thread.start()
    monitor_thread.start()