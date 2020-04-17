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
    attrs = {
        "src": attr.label(
            mandatory = True,
            allow_single_file = True,
        ),
        "out": attr.string(
            mandatory = True,
        ),
    },
    toolchains = ["@bazel_tools//tools/cpp:toolchain_type"],
    outputs = {
        "bin": "%{out}",
    }
)
