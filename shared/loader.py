import json
from jsonschema import validate, ValidationError

def load_and_validate_json_file(json_path: str, schema_path: str):
    """
    Opens and validates a JSON file according to a JSON schema
    """
    with open(json_path, "r") as f:
        data = json.load(f)
    with open(schema_path, "r") as f:
        schema = json.load(f)
    validate(instance=data, schema=schema)
    return data
