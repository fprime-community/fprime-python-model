import subprocess
import argparse
from pathlib import Path
import sys
import os
import re
from fprime_python_model.fpp_version import check_version
from typing import Optional, Dict, Tuple, List

# fpp-to-json tests (with no input files)
# Mapping of fprime-python-model test names to fpp-to-json test names
test_name_map: Dict[str, str] = {
    "active_component": "activeComponents",
    "commands": "commands",
    "constants": "constants",
    "data_products": "dataProducts",
    "events": "events",
    "imported_topology": "importedTopologies",
    "interfaces": "interfaces",
    "internal_ports": "internalPorts",
    "matched_ports": "matchedPorts",
    "parameters": "parameters",
    "passive_component": "passiveComponent",
    "ports": "ports",
    "queued_component": "queuedComponents",
    "special_ports": "specialPorts",
    "telemetry": "telemetry",
    "telemetry_packets": "telemetryPackets",
    "topology": "simpleTopology",
    "topology_ports": "topologyPorts",
    "types": "types",
}

# fpp-to-json tests that are located in different tool directories and might included input files
# Dictionary with test name keys and tuple values with the following format: (location of test, input file)
additional_tests: Dict[str, Tuple[str, Optional[str]]] = {
    "state_machine": ("compiler/tools/fpp-syntax/test/state-machine.fpp", None),
    "patterned_connections": (
        "compiler/tools/fpp-to-json/test/patternedConnections.fpp",
        "compiler/tools/fpp-to-json/test/fprime/defs.fpp",
    ),
    "location_specifier": (
        "compiler/tools/fpp-depend/test/dictionary_no_top.fpp",
        None,
    ),
    "command_patterned_connections": (
        "compiler/tools/fpp-check/test/connection_pattern/command_ok.fpp",
        None,
    ),
}


def clean():
    def remove_file(file_path: str):
        if os.path.exists(file_path):
            os.remove(file_path)

    for test_name in list(test_name_map.keys()) + list(additional_tests.keys()):
        remove_file(f"tests/{test_name}/{test_name}_ast.json")
        remove_file(f"tests/{test_name}/{test_name}_locations.json")
        remove_file(f"tests/{test_name}/{test_name}_analysis.json")
        remove_file(f"tests/{test_name}/{test_name}.fpp")


def create_model_ref_file(
    fpp_format: Path,
    fpp_ref_model: str,
    test_name: str,
    input_file: Optional[str] = None,
):
    test_fpp_ref_name = f"tests/{test_name}/{test_name}.fpp"
    fpp_format_cmd: List = [fpp_format, fpp_ref_model]
    if input_file:
        fpp_format_cmd = [fpp_format, fpp_ref_model, input_file]
    # Run fpp-format on reference model and save output to test case directory
    try:
        with open(test_fpp_ref_name, "w") as f:
            subprocess.run(fpp_format_cmd, stdout=f, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(
            f"Failed to run fpp-format for test case {test_name}. Reference FPP model has not been updated. Error: {e}"
        )


def create_json_ref_files(
    fpp_to_json: Path,
    fpp_ref_model: str,
    test_name: str,
    input_file: Optional[str] = None,
):
    fpp_to_json_cmd: List[str] = [str(fpp_to_json), "-f", fpp_ref_model]
    if input_file:
        fpp_to_json_cmd = [str(fpp_to_json), fpp_ref_model, input_file]
    # Run fpp-to-json on reference model and save output to test case directory
    result = subprocess.run(fpp_to_json_cmd)
    if result.returncode != 0:
        print(f"Encountered an error when running fpp-to-json on {test_name}.fpp")
    else:
        # Define the old and new paths
        old_ast_path = "fpp-ast.json"
        new_ast_path = f"tests/{test_name}/{test_name}_ast.json"

        old_analysis_path = "fpp-analysis.json"
        new_analysis_path = f"tests/{test_name}/{test_name}_analysis.json"

        old_loc_path = "fpp-loc-map.json"
        new_loc_path = f"tests/{test_name}/{test_name}_locations.json"

        path_start = "/".join(str(fpp_to_json).split("/")[:-3])
        for old_file, new_file in [
            (old_ast_path, new_ast_path),
            (old_analysis_path, new_analysis_path),
            (old_loc_path, new_loc_path),
        ]:
            content = ""
            with open(old_file, "r") as f:
                content = f.read()
            # Replace paths with placeholder
            updated_content = content.replace(path_start, "[ local path prefix ]")
            with open(new_file, "w") as f:
                f.write(updated_content)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "fpp_repo_path",
        type=Path,
        help="Location of FPP repo. Note: FPP tools must be installed at compiler/bin",
    )
    args = parser.parse_args()

    fpp_repo_path: Path = args.fpp_repo_path
    fpp_to_json: Path = fpp_repo_path / "compiler/bin/fpp-to-json"
    fpp_format: Path = fpp_repo_path / "compiler/bin/fpp-format"
    fpp_to_json_tests_path: Path = fpp_repo_path / "compiler/tools/fpp-to-json/test"

    if not fpp_repo_path.exists():
        print("FPP repo path does not exist, exiting...")
        sys.exit(1)

    if not fpp_to_json.exists():
        print(f"fpp-to-json is not installed at {fpp_to_json}, exiting...")
        sys.exit(1)

    if not fpp_format.exists():
        print(f"fpp-format is not installed at {fpp_format}, exiting...")
        sys.exit(1)

    if not fpp_to_json_tests_path.exists():
        print(
            f"Could not find fpp-to-json tests at {fpp_to_json_tests_path}, exiting..."
        )
        sys.exit(1)

    help_res = subprocess.run([fpp_to_json, "-h"], capture_output=True)
    match = re.search(r"v(\d+\.\d+\.\d+[a-zA-Z0-9]*)", help_res.stdout.decode())
    if match:
        version = match.group(1)
        check_version(str(version), f"FPP version ({version}) is incompatible.")
    else:
        print("Could not verify FPP tool version, exiting...")
        sys.exit(1)

    # Delete old ref files
    clean()

    for test_name, fpp_to_json_test_name in test_name_map.items():
        fpp_ref_model: str = (
            f"{str(fpp_to_json_tests_path)}/{fpp_to_json_test_name}.fpp"
        )
        create_model_ref_file(fpp_format, fpp_ref_model, test_name)
        create_json_ref_files(fpp_to_json, str(fpp_ref_model), test_name)

    for test_name, (test_location, input_file) in additional_tests.items():
        fpp_ref = str(fpp_repo_path / test_location)

        input_file_path: Optional[str] = None
        if input_file:
            input_file_path = str(fpp_repo_path / input_file)

        create_model_ref_file(fpp_format, fpp_ref, test_name, input_file_path)
        create_json_ref_files(fpp_to_json, fpp_ref, test_name, input_file_path)


if __name__ == "__main__":
    main()
