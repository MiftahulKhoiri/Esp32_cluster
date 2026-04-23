import sqlite3
import time
import threading
import shutil
import os

DB_FILE = "tasks.db"

BACKUP_DIR = "db_backup"

BACKUP_INTERVAL = 300

MAX_BACKUPS = 5

# Kontrol interval retry dengan backoff eksponensial
BASE_RETRY_DELAY = 5   # delay awal dalam detik
MAX_RETRY_DELAY = 300  # batas maksimum delay

db_lock = threading.Lock()

backup_thread_started = False


# =========================
# CONNECTION
# =========================

def get_connection():
    """Membuka dan mengembalikan koneksi ke database SQLite."""
    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


# =========================
# INIT
# =========================

def init_db():
    """
    Menginisialisasi database dan sistem backup.

    Langkah-langkah:
    - Memastikan direktori backup tersedia.
    - Memulihkan database dari backup jika file database tidak ada.
    - Membuat tabel tasks jika belum ada.
    - Memulihkan task yang sebelumnya berstatus 'running' menjadi 'pending'.
    - Memulai thread backup otomatis.
    """
    ensure_backup_dir()

    restore_if_missing()

    with db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                payload TEXT,
                status TEXT,
                retry INTEGER,
                created REAL,
                updated REAL
            )
            """
        )
        conn.commit()
        conn.close()

    recover_running_tasks()

    start_backup_thread()

    print("Database ready")


# =========================
# CRASH RECOVERY
# =========================

def recover_running_tasks():
    """
    Memulihkan task yang terjebak dalam status 'running' akibat crash.

    Semua task dengan status 'running' diubah kembali menjadi 'pending'
    agar dapat diambil ulang oleh worker.
    """
    with db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tasks
            SET status='pending'
            WHERE status='running'
            """
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()

    if affected:
        print(
            "Recovered running tasks:",
            affected
        )


# =========================
# BACKUP SYSTEM
# =========================

def ensure_backup_dir():
    """Membuat direktori backup jika belum tersedia."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)


def restore_if_missing():
    """
    Memulihkan database dari file backup terbaru jika file database utama tidak ada.

    Berguna ketika database asli hilang atau rusak.
    """
    if os.path.exists(DB_FILE):
        return

    backups = sorted(os.listdir(BACKUP_DIR))

    if not backups:
        return

    latest = backups[-1]
    src = os.path.join(BACKUP_DIR, latest)
    shutil.copy2(src, DB_FILE)
    print(
        "Database restored from backup:",
        latest
    )


def create_backup():
    """Membuat salinan file database ke direktori backup dengan nama unik berdasarkan timestamp."""
    timestamp = int(time.time())
    backup_file = os.path.join(BACKUP_DIR, f"tasks_{timestamp}.db")

    try:
        with db_lock:
            if not os.path.exists(DB_FILE):
                return
            shutil.copy2(DB_FILE, backup_file)

        rotate_backups()
        print(
            "Database backup created:",
            backup_file
        )
    except Exception as e:
        print(
            "Backup error:",
            e
        )


def rotate_backups():
    """
    Menghapus file backup tertua jika jumlah backup melebihi batas maksimum.

    Memastikan ruang penyimpanan tidak terpakai oleh backup yang sudah tidak diperlukan.
    """
    backups = sorted(os.listdir(BACKUP_DIR))

    if len(backups) <= MAX_BACKUPS:
        return

    remove_count = len(backups) - MAX_BACKUPS

    for i in range(remove_count):
        old_file = os.path.join(BACKUP_DIR, backups[i])
        try:
            os.remove(old_file)
            print(
                "Old backup removed:",
                backups[i]
            )
        except Exception:
            pass


def backup_worker():
    """
    Worker yang berjalan di thread terpisah untuk membuat backup secara berkala.

    Interval backup ditentukan oleh BACKUP_INTERVAL.
    """
    while True:
        try:
            time.sleep(BACKUP_INTERVAL)
            create_backup()
        except Exception as e:
            print(
                "Backup worker error:",
                e
            )


def start_backup_thread():
    """Memulai thread daemon untuk backup otomatis jika belum berjalan."""
    global backup_thread_started

    if backup_thread_started:
        return

    backup_thread_started = True
    thread = threading.Thread(
        target=backup_worker,
        daemon=True
    )
    thread.start()
    print(
        "Database backup thread started"
    )


# =========================
# INSERT
# =========================

def insert_task(task):
    """
    Menyimpan task baru ke dalam tabel tasks dengan status awal 'pending'.

    Payload task disimpan dalam bentuk string representasi agar mudah dibaca kembali.
    """
    with db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        now = time.time()
        cursor.execute(
            """
            INSERT INTO tasks
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task["task_id"],
                str(task),
                "pending",
                task.get("retry", 0),
                now,
                now
            )
        )
        conn.commit()
        conn.close()


# =========================
# GET
# =========================

def get_pending_task():
    """
    Mengambil satu task paling lama dengan status 'pending' dari database.

    Task dikembalikan dalam bentuk dictionary asli hasil konversi dari string payload.
    Mengembalikan None jika tidak ada task pending.
    """
    now = time.time()

    with db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT task_id, payload
            FROM tasks
            WHERE status='pending'
            ORDER BY created ASC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        conn.close()

    if not row:
        return None

    import ast

    task_id, payload = row
    task = ast.literal_eval(payload)
    return task


# =========================
# UPDATE
# =========================

def update_status(task_id, status):
    """
    Memperbarui status sebuah task dan timestamp terakhir diubah.

    Digunakan untuk menandai task sebagai 'running', 'done', atau 'failed'.
    """
    with db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        now = time.time()
        cursor.execute(
            """
            UPDATE tasks
            SET status=?,
                updated=?
            WHERE task_id=?
            """,
            (
                status,
                now,
                task_id
            )
        )
        conn.commit()
        conn.close()


# =========================
# RETRY WITH BACKOFF
# =========================

def increment_retry(task):
    """
    Meningkatkan jumlah retry pada task dan menjadwalkan ulang dengan delay backoff.

    Delay dihitung secara eksponensial: BASE_RETRY_DELAY * (2^retry), dengan batas maksimum.
    Setelah menunggu, status task diubah kembali menjadi 'pending'.
    """
    retry = task.get("retry", 0) + 1
    delay = min(
        BASE_RETRY_DELAY * (2 ** retry),
        MAX_RETRY_DELAY
    )

    print(
        "Retry",
        retry,
        "delay",
        delay,
        "seconds"
    )

    time.sleep(delay)

    with db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        now = time.time()
        cursor.execute(
            """
            UPDATE tasks
            SET retry=?,
                status='pending',
                updated=?
            WHERE task_id=?
            """,
            (
                retry,
                now,
                task["task_id"]
            )
        )
        conn.commit()
        conn.close()