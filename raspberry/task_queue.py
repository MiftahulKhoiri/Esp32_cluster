# =========================
# IMPOR MODUL
# =========================

import time
import uuid


# =========================
# KELAS TASK QUEUE
# =========================

class TaskQueue:
    """
    Antrean (queue) untuk tugas-tugas yang akan didistribusikan ke node-node
    dalam cluster. Melacak status node, memilih node siap, dan mencatat progres tugas.
    """

    def __init__(self):
        """
        Inisialisasi struktur data:
        - pending   : daftar tugas menunggu
        - running   : dict tugas yang sedang berjalan
        - completed : dict tugas selesai
        - node_status : dict status setiap node ('ready' atau 'busy')
        """
        self.pending = []
        self.running = {}
        self.completed = {}
        self.node_status = {}

    # =====================
    # ADD TASK
    # =====================

    def add_task(self, task):
        """
        Menambahkan tugas baru ke antrean pending.
        Setiap tugas akan diberi task_id unik (UUID4) dan counter retry = 0.
        Mengembalikan task_id yang dibuat.
        """
        task_id = str(uuid.uuid4())
        task["task_id"] = task_id
        task["retry"] = 0
        self.pending.append(task)
        print("Task added:", task_id)
        return task_id

    # =====================
    # GET NEXT TASK
    # =====================

    def get_next_task(self):
        """
        Mengambil tugas pertama dari antrean pending (FIFO).
        Mengembalikan dictionary tugas, atau None jika antrean kosong.
        """
        if not self.pending:
            return None
        return self.pending.pop(0)

    # =====================
    # NODE READY
    # =====================

    def set_node_ready(self, node):
        """
        Menandai node tertentu sebagai 'ready', siap menerima tugas baru.
        """
        self.node_status[node] = "ready"

    # =====================
    # NODE BUSY
    # =====================

    def set_node_busy(self, node):
        """
        Menandai node tertentu sebagai 'busy', sedang mengerjakan tugas.
        """
        self.node_status[node] = "busy"

    # =====================
    # GET READY NODE
    # =====================

    def get_ready_node(self):
        """
        Mencari satu node yang berstatus 'ready'.
        Mengembalikan nama node, atau None jika tidak ada yang siap.
        """
        for node, status in self.node_status.items():
            if status == "ready":
                return node
        return None

    # =====================
    # MARK RUNNING
    # =====================

    def mark_running(self, task_id):
        """
        Mencatat bahwa tugas dengan task_id tertentu sedang berjalan,
        termasuk waktu mulai eksekusi.
        """
        self.running[task_id] = {
            "start_time": time.time()
        }

    # =====================
    # COMPLETE TASK
    # =====================

    def mark_completed(self, task_id, status):
        """
        Memindahkan tugas dari 'running' ke 'completed' dengan hasil status akhir.
        Jika task_id tidak ada di running (mungkin selesai sebelumnya), abaikan.
        """
        if task_id in self.running:
            self.completed[task_id] = status
            del self.running[task_id]
            print("Task finished:", task_id, status)