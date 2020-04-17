load(
    "@rules_python//python:defs.bzl",
    "py_binary",
    "py_library",
)

package(default_visibility = ["//visibility:public"])

filegroup(
    name = "script",
    srcs = ["script.py"],
)

py_library(
    name = "top",
    srcs = ["top.py"],
    deps = [
        "//pip:absl",
        "//pip:nmigen",
    ],
)
