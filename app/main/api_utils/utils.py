def check_required_fields(required_fields: list, data: list) -> list:
    # Validate required fields
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    # Return all missing fields, empty if nothing is missing
    return missing_fields
