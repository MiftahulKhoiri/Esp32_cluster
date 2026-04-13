import os
import sys
import subprocess
from pathlib import Path

from toolsupdate.logger import get_logger
from toolsupdate.update import SelfUpdater

log = get_logger("ESP32_SERVER")

BASE_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = BASE_DIR / "venv"
REQ_FILE = BASE_DIR / "requirements.txt"

REQ_MARKER = VENV_DIR / ".deps_installed"

# ========================================
# VIRTUAL ENV
# ========================================

def in_virtualenv() -> bool:
    return sys.prefix != sys.base_prefix


def create_venv():

    log.warning(
        "Virtualenv belum ada, membuat venv..."
    )

    subprocess.check_call([
        sys.executable,
        "-m",
        "venv",
        str(VENV_DIR)
    ])

    log.info(
        "Virtualenv berhasil dibuat"
    )


def restart_in_venv():

    python_bin = VENV_DIR / "bin" / "python"

    log.warning(
        "Restarting aplikasi di dalam virtualenv..."
    )

    os.execv(
        str(python_bin),
        [str(python_bin)] + sys.argv
    )


# ========================================
# REQUIREMENTS
# ========================================

def install_requirements():

    if REQ_MARKER.exists():

        log.debug(
            "Dependency sudah terinstall"
        )

        return

    log.info(
        "Installing dependency..."
    )

    pip_bin = VENV_DIR / "bin" / "pip"

    subprocess.check_call([
        str(pip_bin),
        "install",
        "--upgrade",
        "-r",
        str(REQ_FILE)
    ])

    REQ_MARKER.touch()

    log.info(
        "Dependency siap"
    )


# ========================================
# BOOTSTRAP FULL
# ========================================

def bootstrap():

    log.info(
        "Bootstrap FULL start"
    )

    # 1. ensure venv

    if not VENV_DIR.exists():

        create_venv()

        restart_in_venv()

        return

    if not in_virtualenv():

        restart_in_venv()

        return

    log.info(
        "Running inside virtualenv"
    )

    # 2. dependency

    install_requirements()

    # 3. auto update

    updater = SelfUpdater(
        repo_dir=str(BASE_DIR)
    )

    if updater.update_if_needed():

        log.warning(
            "Restart setelah update"
        )

        restart_in_venv()

        return

    log.info(
        "Bootstrap FULL selesai"
    )


# ========================================
# BOOTSTRAP FAST
# ========================================

def bootstrap_fast():

    log.info(
        "Bootstrap FAST start"
    )

    if not VENV_DIR.exists():

        create_venv()

        restart_in_venv()

        return

    if not in_virtualenv():

        restart_in_venv()

        return

    log.info(
        "Bootstrap FAST selesai"
    )