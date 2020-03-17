load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)
load("//core:top.bzl", "nmigen_design")

package(default_visibility = ["//visibility:public"])

nmigen_design(
    name = "demo",
    srcs = ["demo.py"],
    deps = [
        ":nexysa7100t",
        "//color:srgb",
        "//core:pwm",
        "//core:timer",
        "//core:top",
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

nmigen_design(
    name = "manual_brightness_demo",
    srcs = ["manual_brightness_demo.py"],
    deps = [
        ":manual_brightness",
        ":nexysa7100t",
        "//color:srgb",
        "//core:top",
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

nmigen_design(
    name = "nexysa7100t",
    srcs = ["nexysa7100t.py"],
    deps = [
        "//core:top",
        requirement("nmigen_boards"),
    ],
)

nmigen_design(
    name = "pmod_8ld_demo",
    srcs = ["pmod_8ld_demo.py"],
    deps = [
        ":nexysa7100t",
        "//core:timer",
        "//core:top",
        "//pmod:pmod_8ld",
        requirement("nmigen"),
    ],
)

nmigen_design(
    name = "seven_segment_demo",
    srcs = ["seven_segment_demo.py"],
    deps = [
        ":nexysa7100t",
        "//core:top",
        "//display:seven_segment",
        requirement("nmigen"),
    ],
)
