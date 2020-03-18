load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)
load("//core:top.bzl", "nmigen_deps", "nmigen_sim_deps")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "bcd",
    srcs = ["bcd.py"],
    deps = nmigen_deps,
)

py_test(
    name = "bcd_test",
    size = "small",
    srcs = ["bcd_test.py"],
    deps = nmigen_sim_deps + [
        ":bcd",
        "//test:util",
    ],
)

py_library(
    name = "lut",
    srcs = ["lut.py"],
    deps = nmigen_deps + [
        "//core:util",
    ],
)

py_library(
    name = "square_fraction",
    srcs = ["square_fraction.py"],
    deps = nmigen_deps,
)

py_test(
    name = "square_fraction_test",
    size = "small",
    srcs = ["square_fraction_test.py"],
    deps = nmigen_sim_deps + [
        ":square_fraction",
    ],
)

py_library(
    name = "trig",
    srcs = ["trig.py"],
    deps = nmigen_deps + [
        ":lut",
        "//core:util",
    ],
)

py_test(
    name = "trig_test",
    size = "small",
    srcs = ["trig_test.py"],
    deps = nmigen_sim_deps + [
        ":lut",
        ":trig",
        "//core:util",
    ],
)
