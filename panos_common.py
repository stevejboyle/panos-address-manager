"""Shared helpers for the PAN-OS address scripts: config, API calls, XPaths."""
import configparser
import csv
import os
import sys
import xml.etree.ElementTree as ET
from getpass import getpass

import requests

CONFIG_FILE = "panw.cfg"
DG_PREFIX = "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name={}]"


class Panorama:
    """Minimal PAN-OS XML API client. The key is sent in the X-PAN-KEY header,
    never in the URL, so it doesn't end up in proxy or server access logs."""

    def __init__(self, host, api_key, verify=True, timeout=30):
        self.url = host.rstrip("/") + "/api/"
        self.session = requests.Session()
        self.session.headers["X-PAN-KEY"] = api_key
        self.session.verify = verify
        self.timeout = timeout
        if verify is False:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def request(self, **params):
        """POST an API call; return the parsed <response> root. Raises
        PanoramaError on HTTP, TLS, parse or API-level failure."""
        try:
            resp = self.session.post(self.url, data=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.SSLError as e:
            raise PanoramaError(
                f"TLS verification failed: {e}\n"
                "    Set ca_bundle = /path/to/panorama-ca.pem in panw.cfg, or verify_ssl = false for a lab box."
            ) from e
        except requests.exceptions.RequestException as e:
            raise PanoramaError(f"HTTP request failed: {e}") from e
        try:
            root = ET.fromstring(resp.content)  # noqa: S314 -- response from our own Panorama
        except ET.ParseError as e:
            raise PanoramaError(f"Unparseable response: {resp.text[:300]}") from e
        if root.get("status") != "success":
            raise PanoramaError(api_error(root))
        return root

    def get(self, xpath):
        return self.request(type="config", action="get", xpath=xpath)

    def set(self, xpath, element):
        return self.request(type="config", action="set", xpath=xpath, element=element)

    def delete(self, xpath):
        return self.request(type="config", action="delete", xpath=xpath)


class PanoramaError(Exception):
    pass


def api_error(root):
    """Best human-readable error text from a PAN-OS <response>."""
    lines = [el.text.strip() for el in root.iter("line") if el.text and el.text.strip()]
    if lines:
        return "; ".join(lines)
    msg = root.find(".//msg")
    if msg is not None and (msg.text or "").strip():
        return msg.text.strip()
    return ET.tostring(root, encoding="unicode")[:300]


def xpath_literal(value):
    """Quote a value as an XPath 1.0 string literal (handles embedded quotes)."""
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"


def is_shared(location):
    return not location or location.strip().lower() == "shared"


def container_xpath(location, node):
    """XPath of the container holding <node> entries (e.g. 'address') in a scope."""
    if is_shared(location):
        return f"/config/shared/{node}"
    return DG_PREFIX.format(xpath_literal(location.strip())) + f"/{node}"


def entry_xpath(location, node, name):
    return container_xpath(location, node) + f"/entry[@name={xpath_literal(name)}]"


def load(csv_option):
    """Read panw.cfg, prompt for the API key, return (Panorama, csv_path)."""
    config = configparser.ConfigParser()
    if not config.read(CONFIG_FILE):
        sys.exit(f"[!] '{CONFIG_FILE}' not found in {os.getcwd()}. See README for the format.")
    try:
        section = config["PANW"]
        host = section["panorama_host"]
        csv_path = section[csv_option]
    except KeyError as e:
        sys.exit(f"[!] '{CONFIG_FILE}' is missing [PANW] {e}. See README for the format.")

    verify = section.get("ca_bundle") or section.getboolean("verify_ssl", fallback=True)
    if not host.startswith(("https://", "http://")):
        host = "https://" + host

    api_key = os.environ.get("PANOS_API_KEY") or getpass("Enter PAN-OS API Key: ")
    if not api_key:
        sys.exit("[!] No API key given.")
    return Panorama(host, api_key, verify=verify), csv_path


def read_rows(csv_path, aliases=None):
    """Yield non-empty CSV rows as dicts with stripped values. `aliases` maps
    alternate header names to the canonical one (e.g. dynamic -> dynamic_filter)."""
    aliases = aliases or {}
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                clean = {}
                for k, v in row.items():
                    if k is None:
                        continue
                    k = k.strip()
                    clean[aliases.get(k, k)] = (v or "").strip()
                if any(clean.values()):
                    yield clean
    except FileNotFoundError:
        sys.exit(f"[!] Input file '{csv_path}' not found. Check {CONFIG_FILE}.")


def split_list(value):
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def add_members(parent, tag, values):
    """Append <tag><member>v</member>...</tag> under parent if values is non-empty."""
    if values:
        el = ET.SubElement(parent, tag)
        for v in values:
            ET.SubElement(el, "member").text = v


def backup_and_delete(pan, node, rows, fields, to_row, label):
    """For each CSV row (needs `name`, optional `location`): read the entry,
    append it to a timestamped backup CSV in the same format the create script
    reads (so the backup can be re-imported), then delete it. Returns the
    number of failures."""
    from datetime import datetime

    backup = f"{datetime.now():%Y%m%d-%H%M%S}-{label.replace(' ', '-')}-backup.csv"
    failures = 0
    with open(backup, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            name, location = row.get("name"), row.get("location") or "shared"
            if not name:
                continue
            xpath = entry_xpath(location, node, name)
            print(f"[*] {label} '{name}' in '{location}'")
            try:
                entry = pan.get(xpath).find(".//entry")
                if entry is None:
                    print(f"[!] Not found: '{name}' in '{location}'")
                    failures += 1
                    continue
                writer.writerow({"name": name, "location": location, **to_row(entry)})
                f.flush()  # backup is on disk before the delete goes out
                pan.delete(xpath)
                print(f"[✓] Backed up and deleted '{name}'")
            except PanoramaError as e:
                print(f"[!] Failed on '{name}': {e}")
                failures += 1
    print(f"[i] Backup written to {backup}")
    print("[i] Changes are staged in the candidate config; commit in Panorama when ready.")
    return failures
