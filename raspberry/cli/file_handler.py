# raspberry/cli/file_handler.py

import base64


def handle_upload_file():

    try:

        print("")

        filename = input(
            "Nama file (txt/csv/json): "
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

        print("File dikirim")

    except Exception as e:

        print("Upload file gagal:", e)