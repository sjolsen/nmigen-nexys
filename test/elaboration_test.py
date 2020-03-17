import os
import subprocess


if __name__ == '__main__':
    env = dict(os.environ)
    # TODO: Big fat hack, should pull in Yosys directly
    env['YOSYS'] = 'C:/Program Files (x86)/Yosys/yosys.exe'
    # TODO: nMigen should not require tools it won't use
    env['VIVADO'] = 'DONOTCALLME'
    subprocess.check_call(['{EXE}', '--nobuild', '--noprogram'], env=env)
