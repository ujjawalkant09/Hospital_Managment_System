import csv
import io
from typing import List, Tuple
from .const import REQUIRED_COLUMNS, ALLOWED_COLUMNS


def validate_csv_text(csv_text: str) -> Tuple[List[dict], List[str]]:
    """
    Validates CSV content and returns:
    - rows: parsed CSV rows
    - errors: list of validation errors
    """

    try:
        reader = csv.DictReader(io.StringIO(csv_text))
    except Exception:
        return [], ["Invalid CSV format"]

    headers = set(reader.fieldnames or [])
    errors: List[str] = []

    missing_columns = REQUIRED_COLUMNS - headers
    extra_columns = headers - ALLOWED_COLUMNS

    if missing_columns:
        errors.append(
            f"Missing required columns: {', '.join(missing_columns)}"
        )

    if extra_columns:
        errors.append(
            f"Unexpected columns found: {', '.join(extra_columns)}"
        )

    rows = []

    for index, row in enumerate(reader, start=1):
        if not any(row.values()):
            errors.append(f"Row {index}: Empty row")
            continue

        if not row.get("name"):
            errors.append(f"Row {index}: 'name' is required")

        if not row.get("address"):
            errors.append(f"Row {index}: 'address' is required")

        rows.append(row)

    if not rows:
        errors.append("CSV contains no valid data rows")

    return rows, errors
