import time
import signal
import sys

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


def shutdown():

    global services_running

    print("")
    print("Stopping system...")

    services_running = False

    time.sleep(1)

    print("System stopped")

    sys.exit(0)


def handle_signal(sig, frame):

    shutdown()


signal.signal(
    signal.SIGINT,
    handle_signal
)


def main():

    # tampilkan banner
    print_banner()

    # start semua service
    start_services()

    # loop command
    while services_running:

        result = command_listener(
            lambda: services_running
        )

        if result == "exit":

            shutdown()

        time.sleep(1)


if __name__ == "__main__":

    bootstrap()

    main()