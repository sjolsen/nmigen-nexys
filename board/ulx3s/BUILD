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