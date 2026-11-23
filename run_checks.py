"""Run all tests: python run_checks.py"""
from p4_env import *
from starter import *

check_task1(MinHeap, UnsortedListPQ)

check_task2(simulate)
check_task3(simulate, MinHeap, UnsortedListPQ)
