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
        "//pip:nmigen",
    ],
)

py_test(
    name = "seven_segment_sim",
    size = "small",
    srcs = ["seven_segment_sim.py"],
    deps = [
        ":seven_segment",
        "//core:util",
        "//pip:nmigen",
        "//test:test_util",
    ],
)

py_test(
    name = "seven_segment_test",
    size = "small",
    srcs = ["seven_segment_test.py"],
    deps = [
        ":seven_segment",
        "//core:util",
        "//pip:nmigen",
        "//test:test_util",
    ],
)

py_library(
    name = "ssd1306",
    srcs = ["ssd1306.py"],
    deps = [
        "//core:shift_register",
        "//core:util",
        "//pip:nmigen",
        "//serial:spi",
    ],
)
