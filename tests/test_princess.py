import nbformat
from pathlib import Path
import shutil

from princess import main

this_dir = Path(__file__).parent

def test_output(capsys):
    main([str(this_dir / 'Sample.ipynb')])

    captured = capsys.readouterr()
    assert 'Print to stdout\n' in captured.out
    assert 'Print to stderr\n' in captured.err
    assert 'Display text' in captured.out
    assert 'ZeroDivisionError' in captured.out


def test_save(tmp_path):
    nb_orig = nbformat.read(this_dir / 'Sample.ipynb', as_version=4)
    assert nb_orig.cells[0].outputs == []

    shutil.copy2(this_dir / 'Sample.ipynb', tmp_path)
    main([str(tmp_path / 'Sample.ipynb'), '--save'])

    nb_saved = nbformat.read(tmp_path / 'Sample.ipynb', as_version=4)
    assert nb_saved.cells[0].outputs[0].text == 'Print to stdout\n'


def test_save_as(tmp_path):
    output_path = tmp_path / 'Executed.ipynb'
    main([str(this_dir / 'Sample.ipynb'), '--save-as', str(output_path)])

    nb_orig = nbformat.read(this_dir / 'Sample.ipynb', as_version=4)
    assert nb_orig.cells[0].outputs == []

    nb_saved = nbformat.read(output_path, as_version=4)
    assert nb_saved.cells[0].outputs[0].text == 'Print to stdout\n'


def test_error():
    assert main([str(this_dir / 'Error.ipynb')]) == 1
    assert main([str(this_dir / 'Error.ipynb'), '--on-error-resume-next']) == 0
