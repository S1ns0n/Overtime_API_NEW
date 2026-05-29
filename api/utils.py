from datetime import datetime

def parse_date(date_string: str) -> datetime:
    """
    Пробует разные форматы дат и возвращает datetime

    Поддерживаемые форматы:
    - 2024-01-15
    - 15.01.2024
    - 15/01/2024
    - 15-01-2024
    - 2024-01-15T10:30:00
    """
    formats = [
        "%Y-%m-%d",  # 2024-01-15
        "%d.%m.%Y",  # 15.01.2024
        "%d/%m/%Y",  # 15/01/2024
        "%d-%m-%Y",  # 15-01-2024
        "%Y-%m-%dT%H:%M:%S",  # 2024-01-15T10:30:00
        "%d.%m.%Y %H:%M",  # 15.01.2024 10:30
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    raise ValueError(
        f"Не удалось распознать дату '{date_string}'. "
        f"Поддерживаемые форматы: 2024-01-15, 15.01.2024, 15/01/2024"
    )