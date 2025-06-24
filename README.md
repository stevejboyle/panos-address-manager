# PAN-OS Address/Object Group Management Scripts

This repository contains a set of Python scripts to **export, delete, and recreate** address objects and address groups on **Palo Alto Networks Panorama** using the XML API.

## 📦 Contents

| Script Name                  | Description |
|-----------------------------|-------------|
| `delete_address_objects.py` | Exports and deletes address objects from Panorama, saving a CSV for later reimport. |
| `delete_address_groups.py`  | Exports and deletes address groups from Panorama, saving a CSV for later reimport. |
| `create_address_objects.py` | Recreates address objects from a previously exported CSV. |
| `create_address_groups.py`  | Recreates address groups (static or dynamic) from a previously exported CSV. |

## 📝 Requirements

- Python 3.x
- `requests` module (install with `pip3 install --user requests`)
- Access to the Panorama API and a valid API key

## 🔐 Authentication

Each script prompts for your Panorama API key at runtime using a secure input prompt (`getpass`).

## 📂 CSV Formats

### `address_objects.csv`

| name          | ip-netmask       | description     | location     | type         | tag        |
|---------------|------------------|------------------|--------------|--------------|------------|
| web-server-1  | 192.168.1.10/32  | Web frontend     | Branch-FWs   | ip-netmask   | external   |
| db-server-1   | 192.168.2.20/32  | Database server  | shared       | ip-netmask   | internal   |

### `address_groups.csv`

| name         | members                   | dynamic           | description              | location    | tag       |
|--------------|----------------------------|-------------------|---------------------------|-------------|-----------|
| web-servers  | web-server-1,api-gateway   |                   | Group of all web servers | Branch-FWs  | external  |
| api-group    |                            | 'tag eq dmz'      | Dynamic group for DMZ    | DataCenter  |           |

- **location**: Use `"shared"` for Shared scope, or specify a Panorama device group name.
- **members**: Comma-separated list of object names for static groups.
- **dynamic**: Filter string for dynamic groups (optional).

## ✅ Example Usage

### Delete and Export

```bash
python3 delete_address_objects.py
python3 delete_address_groups.py
```

### Recreate from CSV

```bash
python3 create_address_objects.py
python3 create_address_groups.py
```

## 🔒 Security Notes

- SSL verification is disabled in these scripts (`verify=False`) for compatibility. You should secure this for production use.
- API keys should be stored securely or rotated regularly.

## 📄 License

MIT License – free to use and adapt.

## 🙋‍♂️ Questions?

Open an issue or contact your automation team.