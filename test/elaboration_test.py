"""Templated test driver for elaboration tests.

Normally one would simply emit a shell script from the elaboration test rule and
execute that directly, but (a) making that work for Windows is more complex than
it should be, and (b) batch scripts can't access runfiles anyway. This lets us
intercept Vivado invocations, anyway.
"""

import os
import subprocess

from rules_python.python.runfiles import runfiles


if __name__ == '__main__':
    r = runfiles.Create()
    env = dict(os.environ)
    # TODO: Big fat hack, should pull in Yosys directly
    env['YOSYS'] = 'C:/Program Files (x86)/Yosys/yosys.exe'
    # TODO: nMigen should not require tools it won't use
    env['VIVADO'] = r.Rlocation('{VIVADO}')
    env.update(r.EnvVars())
    subprocess.check_call(['{EXE}', '--nobuild', '--noprogram'], env=env)
