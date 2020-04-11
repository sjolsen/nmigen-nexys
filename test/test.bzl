"""Bazel rules for testing nMigen designs."""

load("//bazel:script.bzl", "create_script")
load("@rules_python//python:defs.bzl", "py_test")

def Workspace(ctx, label):
    """Get the workspace name associated with a Label.

    Labels do have a workspace_name field, but annoyingly it returns an empty
    string for the default workspace. When the name of the default workspace is
    needed, we get it from ctx.

    Args:
        ctx: The rule context.
        label: The label to inspect.
    """
    if label.workspace_name:
        return label.workspace_name
    else:
        return ctx.workspace_name

def PathJoin(*args):
    return "/".join(args)

def __elaboration_test_src(ctx):
    create_script(
        ctx,
        template = ctx.file._template,
        output = ctx.outputs.src,
        exe = ctx.executable.top,
        env = {
            "VIVADO": PathJoin(
                Workspace(ctx, ctx.attr._no_synthesis.label),
                ctx.executable._no_synthesis.short_path,
            ),
        },
        args = ["--action=elaborate"],
    )

_elaboration_test_src = rule(
    implementation = __elaboration_test_src,
    attrs = {
        "top": attr.label(
            mandatory = True,
            executable = True,
            cfg = "exec",
        ),
        "src": attr.string(
            mandatory = True,
        ),
        "_template": attr.label(
            allow_single_file = True,
            default = "//bazel:script",
        ),
        "_no_synthesis": attr.label(
            default = "//bazel:no_synthesis",
            executable = True,
            cfg = "exec",
        ),
    },
    outputs = {
        "src": "%{src}",
    },
)

def elaboration_test(name = None, top = None, *args, **kwargs):
    """Validate that nMigen can elaborate a design.

    This requires that the design be implemented using
    nmigen_nexys.core.top.build. This sets up the command-line flags that allow
    the test to control build options. Rather than using this directly, use
    nmigen_design defined in //core:top.bzl, which automatically creates an
    elaboration test.

    Args:
        name: The name of the test target.
        top: The py_binary target implementing the design.
        *args: Not allowed.
        **kwargs: Additional arguments to be passed to py_test.
    """
    if args:
        fail("Illegal positional arguments", args)
    _elaboration_test_src(
        name = "%s_src" % name,
        top = top,
        src = "%s.py" % name,
    )
    py_test(
        name = name,
        srcs = ["%s.py" % name],
        data = [
            top,
            "//bazel:no_synthesis",
        ],
        deps = ["@rules_python//python/runfiles"],
        **kwargs
    )
