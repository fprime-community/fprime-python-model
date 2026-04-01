from fprime_python_model.model import FprimePythonModel
from fprime_python_model.utils.fpp_writer import FppWriter
from fprime_python_model.utils.line_utils import Lines
from tests.generate_ref_files import test_name_map, additional_tests
from typing import List
import subprocess
import os


def test_ast():
    all_tests = list(test_name_map.keys()) + list(additional_tests.keys())
    # Get location of test directory
    test_dir = os.path.dirname(os.path.abspath(__file__))

    fpp_writer = FppWriter()
    # Iterate through all test cases
    for test in os.listdir(test_dir):
        test_path = os.path.join(test_dir, test)
        if os.path.isdir(test_path) and test in all_tests:
            print(f"Test Case: {test}")
            fpp_ref_file = os.path.join(test_path, f"{test}.fpp")
            ast_file = os.path.join(test_path, f"{test}_ast.json")
            analysis_file = os.path.join(test_path, f"{test}_analysis.json")
            locations_file = os.path.join(test_path, f"{test}_locations.json")
            files = [fpp_ref_file, ast_file, analysis_file, locations_file]

            # Make sure all test files exist
            for f in files:
                assert os.path.isfile(f)

            # Construct an FprimePythonModel using test inputs
            model = FprimePythonModel(ast_file, locations_file, analysis_file)

            # Run FPP Writer
            fpp_lines: List[Lines] = []
            for tu in model.ast:
                fpp_lines.append(fpp_writer.write_trans_unit(tu))

            # Save FPP Writer output to txt file and diff against reference FPP
            out_file = os.path.join(test_path, f"{test}.out.txt")
            with open(out_file, "w") as out:
                for l in fpp_lines:
                    for line in l.lines:
                        out.write(str(line) + "\n")

            result = subprocess.run(["diff", fpp_ref_file, out_file])
            assert result.returncode == 0
