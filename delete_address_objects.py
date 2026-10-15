"""Back up, then delete, the address objects listed in address_csv (panw.cfg).

Only the `name` and `location` columns are used, so the same CSV used to
create objects (or a previous backup) works as input. The backup is written
in create format, so `create-objects` can restore it.
"""
import sys

from panos_common import backup_and_delete, load, read_rows

FIELDS = ["name", "value", "type", "description", "location", "tag"]


def to_row(entry):
    out = {"type": "unknown", "value": ""}
    for t in ("ip-netmask", "ip-range", "fqdn", "ip-wildcard"):
        el = entry.find(t)
        if el is not None:
            out = {"type": t, "value": el.text or ""}
            break
    out["description"] = entry.findtext("description", "")
    out["tag"] = ",".join(t.text for t in entry.findall("./tag/member") if t.text)
    return out


def main():
    pan, csv_path = load("address_csv")
    failures = backup_and_delete(pan, "address", read_rows(csv_path), FIELDS, to_row, "address object")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
