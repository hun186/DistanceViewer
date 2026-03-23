import pandas as pd
import pytest

from web_app.data_service import DataService


@pytest.fixture
def sample_excel(tmp_path):
    file_path = tmp_path / "sample.xlsx"
    df = pd.DataFrame(
        [
            {"X": 1, "Y": 2, "資源": "木材", "神蹟": "赫菲斯托斯的熔爐"},
            {"X": 5, "Y": 6, "資源": "葡萄酒", "神蹟": "雅典娜神廟"},
            {"X": 9, "Y": 3, "資源": "木材", "神蹟": "雅典娜神廟"},
        ]
    )
    df.to_excel(file_path, index=False)
    return file_path


def test_options_returns_sorted_unique_values(sample_excel):
    service = DataService(str(sample_excel))

    options = service.options()

    assert options["resources"] == sorted(["木材", "葡萄酒"])
    assert options["wonders"] == sorted(["赫菲斯托斯的熔爐", "雅典娜神廟"])


def test_query_points_applies_filters_and_bounds(sample_excel):
    service = DataService(str(sample_excel))

    result = service.query_points(resource="木材", wonder="雅典娜神廟", x_min=0, x_max=10, y_min=0, y_max=5)

    assert result == [
        {"x": 9, "y": 3, "resource": "木材", "wonder": "雅典娜神廟"},
    ]


def test_triangulate_returns_edges_for_triangle(sample_excel):
    service = DataService(str(sample_excel))

    edges = service.triangulate([(0, 0), (3, 0), (0, 4)])

    edge_pairs = {
        frozenset(((edge["x1"], edge["y1"]), (edge["x2"], edge["y2"])))
        for edge in edges
    }
    assert edge_pairs == {
        frozenset(((0, 0), (3, 0))),
        frozenset(((3, 0), (0, 4))),
        frozenset(((0, 4), (0, 0))),
    }

    distances = sorted(edge["distance"] for edge in edges)
    assert distances == [3.0, 4.0, 5.0]


def test_triangulate_with_fewer_than_three_points_returns_empty(sample_excel):
    service = DataService(str(sample_excel))

    assert service.triangulate([(1, 1), (2, 2)]) == []
