import sqlite3
import time
import threading
import shutil
import os

DB_FILE = "tasks.db"

# =========================
# BACKUP CONFIG
# =========================

BACKUP_DIR = "db_backup"

BACKUP_INTERVAL = 300      # seconds

MAX_BACKUPS = 5

# =========================
# GLOBAL LOCK
# =========================

db_lock = threading.Lock()

backup_thread_started = False


# =========================
# CONNECTION
# =========================

def get_connection():

    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


# =========================
# INIT
# =========================

def init_db():

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

    start_backup_thread()

    print("Database ready")


# =========================
# BACKUP SYSTEM
# =========================

def ensure_backup_dir():

    if not os.path.exists(
        BACKUP_DIR
    ):

        os.makedirs(
            BACKUP_DIR
        )


def restore_if_missing():

    if os.path.exists(
        DB_FILE
    ):

        return

    backups = sorted(
        os.listdir(
            BACKUP_DIR
        )
    )

    if not backups:

        return

    latest = backups[-1]

    src = os.path.join(
        BACKUP_DIR,
        latest
    )

    shutil.copy2(
        src,
        DB_FILE
    )

    print(
        "Database restored from backup:",
        latest
    )


def create_backup():

    timestamp = int(
        time.time()
    )

    backup_file = os.path.join(
        BACKUP_DIR,
        f"tasks_{timestamp}.db"
    )

    try:

        with db_lock:

            if not os.path.exists(
                DB_FILE
            ):
                return

            shutil.copy2(
                DB_FILE,
                backup_file
            )

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

    backups = sorted(
        os.listdir(
            BACKUP_DIR
        )
    )

    if len(backups) <= MAX_BACKUPS:

        return

    remove_count = len(backups) - MAX_BACKUPS

    for i in range(remove_count):

        old_file = os.path.join(
            BACKUP_DIR,
            backups[i]
        )

        try:

            os.remove(
                old_file
            )

            print(
                "Old backup removed:",
                backups[i]
            )

        except Exception:

            pass


def backup_worker():

    while True:

        try:

            time.sleep(
                BACKUP_INTERVAL
            )

            create_backup()

        except Exception as e:

            print(
                "Backup worker error:",
                e
            )


def start_backup_thread():

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

    task = ast.literal_eval(
        payload
    )

    return task


# =========================
# UPDATE
# =========================

def update_status(task_id, status):

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
# RETRY
# =========================

def increment_retry(task):

    with db_lock:

        conn = get_connection()

        cursor = conn.cursor()

        retry = task.get(
            "retry",
            0
        ) + 1

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