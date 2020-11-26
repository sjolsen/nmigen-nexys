load("//bazel:top.bzl", "nmigen_design")
load("@pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_test")

package(default_visibility = ["//visibility:public"])

nmigen_design(
    name = "blinky",
    size = "small",
    srcs = ["blinky.py"],
    deps = [
        "//bazel:top",
        requirement("absl-py"),
        requirement("nmigen_boards"),
    ],
)

nmigen_design(
    name = "breathy",
    size = "small",
    srcs = ["breathy.py"],
    deps = [
        "//bazel:top",
        "//color:srgb",
        "//core:pwm",
        "//core:timer",
        "//math:trig",
        requirement("absl-py"),
        requirement("nmigen"),
        requirement("nmigen_boards"),
    ],
)

nmigen_design(
    name = "fm_transmitter",
    size = "small",
    srcs = ["fm_transmitter.py"],
    deps = [
        "//bazel:top",
        "//core:timer",
        "//core:util",
        "//math:trig",
        "//vendor/lattice:primitive",
        requirement("absl-py"),
        requirement("nmigen"),
        requirement("nmigen_boards"),
    ],
)

py_test(
    name = "fm_transmitter_test",
    size = "small",
    srcs = ["fm_transmitter_test.py"],
    deps = [
        ":fm_transmitter",
        "//core:util",
        "//test:test_util",
        requirement("nmigen"),
    ],
)
