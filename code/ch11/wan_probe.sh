#!/bin/sh
# wan_probe.sh -- round-trip time and download rate over the internet.
# Make It Parallel, Chapter 11. Needs curl.
#     sh wan_probe.sh > wan.csv
# For each server, the time from a finished TLS handshake to the first
# byte of the reply approximates one request's round trip. The download
# rate is measured on a large public file.
echo "kind,server,trial,value"
for host in https://github.com/ https://pypi.org/simple/ https://registry.npmjs.org/; do
    for trial in 1 2 3 4 5; do
        curl -s -o /dev/null -w "%{time_appconnect} %{time_starttransfer} %{size_download} %{time_total}\n" "$host" |
        awk -v h="$host" -v t=$trial '{ printf "rtt_ms,%s,%d,%.1f\n", h, t, ($2 - $1) * 1000 }'
    done
done
for trial in 1 2 3; do
    curl -s -o /dev/null -w "%{size_download} %{time_total}\n" https://pypi.org/simple/ |
    awk -v t=$trial '$1 > 1000000 { printf "download_MBps,https://pypi.org/simple/,%d,%.1f\n", t, $1 / $2 / 1e6 }'
done
