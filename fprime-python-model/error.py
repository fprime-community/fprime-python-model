
class InternalError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class NotSupportedInFppToJsonException(Exception):
    def __init__(self, field: str):
        super().__init__(f"The {field} field is not supported in fpp-to-json")

class InvalidFppToJsonField(Exception):
    def __init__(self, field: str):
        super().__init__(f"The {field} field is not valid")
