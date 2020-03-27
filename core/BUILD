load("@rules_python//python:defs.bzl", "py_library")
load(
    "//core:top.bzl",
    "absl_deps",
    "nmigen_deps",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "edge",
    srcs = ["edge.py"],
    deps = nmigen_deps,
)

py_library(
    name = "flop",
    srcs = ["flop.py"],
    deps = nmigen_deps,
)

py_library(
    name = "pwm",
    srcs = ["pwm.py"],
    deps = nmigen_deps,
)

py_library(
    name = "shift_register",
    srcs = ["shift_register.py"],
    deps = nmigen_deps,
)

py_library(
    name = "timer",
    srcs = ["timer.py"],
    deps = nmigen_deps,
)

py_library(
    name = "top",
    srcs = ["top.py"],
    deps = absl_deps + nmigen_deps,
)

py_library(
    name = "util",
    srcs = ["util.py"],
    deps = nmigen_deps + [
        "//test:util"
    ],
)
