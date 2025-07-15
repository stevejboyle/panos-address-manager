import csv
import requests
import urllib3
from getpass import getpass
import configparser
import xml.etree.ElementTree as ET

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
config = configparser.ConfigParser()
# Ensure you have a 'panw.cfg' file in the same directory
# with a section like:
# [PANW]
# panorama_host = https://your_panorama_ip
# address_csv = addresses_to_create.csv
try:
    config.read("panw.cfg")
    PANORAMA_HOST = config.get("PANW", "panorama_host")
    CSV_FILE = config.get("PANW", "address_csv")
except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"Error reading configuration file: {e}")
    print("Please ensure 'panw.cfg' exists and is correctly formatted.")
    exit()

API_KEY = getpass("Enter PAN-OS API Key: ")

def create_address_object(row):
    """
    Creates a Panorama address object based on a row from a CSV file.

    Args:
        row (dict): A dictionary representing a row from the input CSV.
                    Expected keys: 'name', 'location', 'value', 'type',
                                   'description', 'tag'.
    """
    # Use .get() for safe access to dictionary keys, providing default empty strings
    name = row.get("name", "").strip()
    if not name:
        print("[!] Skipping row due to missing 'name'.")
        return

    location = row.get("location", "shared").strip() or "shared"
    value = row.get("value", "").strip()
    obj_type = row.get("type", "").strip()
    description = row.get("description", "").strip()
    tags = [t.strip() for t in row.get("tag", "").split(",") if t.strip()]

    if not value or not obj_type:
        print(f"[!] Skipping '{name}' due to missing 'value' or 'type'.")
        return

    # Determine the correct XPath for the API call
    is_shared = location.lower() == "shared"
    if is_shared:
        xpath = "/config/shared/address"
    else:
        xpath = (f"/config/devices/entry[@name='localhost.localdomain']"
                 f"/device-group/entry[@name='{location}']/address")

    # --- Build the XML element using ElementTree ---
    element = ET.Element("entry", name=name)

    # Add the correct element based on the object type
    if obj_type.lower() == "ip-netmask":
        ip_el = ET.SubElement(element, "ip-netmask")
        ip_el.text = value
    elif obj_type.lower() == "ip-range":
        ip_el = ET.SubElement(element, "ip-range")
        ip_el.text = value
    elif obj_type.lower() == "fqdn":
        ip_el = ET.SubElement(element, "fqdn")
        ip_el.text = value
    else:
        print(f"[!] Skipping '{name}' due to unknown type: '{obj_type}'.")
        return

    if description:
        desc_el = ET.SubElement(element, "description")
        desc_el.text = description

    if tags:
        tag_el = ET.SubElement(element, "tag")
        for tag in tags:
            member_el = ET.SubElement(tag_el, "member")
            member_el.text = tag

    # Convert the ElementTree object to a string for the API payload
    xml_payload = ET.tostring(element, encoding="unicode")

    # --- Make the API call to create the object ---
    params = {
        "type": "config",
        "action": "set",
        "xpath": xpath,
        "element": xml_payload,
        "key": API_KEY
    }

    print(f"[*] Attempting to create address object '{name}' in '{location}'...'{params}'...")
    try:
        response = requests.get(f"{PANORAMA_HOST}/api/", params=params, verify=False, timeout=10)
        response.raise_for_status()

        if 'status="success"' in response.text:
            print(f"[✓] Successfully created address object: '{name}'")
        else:
            try:
                error_root = ET.fromstring(response.content)
                msg_element = error_root.find(".//msg/line") or error_root.find(".//msg")
                if msg_element is not None:
                    print(f"[!] Failed to create '{name}': {msg_element.text.strip()}")
                else:
                    print(f"[!] Failed to create '{name}': {response.text}")
            except ET.ParseError:
                print(f"[!] Failed to create '{name}': {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"[!] HTTP Request failed for '{name}': {e}")


def main():
    """
    Main function to read a CSV and initiate the address object creation process.
    The CSV should have the headers:
    name,location,value,type,description,tag
    """
    try:
        with open(CSV_FILE, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            f.seek(0)

            for row in reader:
                # Ensure we don't process an empty row
                if any(field.strip() for field in row.values()):
                    create_address_object(row)
    except FileNotFoundError:
        print(f"[!] Error: The input file '{CSV_FILE}' was not found.")
        print("Please ensure 'panw.cfg' is configured with the correct file path.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
