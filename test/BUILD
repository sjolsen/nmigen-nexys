load("@pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")

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
    name = "util",
    srcs = ["util.py"],
    deps = [requirement("nmigen")],
)
