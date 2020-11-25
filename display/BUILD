load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "seven_segment",
    srcs = ["seven_segment.py"],
    deps = [
        "//core:pwm",
        "//math:lut",
        requirement("nmigen"),
    ],
)

py_test(
    name = "seven_segment_sim",
    size = "small",
    srcs = ["seven_segment_sim.py"],
    deps = [
        ":seven_segment",
        "//core:util",
        "//test:test_util",
        requirement("nmigen"),
    ],
)

py_test(
    name = "seven_segment_test",
    size = "small",
    srcs = ["seven_segment_test.py"],
    deps = [
        ":seven_segment",
        "//core:util",
        "//test:test_util",
        requirement("nmigen"),
    ],
)

py_library(
    name = "ssd1306",
    srcs = ["ssd1306.py"],
    deps = [
        "//core:shift_register",
        "//core:util",
        "//serial:spi",
        requirement("nmigen"),
    ],
)
