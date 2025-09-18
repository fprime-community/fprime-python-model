# F Prime Python Model

F Prime Python Model is a utility for translating `fpp-to-json` AST, Location Map, 
and Analysis JSON to Python data structures. For more information on the `fpp-to-json` 
tool, see the [FPP User's Guide](https://nasa.github.io/fpp/fpp-users-guide.html#Analyzing-and-Translating-Models_Generating-JSON-Models).


## Installation

```sh
git clone https://github.com/fprime-community/fprime-python-model.git
cd fprime-python-model
pip install fprime-python-model
```

## Usage
In order to use this utility, you must first run the `fpp-to-json` tool to generate
the AST, Location Map, and Analysis JSON files for a given FPP model. For specific 
steps on how to run `fpp-to-json`, see the 
[FPP User's Guide](https://nasa.github.io/fpp/fpp-users-guide.html#Analyzing-and-Translating-Models_Generating-JSON-Models).

> Note: When running the `fpp-to-json` tool, ensure that you *do not* include the 
> `-s` option as that will prevent the Analysis JSON from being generated.

Once the AST, Location Map, and Analysis JSON files have been generated, you can 
translate the model JSON to it's Python representation by doing:

```python
from fprime_python_model.model import FprimePythonModel

model = FprimePythonModel(
    ast_file_path, # Path to AST JSON file
    locations_file_path, # Path to Location Map JSON file
    analysis_json_file_path # Path to Analysis JSON file
)
```

