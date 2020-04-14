load("//bazel:top.bzl", "nmigen_design")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "memory",
    srcs = ["memory.py"],
    deps = [
        "//pip:minerva",
        "//pip:nmigen",
        "//vendor/xilinx:macro",
    ],
)

nmigen_design(
    name = "riscv_demo",
    size = "small",
    srcs = ["riscv_demo.py"],
    deps = [
        ":memory",
        "//bazel:top",
        "//board/nexysa7100t",
        "//debug:remote_bitbang",
        "//pip:absl",
        "//pip:minerva",
        "//pip:nmigen",
    ],
)
