from argparse import ArgumentParser
import sys

from ipykernel.kernelspec import RESOURCES, get_kernel_dict
from jupyter_client import AsyncKernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient
import nbformat


class CurrentEnvKernelSpecManager(KernelSpecManager):
    """Always launch a Python kernel with the current Python interpreter.

    Ignores the kernel name (from the notebook)
    """
    def get_kernel_spec(self, kernel_name):
        return self.kernel_spec_class(resource_dir=RESOURCES, **get_kernel_dict())


class PrincessNotebookClient(NotebookClient):
    def create_kernel_manager(self):
        return AsyncKernelManager(kernel_spec_manager=CurrentEnvKernelSpecManager())

    def output(self, outs, msg, display_id, cell_index):
        msg_type = msg['msg_type']
        content = msg['content']
        stream = sys.stdout
        if msg_type == 'stream':
            if content.get('name') == 'stderr':
                stream = sys.stderr
            text = content.get('text')
        elif msg_type == 'display_data':
            text = content.get('data', {}).get('text/plain')
        elif msg_type == 'error':
            text = '\n'.join(content.get('traceback', []))
        else:
            text = None

        if text:
            print(text, file=stream, end='')

        return super().output(outs, msg, display_id, cell_index)


def main(argv=None):
    ap = ArgumentParser()
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
        '--on-error-resume-next', action='store_true',
        help="Execute remaining cells after an error"
    )

    args = ap.parse_args(argv)

    nb = nbformat.read(args.notebook, as_version=4)

    nb_out = PrincessNotebookClient(
        nb, allow_errors=args.on_error_resume_next,
    ).execute()

    out_filename = args.notebook if args.save else args.save_as
    nbformat.write(nb_out, out_filename)


if __name__ == '__main__':
    sys.exit(main())
