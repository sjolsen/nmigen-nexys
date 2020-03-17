from nmigen import *
from nmigen.build import *

from nmigen_nexys.board.nexysa7100t import nexysa7100t
from nmigen_nexys.display import seven_segment


if __name__ == "__main__":
    platform = nexysa7100t.NexysA7100TPlatform()
    segments = platform.request('display_7seg')
    anodes = platform.request('display_7seg_an')
    demo = seven_segment.DisplayMultiplexerDemo(segments, anodes)
    platform.build(demo, do_program=True)
