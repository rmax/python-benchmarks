"""{{cookiecutter.benchmark_name}}
"""
import sys

import pytest


def func(n):
    for _ in range(2**n):
        pass
    return True


@pytest.mark.parametrize('n', range(10))
@pytest.mark.benchmark
def test_bench(benchmark, n):
    ok = benchmark(func, n)
    assert ok


if __name__ == "__main__":
    args = sys.argv[1:] or ['-x', '--benchmark-sort=mean']
    pytest.main(args)
