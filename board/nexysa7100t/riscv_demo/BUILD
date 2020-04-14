load("//bazel:top.bzl", "nmigen_design")

package(default_visibility = ["//visibility:public"])

nmigen_design(
    name = "riscv_demo",
    size = "small",
    srcs = ["riscv_demo.py"],
    deps = [
        "//bazel:top",
        "//board/nexysa7100t",
        "//debug:remote_bitbang",
        "//pip:absl",
        "//pip:minerva",
        "//pip:nmigen",
    ],
)
