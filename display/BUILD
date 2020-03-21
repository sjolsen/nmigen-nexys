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
    name = "seven_segment",
    srcs = ["seven_segment.py"],
    deps = nmigen_deps + [
        "//core:pwm",
    ],
)

py_test(
    name = "seven_segment_sim",
    size = "small",
    srcs = ["seven_segment_sim.py"],
    deps = nmigen_sim_deps + [
        ":seven_segment",
        "//test:util",
    ],
)

py_test(
    name = "seven_segment_test",
    size = "small",
    srcs = ["seven_segment_test.py"],
    deps = nmigen_sim_deps + [
        ":seven_segment",
        "//test:util",
    ],
)

py_library(
    name = "ssd1306",
    srcs = ["ssd1306.py"],
    deps = nmigen_deps + [
        "//core:shift_register",
        "//core:util",
        "//serial:spi",
    ],
)
