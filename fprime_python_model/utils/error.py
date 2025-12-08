from fprime_python_model.fpp_ast.fpp_locations import Location
from typing import Optional
import json


class InternalError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


# Field not supported by fpp-to-json
class NotSupportedInFppToJsonException(Exception):
    def __init__(self, field: str):
        super().__init__(f'The "{field}" field is not supported in fpp-to-json')


# Error for invalid JSON field with optional node location
class InvalidFppToJsonField(Exception):
    def __init__(self, field: str, node_location: Optional[Location] = None):
        msg = f'The "{field}" field is not valid.'
        if node_location:
            msg += f"\nLocation: {str(node_location)}"
        super().__init__(msg)


# Error for invalid JSON dictionary with optional node location
class InvalidFppToJsonDictionary(Exception):
    def __init__(self, name: str, dict: dict, node_location: Optional[Location] = None):
        msg = f"Encountered invalid JSON dictionary when translating {name}. Invalid dictionary is:\n{json.dumps(dict, indent=2)}."
        if node_location:
            msg += f"\nLocation: {str(node_location)}"
        super().__init__(msg)
