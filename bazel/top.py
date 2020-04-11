"""Command-line entry-point for Platform.build."""

from absl import app
from absl import flags
from nmigen import *
from nmigen.build import *


flags.DEFINE_string('name', 'top', 'Top module name')
flags.DEFINE_string('build_dir', 'build', 'Build output directory')
flags.DEFINE_string('action', None, '"elaborate", "build", or "program"')

FLAGS = flags.FLAGS


def build(platform: Platform, top: Elaboratable):
    if FLAGS.action == 'elaborate':
        platform.prepare(top, FLAGS.name)
    elif FLAGS.action == 'build':
        plan = platform.prepare(top, FLAGS.name)
        plan.execute_local(FLAGS.build_dir)
    elif FLAGS.action == 'program':
        platform.toolchain_program(LocalBuildProducts(FLAGS.build_dir),
                                   FLAGS.name)
    else:
        raise app.UsageError(f'Invalid action: {FLAGS.action}')
