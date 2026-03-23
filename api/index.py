from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from web_app.data_service import DataService

app = Flask(__name__, static_folder="../public", static_url_path="/")
service = DataService()


@app.get("/")
def root():
    public_dir = (Path(__file__).resolve().parent.parent / "public").resolve()
    return send_from_directory(public_dir, "index.html")


@app.get("/api/options")
def options():
    return jsonify(service.options())


@app.get("/api/points/query")
def query_points():
    resource = request.args.get("resource", "").strip()
    wonder = request.args.get("wonder", "").strip()
    return jsonify(service.query_points(resource=resource, wonder=wonder))


@app.post("/api/triangulate")
def triangulate():
    payload = request.get_json(silent=True) or {}
    points = payload.get("points", [])
    normalized = []
    for point in points:
        try:
            normalized.append((int(point["x"]), int(point["y"])))
        except (KeyError, TypeError, ValueError):
            continue
    return jsonify(service.triangulate(normalized))


# Vercel serverless expects `app` variable
