"""Create Panorama address objects from the address_csv file in panw.cfg.

CSV headers: name,value,type,description,location,tag
"""
import sys
import xml.etree.ElementTree as ET

from panos_common import PanoramaError, add_members, container_xpath, load, read_rows, split_list

TYPES = {"ip-netmask", "ip-range", "fqdn"}


def build_entry(row):
    """Return (location, element_xml) for a CSV row, or raise ValueError."""
    name, value, obj_type = row.get("name"), row.get("value"), row.get("type", "").lower()
    if not name:
        raise ValueError("missing 'name'")
    if not value or not obj_type:
        raise ValueError("missing 'value' or 'type'")
    if obj_type not in TYPES:
        raise ValueError(f"unknown type '{obj_type}' (use {', '.join(sorted(TYPES))})")
    entry = ET.Element("entry", name=name)
    ET.SubElement(entry, obj_type).text = value
    if row.get("description"):
        ET.SubElement(entry, "description").text = row["description"]
    add_members(entry, "tag", split_list(row.get("tag")))
    return row.get("location") or "shared", ET.tostring(entry, encoding="unicode")


def main():
    pan, csv_path = load("address_csv")
    failures = 0
    for row in read_rows(csv_path):
        name = row.get("name") or "<no name>"
        try:
            location, element = build_entry(row)
        except ValueError as e:
            print(f"[!] Skipping '{name}': {e}")
            failures += 1
            continue
        print(f"[*] Creating address object '{name}' in '{location}'...")
        try:
            pan.set(container_xpath(location, "address"), element)
            print(f"[✓] Created '{name}'")
        except PanoramaError as e:
            print(f"[!] Failed to create '{name}': {e}")
            failures += 1
    print("[i] Changes are staged in the candidate config; commit in Panorama when ready.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
