import sys
from ujson import loads, dumps

for line in sys.stdin:
    obj = loads(line)
    sys.stdout.write(dumps(obj['actor']))
    sys.stdout.write('\n')


