load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)
load("//bazel:top.bzl", "nmigen_design")

package(default_visibility = ["//visibility:public"])

nmigen_design(
    name = "demo",
    size = "small",
    srcs = ["demo.py"],
    deps = [
        ":nexysa7100t",
        "//color:srgb",
        "//core:pwm",
        "//core:timer",
        "//bazel:top",
        "//math:trig",
        requirement("absl-py"),
        requirement("nmigen"),
    ],
)

nmigen_design(
    name = "macro_demo",
    size = "small",
    srcs = ["macro_demo.py"],
    deps = [
        ":nexysa7100t",
        "//bazel:top",
        "//vendor/xilinx:macro",
        requirement("absl-py"),
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
    size = "small",
    srcs = ["manual_brightness_demo.py"],
    deps = [
        ":manual_brightness",
        ":nexysa7100t",
        "//color:srgb",
        "//bazel:top",
        "//display:seven_segment",
        requirement("absl-py"),
        requirement("nmigen"),
    ],
)

py_test(
    name = "manual_brightness_test",
    size = "small",
    srcs = ["manual_brightness_test.py"],
    deps = [
        ":manual_brightness",
        "//core:util",
        "//display:seven_segment",
        "//test:test_util",
        requirement("nmigen"),
    ],
)

nmigen_design(
    name = "nexysa7100t",
    size = "small",
    srcs = ["nexysa7100t.py"],
    deps = [
        "//bazel:top",
        requirement("absl-py"),
        requirement("nmigen"),
        requirement("nmigen_boards"),
    ],
)

nmigen_design(
    name = "pmod_8ld_demo",
    size = "small",
    srcs = ["pmod_8ld_demo.py"],
    deps = [
        ":nexysa7100t",
        "//core:timer",
        "//bazel:top",
        "//pmod:pmod_8ld",
        requirement("absl-py"),
        requirement("nmigen"),
    ],
)

nmigen_design(
    name = "pmod_oled_demo",
    size = "small",
    srcs = ["pmod_oled_demo.py"],
    deps = [
        ":nexysa7100t",
        "//core:shift_register",
        "//core:timer",
        "//bazel:top",
        "//core:util",
        "//display:ssd1306",
        "//math:lfsr",
        "//pmod/oled:pmod_oled",
        requirement("absl-py"),
        requirement("nmigen"),
    ],
)

nmigen_design(
    name = "seven_segment_demo",
    size = "small",
    srcs = ["seven_segment_demo.py"],
    deps = [
        ":nexysa7100t",
        "//bazel:top",
        "//display:seven_segment",
        requirement("absl-py"),
        requirement("nmigen"),
    ],
)

nmigen_design(
    name = "uart_demo",
    size = "small",
    srcs = ["uart_demo.py"],
    deps = [
        ":nexysa7100t",
        "//bazel:top",
        "//serial:uart",
        requirement("absl-py"),
        requirement("nmigen"),
    ],
)

py_test(
    name = "uart_demo_test",
    size = "small",
    srcs = ["uart_demo_test.py"],
    deps = [
        ":uart_demo",
        "//core:util",
        "//serial:uart",
        "//test:test_util",
        requirement("nmigen"),
    ],
)
