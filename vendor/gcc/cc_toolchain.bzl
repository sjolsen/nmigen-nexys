load("@bazel_tools//tools/cpp:cc_toolchain_config_lib.bzl", "tool_path")

_TOOLS = ["gcc", "ld", "ar", "cpp", "gcov", "nm", "objcopy", "objdump", "strip"]

def _cc_toolchain_config(ctx):
    tool_paths = [
        tool_path(
            name = tool,
            path = "{idir}/bin/{target}-{tool}".format(
                idir = ctx.attr.installation_directory,
                target = ctx.attr.target_system_name,
                tool = tool),
        )
        for tool in _TOOLS
    ]
    return cc_common.create_cc_toolchain_config_info(
        ctx = ctx,
        cxx_builtin_include_directories = ctx.attr.cxx_builtin_include_directories,
        toolchain_identifier = ctx.attr.toolchain_identifier,
        host_system_name = ctx.attr.host_system_name,
        target_system_name = ctx.attr.target_system_name,
        target_cpu = ctx.attr.target_cpu,
        target_libc = ctx.attr.target_libc,
        compiler = ctx.attr.compiler,
        abi_version = ctx.attr.abi_version,
        abi_libc_version = ctx.attr.abi_libc_version,
        tool_paths = tool_paths,
    )

cc_toolchain_config = rule(
    implementation = _cc_toolchain_config,
    attrs = {
        # Custom args
        "installation_directory": attr.string(mandatory = True),
        # Standard args
        "cxx_builtin_include_directories": attr.string_list(),
        "toolchain_identifier": attr.string(mandatory = True),
        "host_system_name": attr.string(mandatory = True),
        "target_system_name": attr.string(mandatory = True),
        "target_cpu": attr.string(mandatory = True),
        "target_libc": attr.string(default = "unknown"),
        "compiler": attr.string(mandatory = True),
        "abi_version": attr.string(default = "unknown"),
        "abi_libc_version": attr.string(default = "unknown"),
    },
    provides = [CcToolchainConfigInfo],
)
