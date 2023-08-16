from datetime import datetime


def iso_to_unix_timestamp(iso_string: str) -> float:
    """
    Convert ISO 8601 string to Unix timestamp

    For example, "2023-07-25T00:00:00.000Z" -> 1630368000.0
    """
    datetime_object = datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp = datetime_object.timestamp()
    return timestamp
