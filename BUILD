load("@pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
    name = "nexysa7100t",
    srcs = ["nexysa7100t.py"],
    deps = [requirement("nmigen_boards")],
)