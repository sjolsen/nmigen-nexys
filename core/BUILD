load("@pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "pwm",
    srcs = ["pwm.py"],
    deps = [requirement("nmigen")],
)

py_library(
    name = "timer",
    srcs = ["timer.py"],
    deps = [requirement("nmigen")],
)

py_library(
    name = "top",
    srcs = ["top.py"],
    deps = [
        requirement("absl-py"),
        requirement("nmigen"),
        requirement("six"),  # TODO: Fix this, needed by absl
    ],
)

py_library(
    name = "util",
    srcs = ["util.py"],
    deps = [requirement("nmigen")],
)
