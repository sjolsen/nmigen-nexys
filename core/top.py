"""Command-line entry-point for Platform.build."""

from typing import List

from absl import app
from absl import flags
from nmigen import *
from nmigen.build import *


flags.DEFINE_string('name', 'top', 'Top module name')
flags.DEFINE_string('build_dir', 'build', 'Build output directory')
flags.DEFINE_boolean('build', True, 'Build the bitstream')
flags.DEFINE_multi_string(
    'program_opts', None, 'Options to be passed to the backend toolchain')
flags.DEFINE_boolean('program', False, 'Write the bitstream to the device')

FLAGS = flags.FLAGS


def _build(argv: List[str], platform: Platform, top: Elaboratable):
    if len(argv) > 1:
        raise app.UsageError(
            f"Don't know how to handle command-line arguments: {argv[1:]}")
    platform.build(
        top, name=FLAGS.name, build_dir=FLAGS.build_dir, do_build=FLAGS.build,
        program_opts=FLAGS.program_opts, do_program=FLAGS.program)


def main(platform: Platform, top: Elaboratable):
    """Run platform.build(top) using command-line options."""
    app.run(lambda argv: _build(argv, platform, top))
