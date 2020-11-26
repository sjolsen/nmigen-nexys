"""Bazel rules for building nMigen designs."""

load("@rules_python//python:defs.bzl", "py_binary")
load("//test:test.bzl", "elaboration_test")

NmigenBuildInfo = provider(fields = ["design", "build_dir"])

def __build_design(ctx):
    tools = ctx.toolchains["//vendor/xilinx:toolchain_type"].xilinx
    bdir = ctx.actions.declare_directory(ctx.label.name + "_build")
    genbit = ctx.actions.declare_file(ctx.label.name + "_build/top.bit")
    ctx.actions.run(
        outputs = [bdir, genbit],
        inputs = [],
        executable = ctx.executable.design,
        arguments = ["--action=build", "--build_dir=" + bdir.path],
        env = {
            "HOME": ctx.label.name + "_home",
            "VIVADO": tools.vivado,
            "YOSYS": "/opt/fpga/bin/yosys",
            "NEXTPNR_ECP5": "/opt/fpga/bin/nextpnr-ecp5",
            "ECPPACK": "/opt/fpga/bin/ecppack",
        },
    )
    ctx.actions.run_shell(
        outputs = [ctx.outputs.bit],
        inputs = [genbit],
        command = "cp %s %s" % (genbit.path, ctx.outputs.bit.path),
    )
    return [NmigenBuildInfo(
        design = ctx.attr.design[DefaultInfo],
        build_dir = bdir,
    )]

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

def __program_design(ctx):
    products = ctx.attr.products[NmigenBuildInfo]
    ctx.actions.write(
        content = "{exe} --action=program --build_dir={build_dir}".format(
            exe = products.design.files_to_run.executable.short_path,
            build_dir = products.build_dir.short_path),
        output = ctx.outputs.executable,
        is_executable = True,
    )
    return [DefaultInfo(
        runfiles = ctx.runfiles([products.build_dir]).merge(products.design.default_runfiles),
    )]

_program_design = rule(
    implementation = __program_design,
    attrs = {
        "products": attr.label(
            mandatory = True,
            providers = [NmigenBuildInfo],
        ),
    },
    executable = True,
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
    _program_design(
        name = "%s.program" % name,
        products = "%s.build" % name,
        tags = ["manual"],
    )
