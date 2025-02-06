from PyCCAN_CodeGenerator import CodeGenerator

# https://github.com/nedbat/cog

# https://nedbatchelder.com/code/cog/index.html#h_running_cog

import sys

print("Hallo")

CodeGenerator.initialize("/home/christoph/CCAN/PyCCAN/gen/config11")
CodeGenerator.process()


print("Done!")
