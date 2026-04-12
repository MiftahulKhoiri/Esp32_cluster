# raspberry/cli/upload_handler.py

def handle_upload():

    try:

        print("")

        filename = input(
            "Masukkan nama file program (.py): "
        ).strip()

        if not filename.endswith(".py"):

            print("File harus .py")

            return

        with open(filename, "r") as f:

            code = f.read()

        from raspberry.coordinator import add_task

        task = {

            "type": "upload_program",

            "filename": filename,

            "code": code

        }

        add_task(task)

        print("")
        print("Program berhasil dikirim ke node")
        print("")

    except FileNotFoundError:

        print("File tidak ditemukan")

    except Exception as e:

        print("Upload gagal:", e)