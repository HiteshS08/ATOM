def remove_charset_from_content_type(content_type: str):
    # Remove any `charset` part from the Content-Type header
    parts = content_type.split(";")
    return parts[0].strip()
