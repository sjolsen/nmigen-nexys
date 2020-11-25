load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "remote_bitbang",
    srcs = ["remote_bitbang.py"],
    deps = [
        "//serial:uart",
        requirement("nmigen"),
    ],
)

py_test(
    name = "remote_bitbang_test",
    size = "small",
    srcs = ["remote_bitbang_test.py"],
    deps = [
        ":remote_bitbang",
        "//core:util",
        "//serial:uart",
        "//test:event",
        "//test:test_util",
        requirement("nmigen"),
    ],
)
