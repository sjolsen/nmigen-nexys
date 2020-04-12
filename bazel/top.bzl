"""Bazel rules for building nMigen designs."""

load("@rules_python//python:defs.bzl", "py_binary")
load("//test:test.bzl", "elaboration_test")

def __build_design(ctx):
    tools = ctx.toolchains["//vendor/xilinx:toolchain_type"].xilinx
    ctx.actions.run(
        outputs = [ctx.outputs.bit],
        inputs = [],
        executable = ctx.executable.design,
        arguments = ["--action=build", "--build_dir=" + ctx.outputs.bit.dirname],
        env = {
            "PROCESSOR_ARCHITECTURE": "AMD64",  # TODO: Hack hack hack
            "VIVADO": tools.vivado,
            "YOSYS": tools.yosys,
        },
    )

_build_design = rule(
    implementation = __build_design,
    attrs = {
        "design": attr.label(
            mandatory = True,
            executable = True,
            cfg = "exec",
        ),
        "bit": attr.string(
            mandatory = True,
        ),
    },
    toolchains = ["//vendor/xilinx:toolchain_type"],
    outputs = {
        "bit": "%{bit}",
    },
)

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
    _build_design(
        name = "%s.build" % name,
        design = name,
        bit = "%s.bit" % name,
        tags = [
            "manual",  # Don't include in build wildcards
            "exclusive",  # Don't build in parallel
        ],
    )
