load(":toolchain.bzl", "xilinx_toolchain")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

toolchain_type(name = "toolchain_type")

py_library(
    name = "macro",
    srcs = ["macro.py"],
    deps = ["//pip:nmigen"],
)

xilinx_toolchain(
    name = "xilinx_linux",
    vivado_path = "/opt/xilinx/Vivado/2019.2/bin/vivado",
    yosys_path = "/usr/bin/yosys",
)

toolchain(
    name = "xilinx_linux_toolchain",
    exec_compatible_with = ["@platforms//os:linux"],
    target_compatible_with = ["@platforms//os:linux"],
    toolchain = ":xilinx_linux",
    toolchain_type = ":toolchain_type",
)

xilinx_toolchain(
    name = "xilinx_windows",
    vivado_path = "C:\\Xilinx\\Vivado\\2019.2\\bin\\vivado.bat",
    yosys_path = "C:\\Program Files (x86)\\Yosys\\yosys.exe",
)

toolchain(
    name = "xilinx_windows_toolchain",
    exec_compatible_with = ["@platforms//os:windows"],
    target_compatible_with = ["@platforms//os:windows"],
    toolchain = ":xilinx_windows",
    toolchain_type = ":toolchain_type",
)
