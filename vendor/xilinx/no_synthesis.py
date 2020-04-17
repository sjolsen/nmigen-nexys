"""Error stub for Vivado.

nMigen should not need Vivado for elaboration. However, it contains logic to
ensure the presence of all toolchain binaries before deciding which actions to
perform. Providing this lets the Vivado check pass, and the test will fail if it
ever (erroneously) actually invokes Vivado.
"""

import sys


if __name__ == '__main__':
    raise RuntimeError(f'Synthesis not implemented; invoked with: {sys.argv}')
