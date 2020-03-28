load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)
load(
    "//core:top.bzl",
    "absl_deps",
    "nmigen_deps",
    "nmigen_design",
    "nmigen_sim_deps",
)

package(default_visibility = ["//visibility:public"])

nmigen_design(
    name = "demo",
    size = "small",
    srcs = ["demo.py"],
    deps = absl_deps + nmigen_deps + [
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
    deps = absl_deps + nmigen_deps + [
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
        "//test:test_util",
    ],
)

nmigen_design(
    name = "nexysa7100t",
    size = "small",
    srcs = ["nexysa7100t.py"],
    deps = absl_deps + nmigen_deps + [
        "//core:top",
        requirement("nmigen-boards"),
    ],
)

nmigen_design(
    name = "pmod_8ld_demo",
    size = "small",
    srcs = ["pmod_8ld_demo.py"],
    deps = absl_deps + nmigen_deps + [
        ":nexysa7100t",
        "//core:timer",
        "//core:top",
        "//pmod:pmod_8ld",
    ],
)

nmigen_design(
    name = "pmod_oled_demo",
    size = "small",
    srcs = ["pmod_oled_demo.py"],
    deps = absl_deps + nmigen_deps + [
        ":nexysa7100t",
        "//core:shift_register",
        "//core:timer",
        "//core:top",
        "//core:util",
        "//display:ssd1306",
        "//math:lfsr",
        "//pmod/oled:pmod_oled",
    ],
)

nmigen_design(
    name = "seven_segment_demo",
    size = "small",
    srcs = ["seven_segment_demo.py"],
    deps = absl_deps + nmigen_deps + [
        ":nexysa7100t",
        "//core:top",
        "//display:seven_segment",
    ],
)

nmigen_design(
    name = "uart_demo",
    size = "small",
    srcs = ["uart_demo.py"],
    deps = absl_deps + nmigen_deps + [
        ":nexysa7100t",
        "//core:top",
        "//serial:uart",
    ],
)

py_test(
    name = "uart_demo_test",
    size = "small",
    srcs = ["uart_demo_test.py"],
    deps = nmigen_sim_deps + [
        ":uart_demo",
        "//core:util",
        "//serial:uart",
        "//test:test_util",
    ],
)
