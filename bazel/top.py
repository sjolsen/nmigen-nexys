"""Command-line entry-point for Platform.build."""
import os
from absl import app
from absl import flags
from nmigen import *
from nmigen.build import *
from nmigen.build.run import LocalBuildProducts


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
        # TODO: Shouldn't need to create the elaboratable at all, but if it is
        # created it needs to be "used"
        platform.prepare(top, FLAGS.name)
        platform.toolchain_program(LocalBuildProducts(FLAGS.build_dir),
                                   FLAGS.name)
    else:
        raise app.UsageError(f'Invalid action: {FLAGS.action}')
