import os
import platform
import sys
import tempfile

from absl import app
from absl import flags
from importlab import environment
from importlab import fs
from importlab import graph
from pytype import single
from pytype.tools.analyze_project import pytype_runner

flags.DEFINE_string('input', None, 'Python source file path')
flags.DEFINE_string('output', None, 'Output file path')
flags.DEFINE_list('imports', None, 'PYTHONPATH entries for analysis')
flags.DEFINE_string('action', None, '"infer" or "check"')
flags.mark_flags_as_required(['input', 'output', 'imports', 'action'])

FLAGS = flags.FLAGS


def main(argv):
    # pythonpath = [os.path.abspath(i) for i in ['..'] + FLAGS.pythonpath]
    # prefixes = set()
    # for i in pythonpath:
    #     try:
    #         common = os.path.commonpath([i, FLAGS.input])
    #     except ValueError:
    #         continue
    #     if common:
    #         prefixes.add(os.path.relpath(FLAGS.input, start=i))
    path = fs.Path()
    for p in FLAGS.imports:
        path.add_path(p, 'os')
    env = environment.Environment(path, sys.version_info[0:2])

    import_graph = graph.ImportGraph.create(env, [FLAGS.input], trim=True)
    deps = {k[0].name: v for k, v in pytype_runner.deps_from_import_graph(import_graph)}
    module = import_graph.provenance[os.path.abspath(FLAGS.input)]
    ifile = tempfile.NamedTemporaryFile(mode='wt', delete=False)
    try:
        for dep in deps[module.module_name]:
            ifile.write(f'{dep.name} {dep.path}\n')
        ifile.close()
        if FLAGS.action == 'infer':
            sys.argv = [
                argv[0],
                '--imports_info', ifile.name,
                # '--module-name', _,
                '-o', FLAGS.output,
                # --no-report-errors --nofail --quick
                FLAGS.input,
            ]
        elif FLAGS.action == 'check':
            sys.argv = [
                argv[0],
                '--imports_info', ifile.name,
                # '--module-name', _,
                '-o', FLAGS.output,
                '--analyze-annotated',
                # --nofail --quick
                FLAGS.input,
            ]
        else:
            app.UsageError(f'Invalid action: {FLAGS.action}')
        print(f'Invoking pytype with args {sys.argv!r}')
        return single.main()
    finally:
        os.remove(ifile.name)

if __name__ == '__main__':
    app.run(main)
