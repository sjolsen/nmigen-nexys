load("//bazel:top.bzl", "nmigen_design")
load("//vendor/gcc:tools.bzl", "riscv_cc_binary")
load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])

riscv_cc_binary(
    name = "deadbeef",
    srcs = ["deadbeef.S"],
    linker_script = "start.ld",
)

py_library(
    name = "peripheral",
    srcs = ["peripheral.py"],
    deps = [
        "//core:util",
        "//display:seven_segment",
        "//vendor/xilinx:macro",
        requirement("minerva"),
        requirement("nmigen"),
    ],
)

py_test(
    name = "peripheral_test",
    srcs = ["peripheral_test.py"],
    data = [":deadbeef.bin"],
    deps = [
        ":peripheral",
        "//core:util",
        "//test:event",
        "//test:test_util",
        "@rules_python//python/runfiles",
        requirement("minerva"),
        requirement("nmigen"),
    ],
)

nmigen_design(
    name = "riscv_demo",
    size = "small",
    srcs = ["riscv_demo.py"],
    data = [":main.bin"],
    deps = [
        ":peripheral",
        "//bazel:top",
        "//board/nexysa7100t",
        "//debug:remote_bitbang",
        "@rules_python//python/runfiles",
        requirement("absl-py"),
        requirement("minerva"),
        requirement("nmigen"),
    ],
)

riscv_cc_binary(
    name = "main",
    srcs = [
        "main.c",
        "main.S",
    ],
    linker_script = "start.ld",
)
