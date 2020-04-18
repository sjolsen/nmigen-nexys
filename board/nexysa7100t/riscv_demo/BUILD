load("//bazel:top.bzl", "nmigen_design")
load("//vendor/gcc:tools.bzl", "riscv_flat_bin")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])

# TODO: Automate these rules
cc_binary(
    name = "deadbeef",
    srcs = ["deadbeef.S"],
    additional_linker_inputs = ["start.ld"],
    copts = ["-ffreestanding", "-nostdlib"],
    linkopts = ["-ffreestanding", "-nostdlib", "-Wl,-T", "-Wl,$(location start.ld)"],
    # TODO: https://github.com/bazelbuild/bazel/issues/3780
    # target_compatible_with = [
    #     "//bazel/platforms/cpu:riscv",
    #     "@platforms//os:none",
    # ],
    tags = ["manual"],
)

# Build with:
riscv_flat_bin(
    name = "deadbeef_flat",
    src = ":deadbeef",
    out = "deadbeef.bin",
)

py_library(
    name = "peripheral",
    srcs = ["peripheral.py"],
    deps = [
        "//core:util",
        "//pip:minerva",
        "//pip:nmigen",
        "//display:seven_segment",
        "//vendor/xilinx:macro",
    ],
)

py_test(
    name = "peripheral_test",
    srcs = ["peripheral_test.py"],
    data = [":deadbeef.bin"],
    deps = [
        ":peripheral",
        "//core:util",
        "//pip:minerva",
        "//pip:nmigen",
        "//test:event",
        "//test:test_util",
        "@rules_python//python/runfiles",
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
        "//pip:absl",
        "//pip:minerva",
        "//pip:nmigen",
        "@rules_python//python/runfiles",
    ],
)

cc_binary(
    name = "main",
    srcs = [
        "main.c",
        "main.S",
    ],
    additional_linker_inputs = ["start.ld"],
    copts = ["-ffreestanding", "-nostdlib"],
    linkopts = ["-ffreestanding", "-nostdlib", "-Wl,-T", "-Wl,$(location start.ld)"],
    # TODO: https://github.com/bazelbuild/bazel/issues/3780
    # target_compatible_with = [
    #     "//bazel/platforms/cpu:riscv",
    #     "@platforms//os:none",
    # ],
    tags = ["manual"],
)

# Build with:
riscv_flat_bin(
    name = "main_flat",
    src = ":main",
    out = "main.bin",
)
