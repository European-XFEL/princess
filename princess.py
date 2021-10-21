"""Please Run IPython Notebook in the Current Environment with Stdout & Stderr
"""
from argparse import ArgumentParser
import os
import sys
from tempfile import TemporaryDirectory

from ipykernel.kernelspec import RESOURCES, get_kernel_dict
from jupyter_client import AsyncKernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
import nbformat

__version__ = '0.5'


class CurrentEnvKernelSpecManager(KernelSpecManager):
    """Always launch a Python kernel with the current Python interpreter.

    Ignores the kernel name (from the notebook)
    """
    def get_kernel_spec(self, kernel_name):
        return self.kernel_spec_class(resource_dir=RESOURCES, **get_kernel_dict())


class PrincessNotebookClient(NotebookClient):
    __sockets_tmpdir = None

    def create_kernel_manager(self):
        kwargs = {}
        # Use ipc transport (Unix domain sockets) with a temp dir if possible;
        # something else may claim TCP sockets while the kernel is starting.
        if os.name == 'posix':
            self.__sockets_tmpdir = TemporaryDirectory(prefix="jupyter-kernel-")
            kwargs['transport'] = 'ipc'
            kwargs['ip'] = os.path.join(self.__sockets_tmpdir.name, 'socket')

        return AsyncKernelManager(
            kernel_spec_manager=CurrentEnvKernelSpecManager(),
            **kwargs,
        )

    async def _async_cleanup_kernel(self):
        await super()._async_cleanup_kernel()
        if self.__sockets_tmpdir is not None:
            self.__sockets_tmpdir.cleanup()

    def output(self, outs, msg, display_id, cell_index):
        """Display text output, as well as saving it in the notebook"""
        msg_type = msg['msg_type']
        content = msg['content']
        stream = sys.stdout
        if msg_type == 'stream':
            if content.get('name') == 'stderr':
                stream = sys.stderr
            text = content.get('text')
        elif msg_type == 'display_data':
            text = content.get('data', {}).get('text/plain')
            if text:
                text += '\n'
        elif msg_type == 'error':
            ename, evalue = content.get('ename'), content.get('evalue', '')
            if ename == 'SystemExit' and evalue.isdigit():
                text = None  # Exit code handled via CellExecutionError
            else:
                text = '\n'.join(content.get('traceback', [])) + '\n'
        else:
            text = None

        if text:
            print(text, file=stream, end='', flush=True)

        return super().output(outs, msg, display_id, cell_index)


def main(argv=None):
    ap = ArgumentParser(
        prog='python -m princess',
        description="Run a Python notebook in the current environment, showing stdout & stderr."
    )
    ap.add_argument('notebook', help='Notebook file to run')

    save_opts = ap.add_mutually_exclusive_group()
    save_opts.add_argument(
        '--save', action='store_true',
        help="Save the notebook with output in the original file"
    )
    save_opts.add_argument(
        '--save-as', help="Save the notebook with output to another file"
    )
    ap.add_argument(
        '--discard-on-error', action='store_true',
        help="Don't save the notebook after an error. Use with --save/--save-as."
    )
    ap.add_argument(
        '--on-error-resume-next', action='store_true',
        help="Execute remaining cells after an error"
    )

    args = ap.parse_args(argv)

    out_filename = args.notebook if args.save else args.save_as
    if args.discard_on_error and not out_filename:
        print("--discard-on-error requires --save or --save-as", file=sys.stderr)
        return 2

    if args.discard_on_error and args.on_error_resume_next:
        print("--discard-on-error doesn't work with --on-error-resume-next", file=sys.stderr)
        return 2

    nb = nbformat.read(args.notebook, as_version=4)

    # Remove any existing ouput before executing
    for cell in nb.cells:
        if 'outputs' in cell:
            cell.outputs = []

    exit_code = 0
    try:
        PrincessNotebookClient(
            nb, allow_errors=args.on_error_resume_next,
        ).execute()
    except CellExecutionError as e:
        if e.ename == 'SystemExit' and e.evalue.isdigit():
            # From e.g. sys.exit(0) in the notebook - don't display an error.
            exit_code = int(e.evalue)
        else:
            print('\n\n' + '─' * 80)
            print(e, file=sys.stderr)
            exit_code = 1

    if out_filename and ((exit_code == 0) or not args.discard_on_error):
        nbformat.write(nb, out_filename)

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
