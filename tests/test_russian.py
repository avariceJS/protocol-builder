from src.utils.russian import format_files_count, plural_word


def test_plural_word():
    assert plural_word(1, 'файл', 'файла', 'файлов') == 'файл'
    assert plural_word(2, 'файл', 'файла', 'файлов') == 'файла'
    assert plural_word(4, 'файл', 'файла', 'файлов') == 'файла'
    assert plural_word(5, 'файл', 'файла', 'файлов') == 'файлов'
    assert plural_word(11, 'файл', 'файла', 'файлов') == 'файлов'
    assert plural_word(21, 'файл', 'файла', 'файлов') == 'файл'
    assert plural_word(22, 'файл', 'файла', 'файлов') == 'файла'


def test_format_files_count():
    assert format_files_count(1) == '1 файл'
    assert format_files_count(2) == '2 файла'
    assert format_files_count(5) == '5 файлов'
