load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_binary",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])

py_binary(
    name = "demo",
    srcs = ["demo.py"],
    deps = [
        ":nexysa7100t",
        "//color:srgb",
        "//core:pwm",
        "//core:timer",
        "//math:trig",
        requirement("nmigen"),
    ],
)

py_library(
    name = "manual_brightness",
    srcs = ["manual_brightness.py"],
    deps = [
        "//display:seven_segment",
        "//math:bcd",
        requirement("nmigen"),
    ],
)

py_binary(
    name = "manual_brightness_demo",
    srcs = ["manual_brightness_demo.py"],
    deps = [
        ":manual_brightness",
        ":nexysa7100t",
        "//color:srgb",
        "//display:seven_segment",
        "//math:bcd",
        requirement("nmigen"),
    ],
)

py_test(
    name = "manual_brightness_test",
    srcs = ["manual_brightness_test.py"],
    deps = [
        ":manual_brightness",
        "//core:util",
        "//display:seven_segment",
        "//test:util",
        requirement("nmigen"),
        requirement("six"),  # TODO: Fix this, needed by the VCD library
    ],
)

py_binary(
    name = "nexysa7100t",
    srcs = ["nexysa7100t.py"],
    deps = [requirement("nmigen_boards")],
)

py_binary(
    name = "pmod_8ld_demo",
    srcs = ["pmod_8ld_demo.py"],
    deps = [
        ":nexysa7100t",
        "//core:timer",
        "//pmod:pmod_8ld",
        requirement("nmigen"),
    ],
)

py_binary(
    name = "seven_segment_demo",
    srcs = ["seven_segment_demo.py"],
    deps = [
        ":nexysa7100t",
        "//display:seven_segment",
        requirement("nmigen"),
    ],
)
