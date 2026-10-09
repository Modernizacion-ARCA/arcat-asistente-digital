import ast
import sys
from pathlib import Path


TEST_PATTERN = 'project/apps/**/tests/test_*.py'


def check_test_file(path):
    issues = []
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    except SyntaxError as exc:
        return [f'{path}:{exc.lineno}: {exc.msg}']

    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and 'def test_' in node.value.value
        ):
            issues.append(
                f'{path}:{node.lineno}: hay pruebas desactivadas dentro de un string.'
            )
    return issues


def main():
    root = Path(__file__).resolve().parents[1]
    test_files = sorted(root.glob(TEST_PATTERN))
    issues = [
        issue
        for path in test_files
        for issue in check_test_file(path)
    ]
    if issues:
        print('\n'.join(issues), file=sys.stderr)
        return 1
    print(f'Fuentes de tests válidas: {len(test_files)} archivos.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
