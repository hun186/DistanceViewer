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
    try:
        x_min = int(request.args.get("x_min", 0))
        x_max = int(request.args.get("x_max", 100))
        y_min = int(request.args.get("y_min", 0))
        y_max = int(request.args.get("y_max", 100))
    except ValueError:
        return jsonify({"error": "座標範圍必須是整數。"}), 400

    if not (0 <= x_min <= x_max <= 100 and 0 <= y_min <= y_max <= 100):
        return jsonify({"error": "座標範圍需在 0~100 且最小值不可大於最大值。"}), 400

    return jsonify(
        service.query_points(
            resource=resource,
            wonder=wonder,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
        )
    )


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
