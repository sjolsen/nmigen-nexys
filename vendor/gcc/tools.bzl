def _baremetal_riscv_transition(settings, attr):
    _ignore = (settings, attr)
    return [
        {"//command_line_option:platforms" : "//bazel/platforms:baremetal_riscv"},
    ]

baremetal_riscv_transition = transition(
    implementation = _baremetal_riscv_transition,
    inputs = [],
    outputs = ["//command_line_option:platforms"]
)

def _riscv_flat_bin(ctx):
    cc = ctx.toolchains["@bazel_tools//tools/cpp:toolchain_type"]
    args = ctx.actions.args()
    args.add("-I", "elf32-littleriscv")
    args.add("-O", "binary")
    args.add(ctx.file.src)
    args.add(ctx.outputs.bin)
    ctx.actions.run(
        executable = cc.objcopy_executable,
        arguments = [args],
        outputs = [ctx.outputs.bin],
        inputs = [ctx.file.src],
    )

riscv_flat_bin = rule(
    implementation = _riscv_flat_bin,
    cfg = baremetal_riscv_transition,
    attrs = {
        "src": attr.label(
            mandatory = True,
            allow_single_file = True,
        ),
        "out": attr.string(
            mandatory = True,
        ),
        "_whitelist_function_transition": attr.label(
            default = "@bazel_tools//tools/whitelists/function_transition_whitelist"
        )
    },
    toolchains = ["@bazel_tools//tools/cpp:toolchain_type"],
    outputs = {
        "bin": "%{out}",
    }
)

_RISCV_BAREMETAL_COPTS = ["-ffreestanding", "-nostdlib"]

def riscv_cc_binary(name = None, srcs = [], linker_script = None, *args, **kwargs):
    if args:
        fail("Illegal positional arguments", args)
    if linker_script == None:
        fail("Must provide a linker script", linker_script)
    native.cc_binary(
        name = name,
        srcs = srcs,
        additional_linker_inputs = [linker_script],
        copts = _RISCV_BAREMETAL_COPTS,
        linkopts = _RISCV_BAREMETAL_COPTS + ["-Wl,-T", "-Wl,$(location %s)" % linker_script],
        # TODO: https://github.com/bazelbuild/bazel/issues/3780
        # target_compatible_with = [
        #     "//bazel/platforms/cpu:riscv",
        #     "@platforms//os:none",
        # ],
        tags = ["manual"],
        **kwargs
    )
    riscv_flat_bin(
        name = "%s_flat" % name,
        src = name,
        out = "%s.bin" % name,
    )
