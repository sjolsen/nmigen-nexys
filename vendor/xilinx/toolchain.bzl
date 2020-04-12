XilinxToolchainInfo = provider(fields = ["vivado", "yosys"])

def _xilinx_toolchain(ctx):
    return [platform_common.ToolchainInfo(
        xilinx = XilinxToolchainInfo(
            vivado = ctx.attr.vivado_path,
            yosys = ctx.attr.yosys_path,
        ),
    )]

xilinx_toolchain = rule(
    implementation = _xilinx_toolchain,
    attrs = {
        "vivado_path": attr.string(mandatory = True),
        "yosys_path": attr.string(mandatory = True),
    },
)
