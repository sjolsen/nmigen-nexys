"""Bazel rules for building nMigen designs."""

load("@rules_python//python:defs.bzl", "py_binary")
load("//test:test.bzl", "elaboration_test")

def nmigen_design(name = None, *args, **kwargs):
    """An nMigen design using nmigen_nexys.core.top.main.

    This macro creates a simple py_binary for the design. It also automatically
    creates an elaboration test named "%{name}.elaborate".

    Args:
        name: The name of the target.
        *args: Not allowed.
        **kwargs: Arguments to be passed to py_binary.
    """
    if args:
        fail("Illegal positional arguments", args)
    py_binary(
        name = name,
        **kwargs
    )
    elaboration_test(
        name = "%s.elaborate" % name,
        top = name,
    )
