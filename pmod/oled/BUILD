load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "interpreter",
    srcs = ["interpreter.py"],
    deps = [
        "//core:flop",
        "//core:timer",
        "//core:util",
        "//display:ssd1306",
        requirement("nmigen"),
    ],
)

py_library(
    name = "pmod_oled",
    srcs = ["pmod_oled.py"],
    deps = [
        ":interpreter",
        "//core:flop",
        "//core:util",
        "//display:ssd1306",
        requirement("nmigen"),
    ],
)

py_test(
    name = "pmod_oled_test",
    size = "small",
    srcs = ["pmod_oled_test.py"],
    deps = [
        ":pmod_oled",
        "//core:edge",
        "//core:util",
        "//display:ssd1306",
        "//serial:spi",
        "//test:event",
        "//test:test_util",
        requirement("nmigen"),
    ],
)
