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
    name = "interpreter",
    srcs = ["interpreter.py"],
    deps = nmigen_deps + [
        "//core:flop",
        "//core:timer",
        "//core:util",
        "//display:ssd1306",
    ],
)

py_library(
    name = "pmod_oled",
    srcs = ["pmod_oled.py"],
    deps = nmigen_deps + [
        ":interpreter",
        "//core:flop",
        "//core:util",
        "//display:ssd1306",
    ],
)

py_test(
    name = "pmod_oled_test",
    size = "small",
    srcs = ["pmod_oled_test.py"],
    deps = nmigen_sim_deps + [
        ":pmod_oled",
        "//core:edge",
        "//core:util",
        "//display:ssd1306",
        "//serial:spi",
        "//test:test_util",
    ],
)
