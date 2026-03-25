import pandas as pd
import pytest
import os

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


def test_auto_picks_latest_dated_excel(tmp_path, monkeypatch):
    old_file = tmp_path / "Ikariam島嶼_New_20260323.xlsx"
    new_file = tmp_path / "Ikariam島嶼_New_20260725.xlsx"
    df = pd.DataFrame([{"X": 1, "Y": 2, "資源": "木材", "神蹟": "女神"}])
    df.to_excel(old_file, index=False)
    df.to_excel(new_file, index=False)
    monkeypatch.chdir(tmp_path)

    service = DataService()

    assert service.excel_path == new_file.resolve()


def test_glob_input_picks_latest_dated_excel(tmp_path, monkeypatch):
    old_file = tmp_path / "Ikariam島嶼_New_20250101.xlsx"
    new_file = tmp_path / "Ikariam島嶼_New_20251231.xlsx"
    df = pd.DataFrame([{"X": 1, "Y": 2, "資源": "木材", "神蹟": "女神"}])
    df.to_excel(old_file, index=False)
    df.to_excel(new_file, index=False)
    monkeypatch.chdir(tmp_path)

    service = DataService("Ikariam島嶼_New_*.xlsx")

    assert service.excel_path == new_file.resolve()


def test_default_uses_json_data_source_without_excel(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_file = data_dir / "islands_data.json"
    data_file.write_text(
        '{"rows":[{"x":10,"y":20,"resource":"木材","wonder":"女神"}]}',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    service = DataService()

    assert service.options()["resources"] == ["木材"]
    assert service.options()["wonders"] == ["女神"]


def test_refreshes_json_when_excel_is_newer(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_file = data_dir / "islands_data.json"
    data_file.write_text(
        '{"rows":[{"x":1,"y":1,"resource":"舊資源","wonder":"舊神蹟"}]}',
        encoding="utf-8",
    )

    excel_file = tmp_path / "Ikariam島嶼_New_20260725.xlsx"
    df = pd.DataFrame([{"X": 2, "Y": 2, "資源": "新資源", "神蹟": "新神蹟"}])
    df.to_excel(excel_file, index=False)
    os.utime(data_file, (1, 1))
    os.utime(excel_file, (2, 2))
    monkeypatch.chdir(tmp_path)

    service = DataService()

    result = service.query_points(resource="新資源", wonder="新神蹟", x_min=0, x_max=100, y_min=0, y_max=100)
    assert result == [{"x": 2, "y": 2, "resource": "新資源", "wonder": "新神蹟"}]
