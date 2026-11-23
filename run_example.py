"""Full report: python run_example.py [input file]"""
import sys
from p4_env import *
from starter import *

source = sys.argv[1] if len(sys.argv) > 1 else "data/example.txt"
try:
    analyze(source)
except NotImplementedError:
    print("⏳ Finish the TODOs in starter.py first.")
