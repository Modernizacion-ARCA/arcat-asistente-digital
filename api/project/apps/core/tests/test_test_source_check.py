from scripts.check_test_sources import check_test_file


def test_check_test_file_accepts_executable_tests(tmp_path):
    path = tmp_path / 'test_valid.py'
    path.write_text('def test_example():\n    assert True\n', encoding='utf-8')

    assert check_test_file(path) == []


def test_check_test_file_reports_syntax_errors(tmp_path):
    path = tmp_path / 'test_invalid.py'
    path.write_text("'''\ndef test_hidden():\n    assert True\n", encoding='utf-8')

    issues = check_test_file(path)

    assert len(issues) == 1
    assert 'unterminated triple-quoted string' in issues[0]


def test_check_test_file_rejects_tests_hidden_in_strings(tmp_path):
    path = tmp_path / 'test_hidden.py'
    path.write_text(
        "'''\ndef test_hidden():\n    assert True\n'''\n",
        encoding='utf-8',
    )

    issues = check_test_file(path)

    assert len(issues) == 1
    assert 'pruebas desactivadas dentro de un string' in issues[0]
