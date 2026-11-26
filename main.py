"""Audit a route table for common problems.

Usage: python3 main.py routes.csv
CSV columns: destination,gateway,interface,metric.
destination is a CIDR network (0.0.0.0/0 is the default
route); a gateway of 0.0.0.0 or on-link means the network is
directly connected. Checks:
- missing default route: no 0.0.0.0/0 destination at all.
- duplicate destination: the same destination network listed
  more than once.
- unreachable gateway: a gateway that is not inside any
  directly-connected network.
Row verdicts: DUPLICATE, UNREACHABLE GATEWAY, or OK.
DUPLICATE first, then UNREACHABLE GATEWAY, then OK; within a
verdict by destination. Rows with an unparseable destination
or gateway are reported as skipped, not silently dropped.
"""
import argparse, csv, ipaddress, sys

VERDICT_ORDER = {"DUPLICATE": 0, "UNREACHABLE GATEWAY": 1, "OK": 2}

def audit(rows):
    parsed = []
    skipped = 0
    for row in rows:
        try:
            destination = ipaddress.ip_network(row["destination"].strip(),
                                               strict=False)
            gateway_text = row["gateway"].strip().lower()
            interface = row["interface"].strip()
            metric = int(row["metric"])
            if gateway_text not in ("0.0.0.0", "on-link"):
                gateway = ipaddress.ip_address(gateway_text)
            else:
                gateway = None
            if not interface:
                raise ValueError("missing interface")
        except (KeyError, AttributeError, ValueError, TypeError):
            skipped += 1
            continue
        parsed.append((destination, gateway, interface, metric))
    connected = [d for d, g, _, _ in parsed if g is None]
    counts = {}
    for destination, _, _, _ in parsed:
        counts[destination] = counts.get(destination, 0) + 1
    default_present = any(str(d) == "0.0.0.0/0" for d, _, _, _ in parsed)
    out = []
    for destination, gateway, interface, metric in parsed:
        if counts[destination] > 1:
            verdict = "DUPLICATE"
            detail = (f"destination {destination} listed "
                      f"{counts[destination]} time(s)")
        elif gateway is not None and not any(gateway in net for net in connected):
            verdict = "UNREACHABLE GATEWAY"
            detail = f"gateway {gateway} is not in any connected network"
        else:
            verdict = "OK"
            detail = (f"gateway {'on-link' if gateway is None else gateway}, "
                      f"interface {interface}, metric {metric}")
        out.append((str(destination), verdict, detail))
    out.sort(key=lambda r: (VERDICT_ORDER[r[1]], r[0]))
    return out, skipped, default_present

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    args = parser.parse_args(argv)
    with open(args.path, newline="", encoding="utf-8") as f:
        results, skipped, default_present = audit(list(csv.DictReader(f)))
    for destination, verdict, detail in results:
        print(f"{destination}: {verdict} - {detail}")
    if default_present:
        print("Default route: present.")
    else:
        print("Default route: MISSING - no 0.0.0.0/0 route.")
    counts = {v: sum(1 for _, verdict, _ in results if verdict == v)
              for v in VERDICT_ORDER}
    print(f"{counts['DUPLICATE']} duplicate(s), "
          f"{counts['UNREACHABLE GATEWAY']} unreachable gateway(s), "
          f"{counts['OK']} ok out of {len(results)} route(s).")
    if skipped:
        print(f"Skipped {skipped} invalid row(s).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
