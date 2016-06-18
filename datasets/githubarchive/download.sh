#!/bin/bash
set -e

CONCURRENCY=${1:-"0"}
URLS=$(echo http://data.githubarchive.org/2016-05-{01..31}-{0..23}.json.gz)
WGET="wget -c"

case $CONCURRENCY in
  *[!0-9]* ) echo "invalid concurrency: $CONCURRENCY"; exit 2;;
esac

if [ $CONCURRENCY = "0" -o $CONCURRENCY = "1" ]; then
  $WGET $URLS
else
  echo $URLS | xargs -P$CONCURRENCY -n1 $WGET
fi

exit $?
