# raspberry/cli/program_handler.py

def handle_upload_program():

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

        print("Program dikirim")

    except Exception as e:

        print("Upload program gagal:", e)


def handle_start_program():

    try:

        print("")

        program_name = input(
            "Program yang akan dijalankan: "
        ).strip()

        from raspberry.coordinator import add_task

        task = {

            "type": "start_program",

            "program": program_name

        }

        add_task(task)

        print("Start command dikirim")

    except Exception as e:

        print("Start gagal:", e)