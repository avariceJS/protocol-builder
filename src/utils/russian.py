"""Russian plural forms for UI counters."""


def plural_word(n: int, one: str, few: str, many: str) -> str:
    """Return the correct Russian plural form for *n* (1 → one, 2–4 → few, else many)."""
    abs_n = abs(n) % 100
    n1 = abs_n % 10
    if 11 <= abs_n <= 19:
        return many
    if n1 == 1:
        return one
    if 2 <= n1 <= 4:
        return few
    return many


def format_files_count(n: int) -> str:
    return f'{n} {plural_word(n, "файл", "файла", "файлов")}'
