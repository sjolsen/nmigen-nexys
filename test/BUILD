load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "event",
    srcs = ["event.py"],
    deps = [
        ":test_util",
        "//core:edge",
        "//core:util",
        requirement("nmigen"),
    ],
)

py_test(
    name = "sim_perf_test",
    size = "large",
    srcs = ["sim_perf_test.py"],
    deps = [
        "//board/nexysa7100t:uart_demo",
        "//core:util",
        "//serial:uart",
        "//test:test_util",
        requirement("absl-py"),
        requirement("nmigen"),
    ],
)

py_library(
    name = "test_util",
    srcs = ["test_util.py"],
    deps = [
        "//core:util",
        requirement("nmigen"),
    ],
)
