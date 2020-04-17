load(
    "@rules_python//python:defs.bzl",
    "py_library",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "remote_bitbang",
    srcs = ["remote_bitbang.py"],
    deps = [
        "//pip:nmigen",
        "//serial:uart",
    ],
)

py_test(
    name = "remote_bitbang_test",
    size = "small",
    srcs = ["remote_bitbang_test.py"],
    deps = [
        ":remote_bitbang",
        "//core:util",
        "//pip:nmigen",
        "//serial:uart",
        "//test:event",
        "//test:test_util",
    ],
)
