"""Create Panorama address groups from the address_group_csv file in panw.cfg.

CSV headers: name,members,dynamic_filter,description,location,tag
(static groups use `members`, dynamic groups use `dynamic_filter`)
"""
import sys
import xml.etree.ElementTree as ET

from panos_common import PanoramaError, add_members, container_xpath, load, read_rows, split_list

ALIASES = {"dynamic": "dynamic_filter"}


def build_entry(row):
    """Return (location, element_xml) for a CSV row, or raise ValueError."""
    name = row.get("name")
    if not name:
        raise ValueError("missing 'name'")
    members, dyn = split_list(row.get("members")), row.get("dynamic_filter")
    if members and dyn:
        raise ValueError("set either 'members' or 'dynamic_filter', not both")
    if not members and not dyn:
        raise ValueError("needs 'members' (static) or 'dynamic_filter' (dynamic)")
    entry = ET.Element("entry", name=name)
    if members:
        add_members(entry, "static", members)
    else:
        ET.SubElement(ET.SubElement(entry, "dynamic"), "filter").text = dyn
    if row.get("description"):
        ET.SubElement(entry, "description").text = row["description"]
    add_members(entry, "tag", split_list(row.get("tag")))
    return row.get("location") or "shared", ET.tostring(entry, encoding="unicode")


def main():
    pan, csv_path = load("address_group_csv")
    failures = 0
    for row in read_rows(csv_path, ALIASES):
        name = row.get("name") or "<no name>"
        try:
            location, element = build_entry(row)
        except ValueError as e:
            print(f"[!] Skipping '{name}': {e}")
            failures += 1
            continue
        print(f"[*] Creating address group '{name}' in '{location}'...")
        try:
            pan.set(container_xpath(location, "address-group"), element)
            print(f"[✓] Created '{name}'")
        except PanoramaError as e:
            print(f"[!] Failed to create '{name}': {e}")
            failures += 1
    print("[i] Changes are staged in the candidate config; commit in Panorama when ready.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
