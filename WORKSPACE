workspace(name = "nmigen_nexys")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "rules_python",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.0.1/rules_python-0.0.1.tar.gz",
    sha256 = "aa96a691d3a8177f3215b14b0edc9641787abaaa30363a080165d06ab65e1161",
)

load("@rules_python//python:pip.bzl", "pip_repositories")
load("@rules_python//python:repositories.bzl", "py_repositories")
pip_repositories()
py_repositories()

# Create a central repo that knows about the dependencies needed for
# requirements.txt.
load("@rules_python//python:pip.bzl", "pip_import")
pip_import(
    name = "pip_deps",
    requirements = "//:pip_requirements.txt",
)

# Load the central repo's install function from its `//:requirements.bzl` file,
# and call it.
load("@pip_deps//:requirements.bzl", "pip_install")
pip_install()

new_local_repository(
    name = "nmigen_boards",
    path = "C:/Users/Stuart/nmigen-boards",
    build_file = "BUILD.nmigen_boards",
)