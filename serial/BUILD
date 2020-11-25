load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "spi",
    srcs = ["spi.py"],
    deps = [
        "//core:edge",
        "//core:shift_register",
        "//core:timer",
        "//core:util",
        requirement("nmigen"),
    ],
)

py_test(
    name = "spi_test",
    size = "small",
    srcs = ["spi_test.py"],
    deps = [
        ":spi",
        "//core:edge",
        "//core:shift_register",
        "//core:util",
        "//test:test_util",
        requirement("nmigen"),
    ],
)

py_library(
    name = "uart",
    srcs = ["uart.py"],
    deps = [
        "//core:edge",
        "//core:shift_register",
        "//core:timer",
        "//core:util",
        requirement("nmigen"),
    ],
)

py_test(
    name = "uart_test",
    size = "small",
    srcs = ["uart_test.py"],
    deps = [
        ":uart",
        "//core:util",
        "//test:test_util",
        requirement("nmigen"),
    ],
)
