import sqlite3
import time


DB_FILE = "tasks.db"


def get_connection():

    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


def init_db():

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

    print("Database ready")


def insert_task(task):

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


def get_pending_task():

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


def update_status(task_id, status):

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


def increment_retry(task):

    conn = get_connection()

    cursor = conn.cursor()

    retry = task.get("retry", 0) + 1

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