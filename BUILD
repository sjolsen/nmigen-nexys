load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
    name = "nexysa7100t",
    srcs = ["nexysa7100t.py"],
    deps = ["@nmigen_boards//:nmigen_boards"],
)

py_binary(
    name = "demo",
    srcs = ["demo.py"],
    deps = [":nexysa7100t"],
)