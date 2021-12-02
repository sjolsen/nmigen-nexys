load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "bcd",
    srcs = ["bcd.py"],
    deps = [requirement("nmigen")],
)

py_test(
    name = "bcd_test",
    size = "small",
    srcs = ["bcd_test.py"],
    deps = [
        ":bcd",
        "//core:util",
        "//test:test_util",
        requirement("nmigen"),
    ],
)

py_library(
    name = "delta_sigma",
    srcs = ["delta_sigma.py"],
    deps = [
        "//core:util",
        requirement("nmigen"),
    ],
)

py_test(
    name = "delta_sigma_test",
    size = "small",
    srcs = ["delta_sigma_test.py"],
    deps = [
        ":delta_sigma",
        "//core:timer",
        "//core:util",
        "//test:test_util",
        requirement("nmigen"),
    ],
)

py_library(
    name = "lfsr",
    srcs = ["lfsr.py"],
    deps = [
        "//core:shift_register",
        requirement("nmigen"),
    ],
)

py_library(
    name = "lut",
    srcs = ["lut.py"],
    deps = [
        "//core:util",
        requirement("nmigen"),
    ],
)

py_library(
    name = "square_fraction",
    srcs = ["square_fraction.py"],
    deps = [requirement("nmigen")],
)

py_test(
    name = "square_fraction_test",
    size = "small",
    srcs = ["square_fraction_test.py"],
    deps = [
        ":square_fraction",
        requirement("nmigen"),
    ],
)

py_library(
    name = "trig",
    srcs = ["trig.py"],
    deps = [
        ":lut",
        "//core:util",
        requirement("nmigen"),
    ],
)

py_test(
    name = "trig_test",
    size = "small",
    srcs = ["trig_test.py"],
    deps = [
        ":lut",
        ":trig",
        "//core:util",
        requirement("nmigen"),
    ],
)
