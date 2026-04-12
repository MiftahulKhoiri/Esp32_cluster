# raspberry/cli/upload_file.py

import base64


def upload_file():

    try:

        print("")

        filename = input(
            "Nama file data: "
        ).strip()

        with open(filename, "rb") as f:

            data = f.read()

        encoded = base64.b64encode(
            data
        ).decode()

        from raspberry.coordinator import add_task

        task = {

            "type": "upload_file",

            "filename": filename,

            "data": encoded

        }

        add_task(task)

        print("File berhasil dikirim")

    except FileNotFoundError:

        print("File tidak ditemukan")

    except Exception as e:

        print("Upload file gagal:", e)