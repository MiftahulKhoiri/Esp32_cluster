# raspberry/cli/start_train.py

def start_train():

    try:

        print("")

        program_name = input(
            "Program yang akan dijalankan: "
        ).strip()

        from raspberry.coordinator import add_task

        task = {

            "type": "start_train",

            "program": program_name

        }

        add_task(task)

        print("Perintah start dikirim")

    except Exception as e:

        print("Start gagal:", e)