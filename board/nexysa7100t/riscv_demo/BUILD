load("//bazel:top.bzl", "nmigen_design")
load("//vendor/gcc:tools.bzl", "riscv_flat_bin")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "peripheral",
    srcs = ["peripheral.py"],
    data = [":start.bin"],
    deps = [
        "//core:util",
        "//pip:minerva",
        "//pip:nmigen",
        "//display:seven_segment",
        "//vendor/xilinx:macro",
        "@rules_python//python/runfiles",
    ],
)

py_test(
    name = "peripheral_test",
    srcs = ["peripheral_test.py"],
    deps = [
        ":peripheral",
        "//core:util",
        "//pip:minerva",
        "//pip:nmigen",
        "//test:event",
        "//test:test_util",
    ],
)

nmigen_design(
    name = "riscv_demo",
    size = "small",
    srcs = ["riscv_demo.py"],
    deps = [
        ":peripheral",
        "//bazel:top",
        "//board/nexysa7100t",
        "//debug:remote_bitbang",
        "//pip:absl",
        "//pip:minerva",
        "//pip:nmigen",
    ],
)

cc_binary(
    name = "start",
    srcs = ["start.S"],
    additional_linker_inputs = ["start.ld"],
    copts = ["-ffreestanding", "-nostdlib"],
    linkopts = ["-ffreestanding", "-nostdlib", "-Wl,-T", "-Wl,$(location start.ld)"],
    # TODO: https://github.com/bazelbuild/bazel/issues/3780
    # target_compatible_with = [
    #     "//platforms/cpu:riscv",
    #     "@platforms//os:none",
    # ],
    tags = ["manual"],
)

# Build with:
riscv_flat_bin(
    name = "start_flat",
    src = ":start",
    out = "start.bin",
)
