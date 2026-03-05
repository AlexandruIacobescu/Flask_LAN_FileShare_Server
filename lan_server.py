# lan_https_file_server.py
import argparse
import os
import mimetypes
from datetime import datetime
from flask import Flask, render_template_string, send_file, request, abort, url_for
from pathlib import Path

app = Flask(__name__, static_folder=None)

# ---------- Utilities ----------
def safe_join(base: str, *paths) -> str:
    """Join paths and ensure the result is within base (prevent path traversal)."""
    base_path = Path(base).resolve()
    candidate = base_path.joinpath(*paths).resolve()
    if not str(candidate).startswith(str(base_path)):
        raise ValueError("Attempt to access outside of base directory")
    return str(candidate)


def format_size(nbytes: int) -> str:
    for unit in ['B','KB','MB','GB','TB']:
        if nbytes < 1024:
            return f"{nbytes:.0f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} PB"


def list_dir_entries(root: str, relpath: str = ""):
    """Return list of entries (files & dirs) for rendering."""
    target = safe_join(root, relpath) if relpath else root
    entries = []
    for entry in sorted(os.scandir(target), key=lambda e: (not e.is_dir(), e.name.lower())):
        st = entry.stat()
        entries.append({
            "name": entry.name,
            "is_dir": entry.is_dir(),
            "size": st.st_size,
            "size_str": format_size(st.st_size) if not entry.is_dir() else "--",
            "mtime": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "href": (f"/browse/{relpath.rstrip('/')}/{entry.name}".replace('//','/')) if entry.is_dir() else f"/download/{relpath.rstrip('/')}/{entry.name}".replace('//','/')
        })
    return entries

# ---------- Templates (updated contrast & removed absolute path display) ----------
LIST_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>LAN Files — {{ relpath or '/' }}</title>
<style>
:root{--bg:#041022;--card:#071427;--muted:#cbd5e1;--accent:#7c3aed;--text:#f8fbff}
body{font-family:Inter,system-ui,Segoe UI,Roboto,Arial;margin:0;background:linear-gradient(180deg,#031426,#051427);color:var(--text);min-height:100vh;display:flex;justify-content:center;align-items:flex-start;padding:28px}
.container{width:100%;max-width:1100px;background:rgba(255,255,255,0.03);border-radius:12px;padding:20px;box-shadow:0 12px 40px rgba(2,6,23,0.6)}
.header{display:flex;align-items:center;justify-content:space-between;gap:12px}
.header h1{margin:0;font-size:18px;color:var(--text)}
.controls{display:flex;gap:8px;align-items:center}
.search{padding:8px 10px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:transparent;color:var(--text)}
.table{width:100%;margin-top:14px;border-collapse:collapse}
.table thead{color:var(--muted);font-size:13px}
.table th, .table td{padding:10px 8px;text-align:left;color:var(--text)}
.row{border-bottom:1px solid rgba(255,255,255,0.04);background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.005))}
.file-icon{display:inline-block;width:36px;text-align:center;font-size:18px}
.btn{background:linear-gradient(90deg,var(--accent),#5b21b6);border:none;color:white;padding:8px 12px;border-radius:10px;cursor:pointer}
.small{font-size:13px;color:var(--muted)}
a{color:#ffffff;text-decoration:none}
a:hover{text-decoration:underline}
.row:hover{background:rgba(255,255,255,0.02)}
.breadcrumb{margin-top:8px;color:var(--muted);font-size:13px}
@media (max-width:760px){ .header{flex-direction:column;align-items:flex-start} .table td:nth-child(3),.table th:nth-child(3){display:none} }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>LAN File Share</h1>
      <div class="small">Path: <strong>{{ relpath or '/' }}</strong></div>
    </div>
    <div class="controls">
      <input id="search" class="search" placeholder="Search files..." />
      <a class="btn" href="{{ url_for('index') }}">Home</a>
    </div>
  </div>

  <div class="breadcrumb">Root → {{ relpath or '/' }}</div>

  <table class="table" id="filesTable">
    <thead>
      <tr><th></th><th>Name</th><th>Modified</th><th>Size</th><th></th></tr>
    </thead>
    <tbody>
      {% for e in entries %}
      <tr class="row" data-name="{{ e.name|lower }}">
        <td class="file-icon">{% if e.is_dir %}📁{% else %}📄{% endif %}</td>
        <td><a href="{{ e.href }}">{{ e.name }}</a></td>
        <td class="small">{{ e.mtime }}</td>
        <td class="small">{{ e.size_str }}</td>
        <td>{% if not e.is_dir %}<a class="btn" href="{{ e.href }}">Download</a>{% endif %}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <!-- absolute path display removed for privacy -->
</div>

<script>
const search = document.getElementById('search');
search.addEventListener('input', (e)=> {
  const q = e.target.value.trim().toLowerCase();
  document.querySelectorAll('#filesTable tbody tr').forEach(tr=>{
    const name = tr.dataset.name || '';
    tr.style.display = q && !name.includes(q) ? 'none' : '';
  });
});
</script>
</body>
</html>
"""

# ---------- Routes ----------
@app.route("/")
def index():
    root = app.config['ROOT_DIR']
    entries = list_dir_entries(root, "")
    return render_template_string(LIST_TEMPLATE, entries=entries, relpath="", root=root)

@app.route("/browse/<path:subpath>")
def browse(subpath):
    root = app.config['ROOT_DIR']
    try:
        safe_join(root, subpath)
    except ValueError:
        abort(403)
    entries = list_dir_entries(root, subpath)
    return render_template_string(LIST_TEMPLATE, entries=entries, relpath=subpath, root=root)

@app.route("/download/<path:filepath>")
def download(filepath):
    root = app.config['ROOT_DIR']
    try:
        abs_path = safe_join(root, filepath)
    except ValueError:
        abort(403)
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        abort(404)
    return send_file(abs_path, as_attachment=True)

# ---------- CLI ----------
def main():
    p = argparse.ArgumentParser(description="LAN HTTPS File Server")
    p.add_argument("--dirpath", default=os.path.join(os.getcwd(), "shared"), help="Root directory to share")
    p.add_argument("--host", default="0.0.0.0", help="Host to bind")
    p.add_argument("--port", type=int, default=8443, help="Port to bind (default 8443 for HTTPS)")
    p.add_argument("--cert", default=None, help="Path to TLS cert file (PEM). If omitted server runs HTTP.")
    p.add_argument("--key", default=None, help="Path to TLS key file (PEM). Required if --cert is used.")
    args = p.parse_args()

    root = os.path.abspath(args.dirpath)
    os.makedirs(root, exist_ok=True)
    app.config['ROOT_DIR'] = root

    if args.cert and args.key:
        context = (args.cert, args.key)
        print(f"Serving (HTTPS) https://{args.host}:{args.port} -> [hidden]")
        app.run(host=args.host, port=args.port, ssl_context=context)
    else:
        print(f"Serving (HTTP) http://{args.host}:{args.port} -> [hidden]")
        app.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
