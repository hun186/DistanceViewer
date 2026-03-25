import math
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

Coordinate = Tuple[int, int]


@dataclass
class IslandInfo:
    resource: str
    wonder: str


class DataService:
    def __init__(self, excel_file: Optional[str] = None, data_file: str = "data/islands_data.json") -> None:
        self.data_path = Path(data_file).resolve()
        self.excel_path: Optional[Path] = None
        records = self._load_records(excel_file)
        self.data_dict: Dict[Coordinate, IslandInfo] = {}
        for row in records:
            coord = (int(row["x"]), int(row["y"]))
            self.data_dict[coord] = IslandInfo(
                resource=str(row.get("resource", "") or ""),
                wonder=str(row.get("wonder", "") or ""),
            )

        self.resources = sorted({v.resource for v in self.data_dict.values() if v.resource})
        self.wonders = sorted({v.wonder for v in self.data_dict.values() if v.wonder})

    @staticmethod
    def _date_key(path: Path) -> Tuple[int, str]:
        matched = re.search(r"_(\d{8})$", path.stem)
        if not matched:
            return (0, path.name)
        return (int(matched.group(1)), path.name)

    @classmethod
    def _pick_latest_file(cls, candidates: List[Path]) -> Path:
        if not candidates:
            raise FileNotFoundError("No Excel file candidates found.")
        return sorted(candidates, key=cls._date_key, reverse=True)[0]

    @classmethod
    def _resolve_excel_path(cls, excel_file: Optional[str]) -> Path:
        if excel_file:
            if "*" in excel_file:
                candidates = [path.resolve() for path in Path(".").glob(excel_file)]
                return cls._pick_latest_file(candidates)
            return Path(excel_file).resolve()

        preferred = [path.resolve() for path in Path(".").glob("Ikariam島嶼_New_*.xlsx")]
        if preferred:
            return cls._pick_latest_file(preferred)

        fallback = [path.resolve() for path in Path(".").glob("*.xlsx")]
        if fallback:
            return sorted(fallback, key=lambda p: p.stat().st_mtime, reverse=True)[0]

        raise FileNotFoundError("No Excel files found under current working directory.")

    @classmethod
    def _try_resolve_excel_path(cls, excel_file: Optional[str]) -> Optional[Path]:
        try:
            return cls._resolve_excel_path(excel_file)
        except FileNotFoundError:
            return None

    @staticmethod
    def _normalize_rows(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
        normalized = []
        for row in rows:
            normalized.append(
                {
                    "x": int(row["x"]),
                    "y": int(row["y"]),
                    "resource": str(row.get("resource", "") or ""),
                    "wonder": str(row.get("wonder", "") or ""),
                }
            )
        return normalized

    def _load_records_from_json(self) -> Optional[List[Dict[str, object]]]:
        if not self.data_path.exists():
            return None
        try:
            with self.data_path.open("r", encoding="utf-8") as data_file:
                payload = json.load(data_file)
            if isinstance(payload, list):
                return self._normalize_rows(payload)
            rows = payload.get("rows", []) if isinstance(payload, dict) else []
            if isinstance(rows, list):
                return self._normalize_rows(rows)
        except (json.JSONDecodeError, OSError, ValueError, TypeError, KeyError):
            return None
        return None

    def _load_records_from_excel(self, excel_file: Optional[str]) -> List[Dict[str, object]]:
        self.excel_path = self._resolve_excel_path(excel_file)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.excel_path}")
        df = pd.read_excel(self.excel_path)
        return [
            {
                "x": int(x),
                "y": int(y),
                "resource": str(resource or ""),
                "wonder": str(wonder or ""),
            }
            for x, y, resource, wonder in df[["X", "Y", "資源", "神蹟"]].itertuples(index=False, name=None)
        ]

    def _write_json_data(self, rows: List[Dict[str, object]]) -> None:
        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            with self.data_path.open("w", encoding="utf-8") as data_file:
                json.dump({"rows": rows}, data_file, ensure_ascii=False)
        except OSError:
            pass

    def _load_records(self, excel_file: Optional[str]) -> List[Dict[str, object]]:
        if excel_file:
            return self._load_records_from_excel(excel_file)

        excel_path = self._try_resolve_excel_path(excel_file)
        if excel_path is not None:
            self.excel_path = excel_path

        json_rows = self._load_records_from_json()
        if json_rows is not None:
            if self.excel_path is None:
                return json_rows
            if self.data_path.stat().st_mtime >= self.excel_path.stat().st_mtime:
                return json_rows

        if self.excel_path is None:
            raise FileNotFoundError("No JSON data file or Excel source available.")

        rows = self._load_records_from_excel(str(self.excel_path))
        if rows:
            self._write_json_data(rows)
        return rows

    def options(self) -> Dict[str, List[str]]:
        return {"resources": self.resources, "wonders": self.wonders}

    def query_points(
        self,
        resource: str = "",
        wonder: str = "",
        x_min: int = 0,
        x_max: int = 100,
        y_min: int = 0,
        y_max: int = 100,
    ) -> List[Dict]:
        result = []
        for (x, y), info in self.data_dict.items():
            if resource and info.resource != resource:
                continue
            if wonder and info.wonder != wonder:
                continue
            if x < x_min or x > x_max:
                continue
            if y < y_min or y > y_max:
                continue
            result.append(
                {
                    "x": x,
                    "y": y,
                    "resource": info.resource,
                    "wonder": info.wonder,
                }
            )
        return result

    @staticmethod
    def _distance(p1: Coordinate, p2: Coordinate) -> float:
        return math.dist(p1, p2)

    @staticmethod
    def _angles(pts: np.ndarray) -> List[float]:
        a = np.linalg.norm(pts[1] - pts[0])
        b = np.linalg.norm(pts[2] - pts[1])
        c = np.linalg.norm(pts[0] - pts[2])
        angle_a = np.degrees(np.arccos((b**2 + c**2 - a**2) / (2 * b * c)))
        angle_b = np.degrees(np.arccos((a**2 + c**2 - b**2) / (2 * a * c)))
        angle_c = np.degrees(np.arccos((a**2 + b**2 - c**2) / (2 * a * b)))
        return [float(angle_a), float(angle_b), float(angle_c)]

    def triangulate(self, points: List[Coordinate]) -> List[Dict]:
        if len(points) < 3:
            return []

        from scipy.spatial import Delaunay

        points_array = np.array(points)
        tri = Delaunay(points_array)
        edges = []

        for simplex in tri.simplices:
            pts = points_array[simplex]
            angles = self._angles(pts)
            if not all(angle <= 160 for angle in angles):
                continue

            for i in range(3):
                p1 = tuple(map(int, pts[i]))
                p2 = tuple(map(int, pts[(i + 1) % 3]))
                edges.append(
                    {
                        "x1": p1[0],
                        "y1": p1[1],
                        "x2": p2[0],
                        "y2": p2[1],
                        "distance": round(self._distance(p1, p2), 2),
                    }
                )

        # 去重
        uniq = {}
        for edge in edges:
            key = tuple(sorted(((edge["x1"], edge["y1"]), (edge["x2"], edge["y2"]))))
            uniq[key] = edge
        return list(uniq.values())
