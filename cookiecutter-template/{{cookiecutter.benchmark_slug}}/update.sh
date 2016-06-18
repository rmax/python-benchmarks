#!/bin/sh
python test_bench.py -x --benchmark-sort=mean --benchmark-json benchmark.json --benchmark-histogram histograms/result $@ | tee benchmark.log
