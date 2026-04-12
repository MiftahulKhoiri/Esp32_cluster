# raspberry/cli/upload_file.py

import os
import math
import base64
import json
import time


# =========================
# CONFIG
# =========================

CHUNK_SIZE = 8 * 1024   # 8 KB (aman untuk ESP32)
SEND_DELAY = 0.05       # delay antar chunk (stabilkan MQTT)


# =========================
# GET DATA DIRECTORY
# =========================

def get_data_directory():

    current_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    data_dir = os.path.join(
        current_dir,
        "data"
    )

    return data_dir


# =========================
# LIST DATA FILES
# =========================

def list_data_files():

    try:

        data_dir = get_data_directory()

        if not os.path.exists(data_dir):

            print("")
            print("Folder data belum ada:")
            print(data_dir)
            print("")

            return []

        files = []

        for file in os.listdir(data_dir):

            if not file.startswith("."):

                files.append(file)

        files.sort()

        return files

    except Exception as e:

        print("Error membaca folder:", e)

        return []


# =========================
# GET ACTIVE NODES
# =========================

def get_active_nodes():

    try:

        from raspberry.coordinator import ready_nodes

        nodes = list(ready_nodes)

        return nodes

    except Exception as e:

        print("Gagal membaca node:", e)

        return []


# =========================
# SPLIT DATA RANGE
# =========================

def calculate_partition_ranges(total_size, node_count):

    ranges = []

    part_size = math.ceil(
        total_size / node_count
    )

    start = 0

    for i in range(node_count):

        end = start + part_size

        if end > total_size:

            end = total_size

        ranges.append(
            (start, end)
        )

        start = end

    return ranges


# =========================
# SEND CHUNK TO NODE
# =========================

def send_chunks_to_node(
    client,
    node,
    filename,
    data_slice,
    auto_train
):

    total_chunks = math.ceil(
        len(data_slice) / CHUNK_SIZE
    )

    chunk_index = 0

    while True:

        start = chunk_index * CHUNK_SIZE
        end = start + CHUNK_SIZE

        chunk = data_slice[start:end]

        if not chunk:

            break

        encoded = base64.b64encode(
            chunk
        ).decode()

        last_chunk = (
            chunk_index + 1
            == total_chunks
        )

        task = {

            "type": "upload_chunk",

            "filename": filename,

            "chunk_index": chunk_index + 1,

            "total_chunks": total_chunks,

            "data": encoded,

            "auto_train": last_chunk and auto_train

        }

        topic = "cluster/task/" + node

        client.publish(
            topic,
            json.dumps(task)
        )

        print(
            "  {} → chunk {}/{}".format(
                node,
                chunk_index + 1,
                total_chunks
            )
        )

        chunk_index += 1

        time.sleep(SEND_DELAY)


# =========================
# MAIN UPLOAD FUNCTION
# =========================

def upload_file():

    try:

        print("")

        data_dir = get_data_directory()

        files = list_data_files()

        if not files:

            print(
                "Tidak ada file di folder data"
            )
            return

        print("Lokasi folder data:")
        print(data_dir)
        print("")

        print("Daftar file:")
        print("")

        for i, file in enumerate(files):

            print(
                "{}. {}".format(
                    i + 1,
                    file
                )
            )

        print("")

        choice = input(
            "Pilih nomor file: "
        ).strip()

        if not choice.isdigit():

            print("Input harus angka")
            return

        index = int(choice) - 1

        if index < 0 or index >= len(files):

            print("Nomor tidak valid")
            return

        filename = files[index]

        filepath = os.path.join(
            data_dir,
            filename
        )

        # =========================
        # READ FILE
        # =========================

        with open(filepath, "rb") as f:

            file_data = f.read()

        file_size = len(file_data)

        # =========================
        # DETECT NODES
        # =========================

        nodes = get_active_nodes()

        if not nodes:

            print("")
            print("Tidak ada node aktif")
            print("")
            return

        node_count = len(nodes)

        print("")
        print("File dipilih :", filename)
        print("Ukuran file  :", file_size, "bytes")
        print("Node aktif   :", node_count)
        print("Chunk size   :", CHUNK_SIZE)
        print("")

        # =========================
        # SPLIT FILE PER NODE
        # =========================

        ranges = calculate_partition_ranges(
            file_size,
            node_count
        )

        from raspberry.coordinator import client

        print("Mengirim data ke node:")
        print("")

        for i, node in enumerate(nodes):

            start, end = ranges[i]

            data_slice = file_data[start:end]

            print(
                "Node:",
                node,
                "→ bytes",
                start,
                "-",
                end
            )

            send_chunks_to_node(
                client,
                node,
                filename,
                data_slice,
                auto_train=True
            )

        print("")
        print("Upload selesai")
        print("Node akan otomatis training")
        print("")

    except Exception as e:

        print(
            "Upload file gagal:",
            e
        )