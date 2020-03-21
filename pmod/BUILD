load(
    "@rules_python//python:defs.bzl",
    "py_library",
)
load(
    "//core:top.bzl",
    "nmigen_deps",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "pmod_8ld",
    srcs = ["pmod_8ld.py"],
    deps = nmigen_deps,
)
