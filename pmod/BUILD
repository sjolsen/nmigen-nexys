load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_binary",
    "py_library",
)
package(default_visibility = ["//visibility:public"])

py_library(
    name = "pmod_8ld",
    srcs = ["pmod_8ld.py"],
    deps = [requirement("nmigen")],
)

py_binary(
    name = "pmod_8ld_demo",
    srcs = ["pmod_8ld_demo.py"],
    deps = [
        ":pmod_8ld",
        "//:nexysa7100t",
        "//:timer",
    ],
)
