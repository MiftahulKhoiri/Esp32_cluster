import os
import base64


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
# SAVE RESULT FROM NODE
# =========================

def save_node_result(
    node,
    filename,
    data_base64
):

    ensure_directories()

    file_path = os.path.join(
        TEMP_DIR,
        f"{node}_{filename}"
    )

    data = base64.b64decode(
        data_base64
    )

    with open(
        file_path,
        "wb"
    ) as f:

        f.write(data)

    print(
        "Result saved:",
        file_path
    )


# =========================
# CHECK IF ALL RESULT READY
# =========================

def all_results_received():

    from raspberry.coordinator import ready_nodes

    nodes = list(ready_nodes)

    files = os.listdir(
        TEMP_DIR
    )

    received_nodes = set()

    for file in files:

        node = file.split("_")[0]

        received_nodes.add(node)

    return set(nodes) == received_nodes


# =========================
# MERGE RESULT FILES
# =========================

def merge_results(
    output_name="final_result.csv"
):

    ensure_directories()

    output_path = os.path.join(
        HASIL_DIR,
        output_name
    )

    files = sorted(
        os.listdir(
            TEMP_DIR
        )
    )

    with open(
        output_path,
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

    print("")
    print(
        "Final result created:"
    )

    print(
        output_path
    )

    print("")


# =========================
# MAIN HANDLER
# =========================

def handle_result(
    node,
    filename,
    data_base64
):

    save_node_result(
        node,
        filename,
        data_base64
    )

    if all_results_received():

        print(
            "All node results received"
        )

        merge_results()