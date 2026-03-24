from api import index


class FakeService:
    def __init__(self):
        self.query_calls = []
        self.triangulate_calls = []

    def options(self):
        return {"resources": ["木材"], "wonders": ["雅典娜神廟"]}

    def query_points(self, **kwargs):
        self.query_calls.append(kwargs)
        return [{"x": 1, "y": 2, "resource": "木材", "wonder": "雅典娜神廟"}]

    def triangulate(self, points):
        self.triangulate_calls.append(points)
        return [{"x1": 1, "y1": 2, "x2": 3, "y2": 4, "distance": 2.83}]


def test_options_endpoint_returns_service_options(monkeypatch):
    fake_service = FakeService()
    monkeypatch.setattr(index, "service", fake_service)

    client = index.app.test_client()
    response = client.get("/api/options")

    assert response.status_code == 200
    assert response.get_json() == {"resources": ["木材"], "wonders": ["雅典娜神廟"]}


def test_query_points_endpoint_parses_and_forwards_params(monkeypatch):
    fake_service = FakeService()
    monkeypatch.setattr(index, "service", fake_service)

    client = index.app.test_client()
    response = client.get(
        "/api/points/query?resource=木材&wonder=雅典娜神廟&x_min=1&x_max=9&y_min=2&y_max=10"
    )

    assert response.status_code == 200
    assert response.get_json() == [{"x": 1, "y": 2, "resource": "木材", "wonder": "雅典娜神廟"}]
    assert fake_service.query_calls == [
        {
            "resource": "木材",
            "wonder": "雅典娜神廟",
            "x_min": 1,
            "x_max": 9,
            "y_min": 2,
            "y_max": 10,
        }
    ]


def test_query_points_endpoint_rejects_non_integer_bounds():
    client = index.app.test_client()
    response = client.get("/api/points/query?x_min=abc")

    assert response.status_code == 400
    assert response.get_json() == {"error": "座標範圍必須是整數。"}


def test_query_points_endpoint_rejects_invalid_range():
    client = index.app.test_client()
    response = client.get("/api/points/query?x_min=50&x_max=40")

    assert response.status_code == 400
    assert response.get_json() == {"error": "座標範圍需在 0~100 且最小值不可大於最大值。"}


def test_triangulate_endpoint_normalizes_points(monkeypatch):
    fake_service = FakeService()
    monkeypatch.setattr(index, "service", fake_service)

    client = index.app.test_client()
    response = client.post(
        "/api/triangulate",
        json={
            "points": [
                {"x": "1", "y": 2},
                {"x": 3, "y": "4"},
                {"x": "bad", "y": 5},
                {"invalid": True},
            ]
        },
    )

    assert response.status_code == 200
    assert response.get_json() == [{"x1": 1, "y1": 2, "x2": 3, "y2": 4, "distance": 2.83}]
    assert fake_service.triangulate_calls == [[(1, 2), (3, 4)]]
