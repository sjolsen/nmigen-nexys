"""Bazel rules for building nMigen designs."""

load("@pip_deps//:requirements.bzl", "requirement")
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

# The pip rules unfortunately aren't smart enough to figure out all the
# transitive dependencies. TODO: Fix this ugly mess!!!
absl_deps = [
    requirement("absl-py"),
    requirement("six"),  # Needed by absl-py
]

nmigen_deps = [
    requirement("nmigen"),
    requirement("jinja2"),  # Needed by nmigen
    requirement("markupsafe"),  # Needed by jinja2
]

nmigen_sim_deps = nmigen_deps + [
    requirement("pyvcd"),  # Needed by nmigen
    requirement("six"),  # Needed by pyvcd
]
