# Flask LAN HTTPS File Share Server

A simple and secure file browsing and download utility built with Flask. This script allows you to share a directory over your local network (LAN) with optional HTTPS support. It displays a modern, responsive file listing, supports nested folders, and prevents path traversal attacks.

## Features

- Browse files and directories within a specified root
- Display file icons, sizes, and modification timestamps
- Search within the current directory in real-time
- Download individual files as attachments
- Optional HTTPS support using provided certificate and key
- Prevention of directory traversal with `safe_join`
- Styled, dark-themed UI with responsive layout

## Installation

1. Clone or download this repository.
2. Create a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install flask
   ```

## Usage

Run the server using the provided `lan_server.py` script. The example below shares the `shared` folder in the repository:

```bash
python lan_server.py --dirpath /path/to/share --host 0.0.0.0 --port 8443
```

### CLI options

- `--dirpath` – root directory to serve (defaults to `shared` in the current working directory)
- `--host` – bind address (default `0.0.0.0`)
- `--port` – port number (default `8443` for HTTPS, `5000` for HTTP when certificates are not provided)
- `--cert` – path to TLS certificate file (PEM). If omitted, server runs plain HTTP.
- `--key` – path to TLS key file (PEM). Required when `--cert` is specified.

### HTTPS example

```bash
python lan_server.py --dirpath shared --cert cert.pem --key key.pem
```

Web browser will connect to `https://<host>:<port>` and show the file listing.

## Security

- `safe_join()` enforces that requests cannot traverse outside the root directory.
- Accessing invalid or unauthorized paths returns a `403 Forbidden` error.
- Non-existent files return `404 Not Found`.

## Customization

- Modify the `LIST_TEMPLATE` string in `lan_server.py` to change the HTML/CSS
- Add or update file type icons in the `icons` dictionary in `list_dir_entries`

## Development

Feel free to fork and extend the project. Contributions such as search filtering, upload support, or authentication are welcome.

## License

This project is released under the MIT License.
