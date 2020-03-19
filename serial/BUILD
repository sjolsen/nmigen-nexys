load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)
load(
    "//core:top.bzl",
    "nmigen_deps",
    "nmigen_sim_deps",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "spi",
    srcs = ["spi.py"],
    deps = nmigen_deps + [
        "//core:edge",
        "//core:shift_register",
        "//core:timer",
        "//core:util",
    ],
)

py_test(
    name = "spi_test",
    size = "small",
    srcs = ["spi_test.py"],
    deps = nmigen_sim_deps + [
        ":spi",
        "//core:shift_register",
        "//test:util",
    ],
)
