load("//bazel:top.bzl", "nmigen_design")
load("@pip_deps//:requirements.bzl", "requirement")

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
