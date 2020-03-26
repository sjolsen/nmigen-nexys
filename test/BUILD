load(
    "@rules_python//python:defs.bzl",
    "py_binary",
    "py_library",
)
load("//core:top.bzl", "nmigen_sim_deps")

package(default_visibility = ["//visibility:public"])

filegroup(
    name = "elaboration_test",
    srcs = ["elaboration_test.py"],
)

py_binary(
    name = "no_synthesis",
    srcs = ["no_synthesis.py"],
)

py_library(
    name = "test_util",
    srcs = ["test_util.py"],
    deps = nmigen_sim_deps + [
        "//core:util",
    ],
)
