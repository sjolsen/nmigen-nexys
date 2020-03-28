"""Command-line entry-point for Platform.build."""

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


def build(platform: Platform, top: Elaboratable):
    platform.build(
        top, name=FLAGS.name, build_dir=FLAGS.build_dir, do_build=FLAGS.build,
        program_opts=FLAGS.program_opts, do_program=FLAGS.program)
