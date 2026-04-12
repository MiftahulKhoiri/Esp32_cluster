# raspberry/cli/upload_program.py

def upload_program():

    try:

        print("")

        filename = input(
            "Nama program (.py): "
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

        print("Program berhasil dikirim")

    except FileNotFoundError:

        print("File tidak ditemukan")

    except Exception as e:

        print("Upload program gagal:", e)