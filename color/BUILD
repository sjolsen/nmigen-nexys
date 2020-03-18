load("@rules_python//python:defs.bzl", "py_library")
load("//core:top.bzl", "nmigen_deps")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "srgb",
    srcs = ["srgb.py"],
    deps = nmigen_deps + [
        "//math:lut",
    ],
)
