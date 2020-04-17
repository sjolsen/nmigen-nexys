load(":cc_toolchain.bzl", "cc_toolchain_config")

filegroup(name = "empty")

cc_toolchain_config(
    name = "riscv_cc_toolchain_config",
    installation_directory = "/opt/riscv32",
    toolchain_identifier = "riscv-toolchain",
    host_system_name = "x86_64-linux-gnu",
    target_system_name = "riscv32-unknown-elf",
    target_cpu = "riscv",
    target_libc = "unknown",
    compiler = "gcc",
    abi_version = "unknown",
    abi_libc_version = "unknown",
)

cc_toolchain(
    name = "riscv_cc_toolchain",
    # toolchain_identifier = "riscv-toolchain",
    toolchain_config = ":riscv_cc_toolchain_config",
    all_files = ":empty",
    compiler_files = ":empty",
    dwp_files = ":empty",
    linker_files = ":empty",
    objcopy_files = ":empty",
    strip_files = ":empty",
    # supports_param_files = 0,
)

toolchain(
    name = "riscv_toolchain",
    exec_compatible_with = [
        "@platforms//cpu:x86_64",
        "@platforms//os:linux",
    ],
    target_compatible_with = [
        "//bazel/platforms/cpu:riscv",
        "@platforms//os:none",
    ],
    toolchain = ":riscv_cc_toolchain",
    toolchain_type = "@bazel_tools//tools/cpp:toolchain_type",
)
