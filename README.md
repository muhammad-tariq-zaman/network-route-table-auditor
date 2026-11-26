# network-route-table-auditor

Audit a route table for common problems: the input CSV lists destination (a CIDR network; 0.0.0.0/0 is the default route), gateway (0.0.0.0 or on-link means the network is directly connected), interface and metric — it flags a missing default route, a duplicate destination (the same destination network listed more than once), and an unreachable gateway (a gateway that is not inside any directly-connected network) — DUPLICATE first, then UNREACHABLE GATEWAY, then OK. Rows with an unparseable destination or gateway are reported as skipped, not silently dropped.

Sample input is included (sample.csv with seven routes, one invalid row).

## How to run

```sh
python3 main.py sample.csv
```

## Example output

```
172.16.0.0/16: DUPLICATE - destination 172.16.0.0/16 listed 2 time(s)
172.16.0.0/16: DUPLICATE - destination 172.16.0.0/16 listed 2 time(s)
203.0.113.0/24: UNREACHABLE GATEWAY - gateway 198.51.100.1 is not in any connected network
0.0.0.0/0: OK - gateway 10.0.0.1, interface eth0, metric 100
10.0.0.0/24: OK - gateway on-link, interface eth0, metric 100
192.168.1.0/24: OK - gateway on-link, interface eth1, metric 100
Default route: present.
2 duplicate(s), 1 unreachable gateway(s), 3 ok out of 6 route(s).
Skipped 1 invalid row(s).
```

Standard library only. Run the tests with `python3 -m unittest discover`.
