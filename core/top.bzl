"""Bazel rules for building nMigen designs."""
load("@rules_python//python:defs.bzl", "py_binary")
load("//test:test.bzl", "elaboration_test")


def nmigen_design(name=None, *args, **kwargs):
    if args:
        fail('Illegal positional arguments', args)
    py_binary(
        name = name,
        **kwargs
    )
    # TODO: elaboration_test.py needs Yosys and Vivado
    # elaboration_test(
    #     name = "%s.elaborate" % name,
    #     top = name,
    # )
