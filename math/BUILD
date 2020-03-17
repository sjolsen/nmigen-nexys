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
    srcs = ["bcd_test.py"],
    deps = [
        ":bcd",
        "//test:util",
        requirement("nmigen"),
        requirement("six"),  # TODO: Fix this, needed by the VCD library
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
    srcs = ["square_fraction_test.py"],
    deps = [
        ":square_fraction",
        requirement("nmigen"),
        requirement("six"),  # TODO: Fix this, needed by the VCD library
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
    srcs = ["trig_test.py"],
    deps = [
        ":lut",
        ":trig",
        "//core:util",
        requirement("nmigen"),
        requirement("six"),  # TODO: Fix this, needed by the VCD library
    ],
)
