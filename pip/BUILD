load("@pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

# The pip rules unfortunately aren't smart enough to figure out all the
# transitive dependencies.
py_library(
    name = "absl",
    deps = [
        ":six",
        requirement("absl-py"),
    ],
)

py_library(
    name = "jinja2",
    deps = [
        ":markupsafe",
        requirement("jinja2"),
    ],
)

py_library(
    name = "jtagtap",
    deps = [
        ":nmigen",
        requirement("jtagtap"),
    ],
)

py_library(
    name = "markupsafe",
    deps = [requirement("markupsafe")],
)

py_library(
    name = "mido",
    deps = [requirement("mido")],
)

py_library(
    name = "minerva",
    deps = [
        ":jtagtap",
        ":nmigen",
        requirement("minerva"),
    ],
)

py_library(
    name = "nmigen",
    deps = [
        ":jinja2",
        ":pyvcd",
        requirement("nmigen"),
    ],
)

py_library(
    name = "nmigen_boards",
    deps = [
        ":nmigen",
        requirement("nmigen-boards"),
    ],
)

py_library(
    name = "pyvcd",
    deps = [
        ":six",
        requirement("pyvcd"),
    ],
)

py_library(
    name = "six",
    deps = [requirement("six")],
)
