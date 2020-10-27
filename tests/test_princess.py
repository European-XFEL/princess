from pathlib import Path
from princess import main

this_dir = Path(__file__).parent

def test_output(capsys):
    main([str(this_dir / 'Sample.ipynb')])

    captured = capsys.readouterr()
    assert 'Print to stdout\n' in captured.out
    assert 'Print to stderr\n' in captured.err
    assert 'Display text' in captured.out
    assert 'ZeroDivisionError' in captured.out
