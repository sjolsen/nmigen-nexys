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
    name = "pmod_8ld",
    srcs = ["pmod_8ld.py"],
    deps = nmigen_deps,
)

py_library(
    name = "pmod_oled",
    srcs = ["pmod_oled.py"],
    deps = nmigen_deps + [
        "//core:shift_register",
        "//core:timer",
        "//display:ssd1306",
        "//serial:spi",
    ],
)

py_test(
    name = "pmod_oled_test",
    size = "small",
    srcs = ["pmod_oled_test.py"],
    deps = nmigen_sim_deps + [
        ":pmod_oled",
        "//test:util",
    ],
)
