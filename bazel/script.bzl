def create_script(ctx, template, output, exe, env=None, args=None):
    substitutions = {
        "{ENV}": env or {},
        "{EXE}": exe.short_path,
        "{ARGS}": args or [],
    }
    ctx.actions.expand_template(
        template = template,
        output = output,
        substitutions = {k: repr(v) for k, v in substitutions.items()},
    )
