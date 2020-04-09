load(
    "@rules_python//python:defs.bzl",
    "py_binary",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])

filegroup(
    name = "elaboration_test",
    srcs = ["elaboration_test.py"],
)

py_binary(
    name = "no_synthesis",
    srcs = ["no_synthesis.py"],
)

py_test(
    name = "sim_perf_test",
    size = "large",
    srcs = ["sim_perf_test.py"],
    deps = [
        "//board/nexysa7100t:uart_demo",
        "//core:util",
        "//pip:absl",
        "//pip:nmigen",
        "//serial:uart",
        "//test:test_util",
    ],
)

py_library(
    name = "test_util",
    srcs = ["test_util.py"],
    deps = [
        "//core:util",
        "//pip:nmigen",
    ],
)
