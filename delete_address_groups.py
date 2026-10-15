"""Back up, then delete, the address groups listed in address_group_csv (panw.cfg).

Only the `name` and `location` columns are used, so the same CSV used to
create groups (or a previous backup) works as input. The backup is written
in create format, so `create-groups` can restore it.
"""
import sys

from panos_common import backup_and_delete, load, read_rows

FIELDS = ["name", "members", "dynamic_filter", "description", "location", "tag"]


def to_row(entry):
    return {
        "members": ",".join(m.text for m in entry.findall("./static/member") if m.text),
        "dynamic_filter": entry.findtext("./dynamic/filter", ""),
        "description": entry.findtext("description", ""),
        "tag": ",".join(t.text for t in entry.findall("./tag/member") if t.text),
    }


def main():
    pan, csv_path = load("address_group_csv")
    failures = backup_and_delete(pan, "address-group", read_rows(csv_path, {"dynamic": "dynamic_filter"}),
                                 FIELDS, to_row, "address group")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
