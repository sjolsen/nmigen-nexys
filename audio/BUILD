load("@pip_deps//:requirements.bzl", "requirement")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
    "py_test",
)

package(default_visibility = ["//visibility:public"])

py_library(
    name = "synth",
    srcs = ["synth.py"],
    deps = [
        "//core:shift_register",
        "//core:timer",
        "//core:util",
        "//math:trig",
        "//serial:uart",
        requirement("nmigen"),
    ],
)

py_test(
    name = "synth_test",
    size = "small",
    srcs = ["synth_test.py"],
    deps = [
        ":synth",
        "//core:util",
        "//serial:uart",
        "//test:test_util",
        requirement("mido"),
        requirement("nmigen"),
    ],
)
