load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)
load(
    "//core:top.bzl",
    "nmigen_deps",
    "nmigen_design",
    "nmigen_sim_deps",
)

package(default_visibility = ["//visibility:public"])

nmigen_design(
    name = "demo",
    size = "small",
    srcs = ["demo.py"],
    deps = nmigen_deps + [
        ":nexysa7100t",
        "//color:srgb",
        "//core:pwm",
        "//core:timer",
        "//core:top",
        "//math:trig",
    ],
)

py_library(
    name = "manual_brightness",
    srcs = ["manual_brightness.py"],
    deps = nmigen_deps + [
        "//display:seven_segment",
        "//math:bcd",
    ],
)

nmigen_design(
    name = "manual_brightness_demo",
    size = "small",
    srcs = ["manual_brightness_demo.py"],
    deps = nmigen_deps + [
        ":manual_brightness",
        ":nexysa7100t",
        "//color:srgb",
        "//core:top",
        "//display:seven_segment",
    ],
)

py_test(
    name = "manual_brightness_test",
    size = "small",
    srcs = ["manual_brightness_test.py"],
    deps = nmigen_sim_deps + [
        ":manual_brightness",
        "//core:util",
        "//display:seven_segment",
        "//test:util",
    ],
)

nmigen_design(
    name = "nexysa7100t",
    size = "small",
    srcs = ["nexysa7100t.py"],
    deps = nmigen_deps + [
        "//core:top",
        requirement("nmigen-boards"),
    ],
)

nmigen_design(
    name = "pmod_8ld_demo",
    size = "small",
    srcs = ["pmod_8ld_demo.py"],
    deps = nmigen_deps + [
        ":nexysa7100t",
        "//core:timer",
        "//core:top",
        "//pmod:pmod_8ld",
    ],
)

nmigen_design(
    name = "seven_segment_demo",
    size = "small",
    srcs = ["seven_segment_demo.py"],
    deps = nmigen_deps + [
        ":nexysa7100t",
        "//core:top",
        "//display:seven_segment",
    ],
)
