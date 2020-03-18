"""Bazel rules for testing nMigen designs."""

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
    ext = ctx.file._template.extension
    substitutions = {
        "{EXE}": ctx.executable.top.short_path,
        "{VIVADO}": PathJoin(
            Workspace(ctx, ctx.attr._no_synthesis.label),
            ctx.executable._no_synthesis.short_path,
        ),
    }
    ctx.actions.expand_template(
        template = ctx.file._template,
        output = ctx.outputs.src,
        substitutions = substitutions,
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
            default = "//test:elaboration_test",
        ),
        "_no_synthesis": attr.label(
            default = "//test:no_synthesis",
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
    nmigen_nexys.core.top.main. This sets up the command-line flags that allow
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
            "//test:no_synthesis",
        ],
        deps = ["@rules_python//python/runfiles"],
        **kwargs
    )
