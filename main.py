import time
import signal
import sys
import os

from toolsupdate.logger import get_logger

from toolsupdate.bootstrap import (
    bootstrap,
    bootstrap_fast
)

from raspberry.services.service_manager import (
    start_services
)

from raspberry.cli.command_listener import (
    command_listener
)

from raspberry.cli.banner import (
    print_banner
)

log = get_logger("ESP32_SERVER")

services_running = True


# =========================
# SHUTDOWN
# =========================

def shutdown():

    global services_running

    log.info("Stopping system")

    services_running = False

    time.sleep(1)

    log.info("System stopped")

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
    print("Pilih Mode untuk mulai:")
    print("")
    print("1. Update program --> start")
    print("2. Langsung Start program")
    print("")

    while True:

        try:

            choice = input(
                "Enter choice (1/2): "
            ).strip()

            if choice == "1":

                log.info("Running full bootstrap")

                bootstrap()

                return

            elif choice == "2":

                log.info("Running fast bootstrap")

                bootstrap_fast()

                return

            else:

                print(
                    "Invalid choice. "
                    "Please select 1 or 2."
                )

        except KeyboardInterrupt:

            shutdown()

        except Exception:

            log.exception(
                "Input error"
            )


# =========================
# MAIN SYSTEM LOOP
# =========================

def main():

    if os.environ.get(
        "ESP32_BOOTSTRAPPED"
    ) != "1":

        choose_start_mode()

    print_banner()

    start_services()

    log.info(
        "Server cluster ESP32 sudah siap"
    )

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

        except Exception:

            log.exception(
                "Runtime error"
            )

            time.sleep(2)


# =========================
# ENTRYPOINT
# =========================

if __name__ == "__main__":

    main()