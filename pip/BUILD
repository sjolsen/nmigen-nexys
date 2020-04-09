load("@pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_library")

package(default_visibility = ["//visibility:public"])

# The pip rules unfortunately aren't smart enough to figure out all the
# transitive dependencies.
py_library(
    name = "absl",
    deps = [
        requirement("absl-py"),
        requirement("six"),  # Needed by absl-py
    ],
)

py_library(
    name = "nmigen",
    deps = [
        requirement("nmigen"),
        requirement("jinja2"),  # Needed by nmigen
        requirement("markupsafe"),  # Needed by jinja2
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
    name = "nmigen_sim",
    deps = [
        ":nmigen",
        requirement("pyvcd"),  # Needed by nmigen
        requirement("six"),  # Needed by pyvcd
    ],
)
