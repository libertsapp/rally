import re


def ano_de(data: str) -> str:
    m = re.match(r"^(\d{4})-\d{2}-\d{2}", data)
    return m.group(1) if m else ""
