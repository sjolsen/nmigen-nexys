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

py_binary(
    name = "display",
    srcs = ["display.py"],
    deps = [
        ":bcd",
        ":nexysa7100t",
        ":pwm",
    ],
)

py_library(
    name = "lut",
    srcs = ["lut.py"],
    deps = [requirement("nmigen")],
)

py_library(
    name = "trig",
    srcs = ["trig.py"],
    deps = [":lut"],
)

py_test(
    name = "trig_test",
    srcs = ["trig_test.py"],
    deps = [
        requirement("six"),  # TODO: Fix this, needed by the VCD library
        ":trig",
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

py_library(
    name = "srgb",
    srcs = ["srgb.py"],
    deps = [":lut"],
)

py_library(
    name = "timer",
    srcs = ["timer.py"],
    deps = [requirement("nmigen")],
)

py_binary(
    name = "demo",
    srcs = ["demo.py"],
    deps = [
        ":nexysa7100t",
        ":trig",
        ":pwm",
        ":srgb",
        ":timer",
    ],
)

py_binary(
    name = "manual_brightness",
    srcs = ["manual_brightness.py"],
    deps = [
        ":bcd",
        ":display",
        ":srgb",
        ":nexysa7100t",
    ],
)

py_test(
    name = "manual_brightness_test",
    srcs = ["manual_brightness_test.py"],
    deps = [
        requirement("six"),  # TODO: Fix this, needed by the VCD library
        ":bcd",
        ":manual_brightness",
    ],
)