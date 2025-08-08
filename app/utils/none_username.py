from typing import Optional


def safe_username(username: Optional[str], default: str) -> str:
    """
    Безопасно обрабатывает username, возвращая дефолтное значение,
    если username отсутствует, пустой или равен строке "none" (регистр не важен).

    :param username: Входящий username, может быть None.
    :param default: Значение по умолчанию, если username некорректен.
    :return: Строка с корректным username или дефолтом.
    """
    if username is None:
        return default
    username_str = str(username).strip()
    if username_str == "" or username_str.lower() == "none":
        return default
    return username_str
