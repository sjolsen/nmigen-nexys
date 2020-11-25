workspace(name = "nmigen_nexys")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "rules_python",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.1.0/rules_python-0.1.0.tar.gz",
    sha256 = "b6d46438523a3ec0f3cead544190ee13223a52f6a6765a29eae7b7cc24cc83a0",
)

load("@rules_python//python:pip.bzl", "pip_install")

# Create a central repo that knows about the dependencies needed for
# requirements.txt.
pip_install(
    name = "pip_deps",
    requirements = "//pip:requirements.txt",
)

register_execution_platforms("//bazel/platforms:baremetal_riscv")

register_toolchains(
    "//vendor/gcc:riscv_toolchain",
    "//vendor/xilinx:xilinx_linux_toolchain",
    "//vendor/xilinx:xilinx_windows_toolchain",
)
