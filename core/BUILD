load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "edge",
    srcs = ["edge.py"],
    deps = ["//pip:nmigen"],
)

py_library(
    name = "flop",
    srcs = ["flop.py"],
    deps = ["//pip:nmigen"],
)

py_library(
    name = "pwm",
    srcs = ["pwm.py"],
    deps = ["//pip:nmigen"],
)

py_library(
    name = "shift_register",
    srcs = ["shift_register.py"],
    deps = ["//pip:nmigen"],
)

py_library(
    name = "timer",
    srcs = ["timer.py"],
    deps = [
        ":util",
        "//pip:nmigen",
    ],
)

py_library(
    name = "top",
    srcs = ["top.py"],
    deps = [
        "//pip:absl",
        "//pip:nmigen",
    ],
)

py_library(
    name = "util",
    srcs = ["util.py"],
    deps = ["//pip:nmigen"],
)
