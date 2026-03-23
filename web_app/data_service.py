import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.spatial import Delaunay

Coordinate = Tuple[int, int]


@dataclass
class IslandInfo:
    resource: str
    wonder: str


class DataService:
    def __init__(self, excel_file: str = "Ikariam島嶼_New_20260323.xlsx") -> None:
        self.excel_path = Path(excel_file)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_file}")

        df = pd.read_excel(self.excel_path)
        self.data_dict: Dict[Coordinate, IslandInfo] = {}
        for _, row in df.iterrows():
            coord = (int(row["X"]), int(row["Y"]))
            self.data_dict[coord] = IslandInfo(
                resource=str(row.get("資源", "") or ""),
                wonder=str(row.get("神蹟", "") or ""),
            )

        self.resources = sorted({v.resource for v in self.data_dict.values() if v.resource})
        self.wonders = sorted({v.wonder for v in self.data_dict.values() if v.wonder})

    def options(self) -> Dict[str, List[str]]:
        return {"resources": self.resources, "wonders": self.wonders}

    def query_points(self, resource: str = "", wonder: str = "") -> List[Dict]:
        result = []
        for (x, y), info in self.data_dict.items():
            if resource and info.resource != resource:
                continue
            if wonder and info.wonder != wonder:
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
