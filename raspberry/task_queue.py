import time
import uuid


class TaskQueue:

    def __init__(self):

        self.pending = []

        self.running = {}

        self.completed = {}

        self.node_status = {}

    # =====================
    # ADD TASK
    # =====================

    def add_task(self, task):

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

        if not self.pending:

            return None

        return self.pending.pop(0)

    # =====================
    # NODE READY
    # =====================

    def set_node_ready(self, node):

        self.node_status[node] = "ready"

    # =====================
    # NODE BUSY
    # =====================

    def set_node_busy(self, node):

        self.node_status[node] = "busy"

    # =====================
    # GET READY NODE
    # =====================

    def get_ready_node(self):

        for node, status in self.node_status.items():

            if status == "ready":

                return node

        return None

    # =====================
    # MARK RUNNING
    # =====================

    def mark_running(self, task_id):

        self.running[task_id] = {

            "start_time": time.time()

        }

    # =====================
    # COMPLETE TASK
    # =====================

    def mark_completed(self, task_id, status):

        if task_id in self.running:

            self.completed[task_id] = status

            del self.running[task_id]

            print(
                "Task finished:",
                task_id,
                status
            )