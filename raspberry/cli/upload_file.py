# raspberry/cli/upload_file.py

import os
import base64


# =========================
# GET DATA DIRECTORY
# =========================

def get_data_directory():

    # lokasi file ini
    current_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    # folder data
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

            # semua file diperbolehkan
            if not file.startswith("."):

                files.append(file)

        files.sort()

        return files

    except Exception as e:

        print("Error membaca folder:", e)

        return []


# =========================
# UPLOAD FILE
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

            data = f.read()

        file_size = len(data)

        # =========================
        # ENCODE BASE64
        # =========================

        encoded = base64.b64encode(
            data
        ).decode()

        # =========================
        # SEND TASK
        # =========================

        from raspberry.coordinator import add_task

        task = {

            "type": "upload_file",

            "filename": filename,

            "data": encoded,

            "size": file_size

        }

        add_task(task)

        print("")
        print("File dipilih :", filename)
        print("Ukuran file :", file_size, "bytes")
        print("File berhasil dikirim ke node")
        print("")

    except Exception as e:

        print(
            "Upload file gagal:",
            e
        )