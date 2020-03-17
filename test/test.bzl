"""Bazel rules for testing nMigen designs."""
load("@rules_python//python:defs.bzl", "py_test")


def __elaboration_test_src(ctx):
    ext = ctx.file._template.extension
    ctx.actions.expand_template(
        template = ctx.file._template,
        output = ctx.outputs.src,
        substitutions = {"{EXE}": ctx.executable.top.short_path},
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
        data = [top],
    )
