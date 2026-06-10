# F Prime Python Model

F Prime Python Model is a utility for translating `fpp-to-json` AST, Location Map, 
and Analysis JSON to Python data structures. For more information on the `fpp-to-json` 
tool, see the [FPP User's Guide](https://nasa.github.io/fpp/fpp-users-guide.html#Analyzing-and-Translating-Models_Generating-JSON-Models).

## Installation

```sh
pip install git+https://github.com/fprime-community/fprime-python-model.git
```

## Usage
In order to use this utility, you must first run the `fpp-to-json` tool to generate
the AST, Location Map, and Analysis JSON files for a given FPP model.

* When using `fpp-to-json` as part of a larger project, you can set
  `FPRIME_ENABLE_JSON_MODEL_GENERATION=ON` in your settings.ini to generate JSON
  files automatically.
* For specific steps on how to run `fpp-to-json` manually, see the 
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

Once an `FprimePythonModel` is constructed, you can access the python data structures that represent
the FPP AST, Location Map, and Analysis of the model:

```python
model.ast # Model AST
model.location_map # Location map
model.analysis # Model Analysis data structure
```

## Traversing AST
You can traverse AST nodes by writing an AST visitor, which can be used to query or search the AST of a model. An AST visitor base class (`AstVisitor`) is provided in `fprime_python_model/utils/fpp_ast_visitor.py`. 

Examples of how the `AstVistor` is used in this project are: 
- `fprime_python_model/utils/fpp_ast_writer.py`, which is used to print the AST to the console 
- `fprime_python_model/translators/construct_ast_id_map.py`, which is used to create a mapping from AST IDs to AST nodes.
