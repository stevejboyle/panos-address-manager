import csv
import requests
import urllib3
from getpass import getpass
from datetime import datetime
import configparser
import xml.etree.ElementTree as ET

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
config = configparser.ConfigParser()
# Ensure you have a 'panw.cfg' file in the same directory
# with a section like:
# [PANW]
# panorama_host = https://your_panorama_ip
# address_csv = addresses_to_delete.csv
try:
    config.read("panw.cfg")
    PANORAMA_HOST = config.get("PANW", "panorama_host")
    CSV_FILE = config.get("PANW", "address_csv")
except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"Error reading configuration file: {e}")
    print("Please ensure 'panw.cfg' exists and is correctly formatted.")
    exit()

API_KEY = getpass("Enter PAN-OS API Key: ")

# --- Output File Setup ---
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
OUTPUT_FILE = f"{timestamp}-address-object-backup.csv"
# Define headers for the CSV backup file. Using 'fqdn' as well for FQDN objects.
OUT_FIELDS = ["name", "value", "type", "description", "location", "tag"]

with open(OUTPUT_FILE, mode='w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=OUT_FIELDS)
    writer.writeheader()
    writer.writerow({
        "name": "Example Name",
        "value": "Example: 1.1.1.1/32, 2.2.2.0/24, or host.example.com",
        "type": "Example: ip-netmask, ip-range, or fqdn",
        "description": "Example Description",
        "location": "Example: shared or a Device-Group name",
        "tag": "Example: Tag1,Tag2"
    })


def export_then_delete_address(name, device_group=None):
    """
    Exports an address object to a CSV file and then deletes it from Panorama.

    Args:
        name (str): The name of the address object to delete.
        device_group (str, optional): The device group where the object resides.
                                     Defaults to None for a 'Shared' location.
    """
    is_shared = not device_group or device_group.strip().lower() == "shared"
    location = "shared" if is_shared else device_group.strip()

    if is_shared:
        xpath = f"/config/shared/address/entry[@name='{name}']"
    else:
        xpath = (f"/config/devices/entry[@name='localhost.localdomain']"
                 f"/device-group/entry[@name='{device_group.strip()}']"
                 f"/address/entry[@name='{name}']")

    print(f"[*] Processing: '{name}' in '{location}'")
    print(f"    XPath: {xpath}")

    # --- Step 1: Get the address object configuration ---
    export_params = {
        'type': 'config',
        'action': 'get',
        'xpath': xpath,
        'key': API_KEY
    }

    try:
        response = requests.get(f"{PANORAMA_HOST}/api/", params=export_params, verify=False, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"[!] HTTP Request failed: {e}")
        return

    # --- Step 2: Parse the XML response and back up the details ---
    try:
        root = ET.fromstring(response.content)
        entry = root.find('.//entry')

        if entry is None:
            print(f"[!] Could not find address object '{name}' in '{location}'.")
            return

        values = {"name": name, "location": location}

        # Determine object type and get its value
        ip_netmask = entry.find('ip-netmask')
        ip_range = entry.find('ip-range')
        fqdn = entry.find('fqdn')

        if ip_netmask is not None:
            values["type"] = "ip-netmask"
            values["value"] = ip_netmask.text
        elif ip_range is not None:
            values["type"] = "ip-range"
            values["value"] = ip_range.text
        elif fqdn is not None:
            values["type"] = "fqdn"
            values["value"] = fqdn.text
        else:
            values["type"] = "unknown"
            values["value"] = ""

        # Extract description and tags
        description = entry.find('description')
        values["description"] = description.text if description is not None else ""

        tags = [t.text for t in entry.findall('./tag/member')]
        values["tag"] = ",".join(tags)

        # Write the extracted data to the backup CSV
        with open(OUTPUT_FILE, mode='a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=OUT_FIELDS)
            writer.writerow(values)
        print(f"[✓] Successfully backed up '{name}'.")

    except ET.ParseError as e:
        print(f"[!] Failed to parse XML response for '{name}': {e}")
        print(f"    Response Text: {response.text}")
        return

    # --- Step 3: Delete the address object ---
    delete_params = {
        'type': 'config',
        'action': 'delete',
        'xpath': xpath,
        'key': API_KEY
    }

    try:
        del_resp = requests.get(f"{PANORAMA_HOST}/api/", params=delete_params, verify=False, timeout=10)
        del_resp.raise_for_status()

        if 'status="success"' in del_resp.text:
            print(f"[✓] Successfully deleted address object '{name}' from '{location}'.")
        else:
            print(f"[!] Failed to delete '{name}': {del_resp.text}")

    except requests.exceptions.RequestException as e:
        print(f"[!] HTTP Request failed during deletion: {e}")


def main():
    """
    Main function to read a CSV and initiate the deletion process.
    """
    try:
        with open(CSV_FILE, newline='') as csvfile:
            # Skip the header and example row
            reader = csv.reader(csvfile)
            next(reader, None)
            next(reader, None)
            for row in reader:
                if not row:
                    continue
                name = row[0].strip()
                device_group = row[1].strip() if len(row) > 1 and row[1].strip() else None
                if name:
                    export_then_delete_address(name, device_group)
    except FileNotFoundError:
        print(f"[!] Error: The input file '{CSV_FILE}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()