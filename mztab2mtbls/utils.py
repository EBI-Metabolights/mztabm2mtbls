

def replace_null_string_with_none(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and value == "null":
                obj[key] = None
            else:
                replace_null_string_with_none(value)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            if isinstance(item, str) and item == "null":
                obj[index] = None
            else:
                replace_null_string_with_none(item)
