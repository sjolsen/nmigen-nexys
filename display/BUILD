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
        requirement("nmigen"),
    ],
)

py_test(
    name = "seven_segment_sim",
    srcs = ["seven_segment_sim.py"],
    deps = [
        ":seven_segment",
        "//test:util",
        requirement("nmigen"),
        requirement("six"),  # TODO: Fix this, needed by the VCD library
    ],
)

py_test(
    name = "seven_segment_test",
    srcs = ["seven_segment_test.py"],
    deps = [
        ":seven_segment",
        "//test:util",
        requirement("nmigen"),
        requirement("six"),  # TODO: Fix this, needed by the VCD library
    ],
)
