load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_binary",
    "py_library",
    "py_test",
)

py_binary(
    name = "nexysa7100t",
    srcs = ["nexysa7100t.py"],
    deps = [requirement("nmigen_boards")],
)

py_library(
    name = "bcd",
    srcs = ["bcd.py"],
    deps = [requirement("nmigen")],
)

py_test(
    name = "bcd_test",
    srcs = ["bcd_test.py"],
    deps = [
        requirement("six"),  # TODO: Fix this, needed by the VCD library
        ":bcd",
    ],
)

py_library(
    name = "pwm",
    srcs = ["pwm.py"],
    deps = [requirement("nmigen")],
)

py_library(
    name = "square_fraction",
    srcs = ["square_fraction.py"],
    deps = [requirement("nmigen")],
)

py_test(
    name = "square_fraction_test",
    srcs = ["square_fraction_test.py"],
    deps = [
        requirement("six"),  # TODO: Fix this, needed by the VCD library
        ":square_fraction",
    ],
)

py_binary(
    name = "demo",
    srcs = ["demo.py"],
    deps = [
        ":nexysa7100t",
        ":pwm",
        ":square_fraction",
    ],
)

py_binary(
    name = "manual_brightness",
    srcs = ["manual_brightness.py"],
    deps = [
        ":nexysa7100t",
        ":bcd",
        ":pwm",
        ":square_fraction",
    ],
)