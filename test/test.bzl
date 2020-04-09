"""Bazel rules for testing nMigen designs."""

load(
    "@rules_python//python:defs.bzl",
    "PyInfo",
    "py_library",
    "py_test",
)

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
            "//test:no_synthesis",
        ],
        deps = ["@rules_python//python/runfiles"],
        **kwargs
    )

# _PyRuleInfo = provider(fields = ["srcs"])

# def __pyrule_info(_target, ctx):
#     return [_PyRuleInfo(srcs = depset(
#         ctx.rule.files.srcs,
#         transitive = [d[_PyRuleInfo].srcs for d in ctx.rule.attr.deps],
#     ))]

# _pyrule_info = aspect(
#     implementation = __pyrule_info,
#     attr_aspects = ["deps"],
#     provides = [_PyRuleInfo],
# )

_PyTypeInfo = provider(fields = ["outputs"])

def __pytype_check(target, ctx):
    # dep_srcs = [d[_PyRuleInfo].srcs for d in ctx.rule.attr.deps]
    imports = [PathJoin("external", i) for i in target[PyInfo].imports.to_list()]
    dep_srcs = target[PyInfo].transitive_sources
    # for src in depset(transitive = dep_srcs).to_list():
    #     print(src.path)
    transitive_outputs = [
        d[_PyTypeInfo].outputs for d in ctx.rule.attr.deps if _PyTypeInfo in d
    ]
    outputs = []
    for src in ctx.rule.files.srcs:
        if src.extension == "py":
            base = src.basename[:-3]
        else:
            base = src.basename
        output = ctx.actions.declare_file(base + ".pyi", sibling=src)
        args = ctx.actions.args()
        args.add("--input", src)
        args.add("--output", output)
        args.add("--imports", ",".join(imports))
        ctx.actions.run(
            executable = ctx.executable._type_check,
            arguments = [args],
            inputs = depset(ctx.rule.files.srcs, transitive = [dep_srcs]),
            outputs = [output],
        )
        outputs.append(output)
    all_outputs = depset(outputs, transitive=transitive_outputs)
    return [_PyTypeInfo(outputs=all_outputs)]

_pytype_check = aspect(
    implementation = __pytype_check,
    # attr_aspects = ["srcs", "deps"],
    # required_aspect_providers = [_PyRuleInfo],
    provides = [_PyTypeInfo],
    attrs = {
        "_type_check": attr.label(
            executable = True,
            cfg = "exec",
            default = "//test:type_check",
        ),
    },
)

def __pytype_library(ctx):
    return [
        DefaultInfo(
            files = depset(transitive = [
                ctx.attr.lib[DefaultInfo].files,
                ctx.attr.lib[_PyTypeInfo].outputs,
            ]),
            runfiles = ctx.attr.lib[DefaultInfo].default_runfiles,
            # runfiles=ctx.runfiles(
            #     files = [],
            #     transitive_files = depset(transitive = [
            #         ctx.attr.lib[DefaultInfo].default_runfiles,
            #         ctx.attr.type_info[DefaultInfo].default_runfiles,
            #     ]),
            # ),
        ),
        ctx.attr.lib[PyInfo],
    ]

_pytype_library = rule(
    implementation = __pytype_library,
    attrs = {
        "lib": attr.label(
            providers = [PyInfo],
            aspects = [_pytype_check],
            # aspects = [_pyrule_info, _pytype_check],
        ),
    },
)

def pytype_library(name = None, *args, **kwargs):
    if args:
        fail("Illegal positional arguments", args)
    py_library(
        name = "%s.unchecked" % name,
        **kwargs
    )
    _pytype_library(
        name = name,
        lib = "%s.unchecked" % name,
    )
