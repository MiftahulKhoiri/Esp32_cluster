import time
import signal
import sys
import os

from toolsupdate.bootstrap import bootstrap

from raspberry.services.service_manager import (
    start_services
)

from raspberry.cli.command_listener import (
    command_listener
)

from raspberry.cli.banner import (
    print_banner
)


services_running = True

VENV_PATH = "venv"
VENV_PYTHON = os.path.join(
    VENV_PATH,
    "bin",
    "python3"
)


# =========================
# VENV CHECK
# =========================

def ensure_venv():

    # apakah sudah jalan di venv
    if sys.prefix != sys.base_prefix:

        return

    print("")
    print("[SYSTEM] Virtual environment not active")

    if not os.path.exists(VENV_PYTHON):

        print(
            "[ERROR] venv not found:",
            VENV_PYTHON
        )

        print(
            "Create venv first:"
        )

        print(
            "python3 -m venv venv"
        )

        sys.exit(1)

    print(
        "[SYSTEM] Restarting using venv..."
    )

    os.execv(
        VENV_PYTHON,
        [VENV_PYTHON] + sys.argv
    )


# =========================
# SHUTDOWN
# =========================

def shutdown():

    global services_running

    print("")
    print("Stopping system...")

    services_running = False

    time.sleep(1)

    print("System stopped")

    sys.exit(0)


# =========================
# SIGNAL HANDLER
# =========================

def handle_signal(sig, frame):

    shutdown()


signal.signal(
    signal.SIGINT,
    handle_signal
)


# =========================
# MODE SELECTION
# =========================

def choose_start_mode():

    print("")
    print("Select startup mode:")
    print("")
    print("1. Update then start")
    print("2. Start immediately")
    print("")

    while True:

        try:

            choice = input(
                "Enter choice (1/2): "
            ).strip()

            if choice == "1":

                print("")
                print("Running update...")

                bootstrap()

                print("")
                print("Update finished")
                print("")

                return

            elif choice == "2":

                print("")
                print("Starting with virtual environment...")
                print("")

                ensure_venv()

                return

            else:

                print(
                    "Invalid choice. "
                    "Please select 1 or 2."
                )

        except KeyboardInterrupt:

            shutdown()

        except Exception as e:

            print(
                "Input error:",
                str(e)
            )


# =========================
# MAIN SYSTEM LOOP
# =========================

def main():

    print_banner()

    choose_start_mode()

    start_services()

    print("")
    print("System ready")
    print("")

    while services_running:

        try:

            result = command_listener(
                lambda: services_running
            )

            if result == "exit":

                shutdown()

            time.sleep(1)

        except KeyboardInterrupt:

            shutdown()

        except Exception as e:

            print(
                "Runtime error:",
                str(e)
            )

            time.sleep(2)


# =========================
# ENTRYPOINT
# =========================

if __name__ == "__main__":

    main()