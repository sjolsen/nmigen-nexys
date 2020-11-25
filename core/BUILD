load("@pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "edge",
    srcs = ["edge.py"],
    deps = [requirement("nmigen")],
)

py_library(
    name = "flop",
    srcs = ["flop.py"],
    deps = [requirement("nmigen")],
)

py_library(
    name = "pwm",
    srcs = ["pwm.py"],
    deps = [requirement("nmigen")],
)

py_library(
    name = "shift_register",
    srcs = ["shift_register.py"],
    deps = [requirement("nmigen")],
)

py_library(
    name = "timer",
    srcs = ["timer.py"],
    deps = [
        ":util",
        requirement("nmigen"),
    ],
)

py_library(
    name = "util",
    srcs = ["util.py"],
    deps = [requirement("nmigen")],
)
