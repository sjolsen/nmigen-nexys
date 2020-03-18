"""Bazel rules for testing nMigen designs."""
load("@rules_python//python:defs.bzl", "py_test")


def Workspace(ctx, label):
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
            ctx.executable._no_synthesis.short_path),
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
        "src": "%{src}"
    },
)

def elaboration_test(name=None, top=None, *args, **kwargs):
    if args:
        fail('Illegal positional arguments', args)
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
    )
