load("@pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "srgb",
    srcs = ["srgb.py"],
    deps = [
        "//math:lut",
        requirement("nmigen"),
    ],
)
