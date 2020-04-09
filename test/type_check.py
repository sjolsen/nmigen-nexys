import os
import sys

from absl import app
from absl import flags
from pytype import single
from rules_python.python.runfiles import runfiles

flags.DEFINE_string('input', None, 'Python source file path')
flags.DEFINE_string('output', None, 'Output file path')
flags.DEFINE_list('imports', None, 'PYTHONPATH entries for analysis')
flags.mark_flags_as_required(['input', 'output', 'imports'])

FLAGS = flags.FLAGS


def main(argv):
    r = runfiles.Create()
    # imports = [r.Rlocation(i) for i in FLAGS.imports]
    # for i in FLAGS.imports:
    # for root, _, files in os.walk('.'):
    #     for f in files:
    #         print(os.path.join(root, f))
    print(os.getcwd())
    sys.argv = [
        argv[0],
        FLAGS.input,
        '-o', FLAGS.output,
        '--pythonpath', os.pathsep.join(os.path.abspath(i) for i in ['..'] + FLAGS.imports),
    ]
    print(f'Invoking pytype with args {sys.argv!r}')
    return single.main()

if __name__ == '__main__':
    app.run(main)
