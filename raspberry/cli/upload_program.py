# raspberry/cli/upload_program.py

import os


# =========================
# GET PROGRAM DIRECTORY
# =========================

def get_program_directory():

    current_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    program_dir = os.path.join(
        current_dir,
        "programs"
    )

    return program_dir


# =========================
# LIST PROGRAM FILES
# =========================

def list_program_files():

    try:

        program_dir = get_program_directory()

        if not os.path.exists(program_dir):

            print("")
            print("Folder programs belum ada:")
            print(program_dir)
            print("")

            return []

        files = []

        for file in os.listdir(program_dir):

            if file.endswith(".py"):

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
# UPLOAD PROGRAM
# =========================

def upload_program():

    try:

        print("")

        program_dir = get_program_directory()

        files = list_program_files()

        if not files:

            print(
                "Tidak ada file .py di folder programs"
            )
            return

        print("Lokasi folder program:")
        print(program_dir)
        print("")

        print("Daftar program:")
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
            "Pilih nomor program: "
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
            program_dir,
            filename
        )

        # =========================
        # READ FILE
        # =========================

        with open(filepath, "r") as f:

            code = f.read()

        # =========================
        # GET ACTIVE NODES
        # =========================

        nodes = get_active_nodes()

        if not nodes:

            print("")
            print("Tidak ada node aktif")
            print("")
            return

        from raspberry.coordinator import client

        print("")
        print("Mengirim program ke node:")
        print("")

        sent_count = 0

        for node in nodes:

            topic = "cluster/task/" + node

            task = {

                "type": "upload_program",

                "filename": filename,

                "code": code

            }

            import json

            client.publish(
                topic,
                json.dumps(task)
            )

            print(
                "✓ dikirim ke",
                node
            )

            sent_count += 1

        print("")
        print("Program :", filename)
        print("Total node :", sent_count)
        print("Upload selesai")
        print("")

    except Exception as e:

        print(
            "Upload program gagal:",
            e
        )