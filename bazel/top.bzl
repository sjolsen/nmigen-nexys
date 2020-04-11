"""Bazel rules for building nMigen designs."""

load("@rules_python//python:defs.bzl", "py_binary")
load("//test:test.bzl", "elaboration_test")

def nmigen_design(name = None, size = None, *args, **kwargs):
    """An nMigen design using nmigen_nexys.core.top.build.

    This macro creates a simple py_binary for the design. It also automatically
    creates an elaboration test named "%{name}.elaborate".

    Args:
        name: The name of the target.
        size: The size of the elaboration test.
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
        size = size,
    )
    native.genrule(
        name = "%s.build" % name,
        srcs = [],
        outs = ["%s.bit" % name],
        tools = [name],
        cmd = "$(location %s) --action=build --build_dir=$(@D)" % name,
        tags = [
            "manual",  # Don't include in build wildcards
            "exclusive",  # Don't build in parallel
        ],
    )
