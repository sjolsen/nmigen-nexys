load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)
load("//core:top.bzl", "nmigen_design")

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
        "//core:top",
        "//math:trig",
        "//pip:absl",
        "//pip:nmigen",
    ],
)

nmigen_design(
    name = "macro_demo",
    size = "small",
    srcs = ["macro_demo.py"],
    deps = [
        ":nexysa7100t",
        "//core:top",
        "//pip:absl",
        "//pip:nmigen",
        "//vendor/xilinx:macro",
    ],
)


py_library(
    name = "manual_brightness",
    srcs = ["manual_brightness.py"],
    deps = [
        "//display:seven_segment",
        "//math:bcd",
        "//pip:nmigen",
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
        "//core:top",
        "//display:seven_segment",
        "//pip:absl",
        "//pip:nmigen",
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
        "//pip:nmigen",
        "//test:test_util",
    ],
)

nmigen_design(
    name = "nexysa7100t",
    size = "small",
    srcs = ["nexysa7100t.py"],
    deps = [
        "//core:top",
        "//pip:absl",
        "//pip:nmigen",
        "//pip:nmigen_boards",
    ],
)

nmigen_design(
    name = "pmod_8ld_demo",
    size = "small",
    srcs = ["pmod_8ld_demo.py"],
    deps = [
        ":nexysa7100t",
        "//core:timer",
        "//core:top",
        "//pip:absl",
        "//pip:nmigen",
        "//pmod:pmod_8ld",
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
        "//core:top",
        "//core:util",
        "//display:ssd1306",
        "//math:lfsr",
        "//pip:absl",
        "//pip:nmigen",
        "//pmod/oled:pmod_oled",
    ],
)

nmigen_design(
    name = "seven_segment_demo",
    size = "small",
    srcs = ["seven_segment_demo.py"],
    deps = [
        ":nexysa7100t",
        "//core:top",
        "//display:seven_segment",
        "//pip:absl",
        "//pip:nmigen",
    ],
)

nmigen_design(
    name = "uart_demo",
    size = "small",
    srcs = ["uart_demo.py"],
    deps = [
        ":nexysa7100t",
        "//core:top",
        "//pip:absl",
        "//pip:nmigen",
        "//serial:uart",
    ],
)

py_test(
    name = "uart_demo_test",
    size = "small",
    srcs = ["uart_demo_test.py"],
    deps = [
        ":uart_demo",
        "//core:util",
        "//pip:nmigen",
        "//serial:uart",
        "//test:test_util",
    ],
)
