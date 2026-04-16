import os
import base64
import threading

from toolsupdate.logger import get_logger

logger = get_logger("result_handler")

# =========================
# DIRECTORY
# =========================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

TEMP_DIR = os.path.join(
    BASE_DIR,
    "cli",
    "temp"
)

HASIL_DIR = os.path.join(
    BASE_DIR,
    "cli",
    "hasil"
)

lock = threading.Lock()


# =========================
# INIT
# =========================

def ensure_directories():

    os.makedirs(
        TEMP_DIR,
        exist_ok=True
    )

    os.makedirs(
        HASIL_DIR,
        exist_ok=True
    )


# =========================
# ATOMIC WRITE
# =========================

def atomic_write(file_path, data):

    temp_path = file_path + ".tmp"

    try:

        with open(
            temp_path,
            "wb"
        ) as f:

            f.write(data)

            try:
                f.flush()
            except:
                pass

        if os.path.exists(
            file_path
        ):
            os.remove(
                file_path
            )

        os.rename(
            temp_path,
            file_path
        )

        return True

    except Exception as e:

        logger.exception(
            "Atomic write failed"
        )

        try:

            if os.path.exists(
                temp_path
            ):
                os.remove(
                    temp_path
                )

        except:
            pass

        return False


# =========================
# SAVE RESULT
# =========================

def save_node_result(
    node,
    filename,
    data_base64
):

    ensure_directories()

    if not data_base64:

        logger.warning(
            "Result data kosong",
            extra={"node": node}
        )

        return False

    try:

        if isinstance(
            data_base64,
            str
        ):

            data_base64 = data_base64.encode()

        data = base64.b64decode(
            data_base64
        )

    except Exception as e:

        logger.error(
            "Base64 decode gagal",
            extra={
                "node": node,
                "error": str(e)
            }
        )

        return False

    file_path = os.path.join(
        TEMP_DIR,
        f"{node}_{filename}"
    )

    try:

        with lock:

            success = atomic_write(
                file_path,
                data
            )

            if not success:
                return False

        print(
            f"Result saved: {file_path}"
        )

        return True

    except Exception:

        logger.exception(
            "Gagal menyimpan result"
        )

        return False


# =========================
# CHECK RESULT READY
# =========================

def all_results_received():

    ensure_directories()

    files = os.listdir(
        TEMP_DIR
    )

    if not files:

        return False

    nodes = set()

    for file in files:

        node = file.split("_")[0]

        nodes.add(node)

    return len(nodes) > 0


# =========================
# MERGE RESULT
# =========================

def merge_results(
    output_name="final_result.csv"
):

    ensure_directories()

    output_path = os.path.join(
        HASIL_DIR,
        output_name
    )

    temp_output = output_path + ".tmp"

    files = sorted(
        os.listdir(
            TEMP_DIR
        )
    )

    if not files:

        logger.warning(
            "Tidak ada result untuk merge"
        )

        return

    try:

        with lock:

            with open(
                temp_output,
                "wb"
            ) as outfile:

                for file in files:

                    file_path = os.path.join(
                        TEMP_DIR,
                        file
                    )

                    with open(
                        file_path,
                        "rb"
                    ) as infile:

                        outfile.write(
                            infile.read()
                        )

            if os.path.exists(
                output_path
            ):
                os.remove(
                    output_path
                )

            os.rename(
                temp_output,
                output_path
            )

        print("")
        print(
            f"Final result created: {output_path}"
        )
        print("")

    except Exception:

        logger.exception(
            "Merge result gagal"
        )

        try:

            if os.path.exists(
                temp_output
            ):
                os.remove(
                    temp_output
                )

        except:
            pass


# =========================
# CLEAR TEMP
# =========================

def clear_temp():

    ensure_directories()

    with lock:

        for file in os.listdir(
            TEMP_DIR
        ):

            file_path = os.path.join(
                TEMP_DIR,
                file
            )

            try:

                os.remove(
                    file_path
                )

            except Exception:

                logger.exception(
                    "Failed removing temp file"
                )


# =========================
# MAIN HANDLER
# =========================

def handle_result(
    node,
    filename,
    data_base64
):

    success = save_node_result(
        node,
        filename,
        data_base64
    )

    if not success:
        return

    if all_results_received():

        print(
            "All node results received"
        )

        merge_results()

        clear_temp()