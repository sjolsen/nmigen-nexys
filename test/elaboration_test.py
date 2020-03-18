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
