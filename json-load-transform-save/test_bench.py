"""JSON Load-Transform-Save benchmark.

Note: Even though non-builtin JSON decoders can accept bytes, we use string to
keep ``json`` compatibility.

"""
import functools
import gzip
import io
import json
import os
import subprocess
import sys

import pytest
import rapidjson
import six
import ujson


def transform(doc):
    return doc['actor']


def _text_io(buf, encoding='utf-8', line_buffering=True):
    if six.PY2:
        # We don't need str<->bytes encoding/decoding.
        return buf
    assert isinstance(buf, io.BufferedIOBase)
    return io.TextIOWrapper(buf, encoding=encoding, line_buffering=line_buffering)


def gznaive(filename, loads, dumps):
    with gzip.open(filename, 'rb') as fp, gzip.open(os.devnull, 'wb') as out:
        reader = _text_io(io.BufferedReader(fp))
        writer = _text_io(out)
        write = writer.write
        for line in reader:
            obj = transform(loads(line))
            write(dumps(obj))
            write("\n")
    return True


def _check_jq(cmd='jq', quiet=True):
    cmd = 'which jq'.split()
    kwargs = {}
    if quiet:
        kwargs['stderr'] = kwargs['stdout'] = subprocess.PIPE
    return subprocess.call(cmd, **kwargs) == 0


def _create_proc(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                 close_fds=True, bufsize=1):
    return subprocess.Popen(cmd, stdin=stdin, stdout=stdout,
                            close_fds=close_fds, bufsize=bufsize)


def gzpiped(filename, loads, dumps, flush_every=1000):
    gzcat_cmd = ['gzip', '-cd', filename]
    gzip_cmd = 'gzip -c'.split()

    with io.open(os.devnull, mode='wb') as out:
        gzcat_proc = _create_proc(gzcat_cmd)
        gzip_proc = _create_proc(gzip_cmd, stdout=out)
        reader = _text_io(gzcat_proc.stdout)
        writer = _text_io(gzip_proc.stdin)
        write = writer.write
        for i, line in enumerate(reader):
            obj = transform(loads(line))
            write(dumps(obj))
            write("\n")
            if i % flush_every == 0:
                gzip_proc.stdin.flush()

        gzcat_proc.stdout.close()
        gzip_proc.communicate()  # wait
        ret = gzip_proc.returncode

    return ret == 0


def gzpiped_jq(filename):
    gzcat_cmd = ['gzip', '-cd', filename]
    jq_cmd = 'jq -c .actor'.split()
    gzip_cmd = 'gzip -c'.split()

    with io.open(os.devnull, 'wb') as out:
        gzcat_proc = _create_proc(gzcat_cmd)
        jq_proc = _create_proc(jq_cmd, stdin=gzcat_proc.stdout)
        gzip_proc = _create_proc(gzip_cmd, stdin=jq_proc.stdout, stdout=out)

        # Let pipes close gracefully.
        gzcat_proc.stdout.close()
        jq_proc.stdout.close()

        gzip_proc.communicate()  # wait
        ret = gzip_proc.returncode

    return ret == 0


@pytest.mark.skipif(not _check_jq(), reason="missing jq")
@pytest.mark.parametrize('func_spec', [
    ('gznaive_json', functools.partial(gznaive, loads=json.loads, dumps=json.dumps)),
    ('gznaive_ujson', functools.partial(gznaive, loads=ujson.loads, dumps=ujson.dumps)),
    ('gznaive_rapidjson', functools.partial(gznaive, loads=rapidjson.loads, dumps=rapidjson.dumps)),
    ('gzpiped_json', functools.partial(gzpiped, loads=json.loads, dumps=json.dumps)),
    ('gzpiped_ujson', functools.partial(gzpiped, loads=ujson.loads, dumps=ujson.dumps)),
    ('gzpiped_rapidjson', functools.partial(gzpiped, loads=rapidjson.loads, dumps=rapidjson.dumps)),
    (gzpiped_jq.__name__, gzpiped_jq),
])
@pytest.mark.parametrize('filename_spec', [
    ('~05Mb', '../datasets/githubarchive/2016-05-01-1.json.gz'),
    ('~20Mb', '../datasets/githubarchive/2016-05-01-3.json.gz'),
    ('~90Mb', '../datasets/githubarchive/2016-05-01-5.json.gz'),
])
@pytest.mark.benchmark
def test_bench(benchmark, func_spec, filename_spec):
    name, func = func_spec
    desc, filename = filename_spec
    benchmark.name = name
    benchmark.group = desc
    ok = benchmark.pedantic(func, args=(filename, ), rounds=3)
    assert ok


if __name__ == "__main__":
    args = sys.argv[1:] or ['-x', '--benchmark-sort=mean']
    pytest.main(args)
