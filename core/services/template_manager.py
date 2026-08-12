import json
from pathlib import Path

import cv2

from core.models.template import Template


class TemplateManager:
    def __init__(self, config_path="data/templates.json"):
        self.config_path = Path(config_path)
        self.templates = {}
        self.load()

    def load(self):
        if not self.config_path.is_file():
            raise FileNotFoundError(
                f"No existe configuración: {self.config_path}"
            )

        with self.config_path.open(encoding="utf-8") as file:
            data = json.load(file)

        self.templates.clear()
        self._load_anchors(data.get("anchors", {}))
        self._load_regions(data.get("regions", {}))

    def _load_anchors(self, anchors):
        anchor_dir = self.config_path.parent / "templates" / "anchors"
        for name, info in anchors.items():
            filename = info.get("file")
            if not filename:
                raise ValueError(f"Anchor sin archivo: {name}")

            path = anchor_dir / filename
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is None:
                raise FileNotFoundError(f"No se pudo cargar: {path}")

            self.templates[name] = Template(
                name=name,
                path=str(path),
                template_type="anchor",
                threshold=float(info.get("threshold", 0.85)),
                image=image,
            )

    def _load_regions(self, regions):
        for name, info in regions.items():
            self.templates[name] = {
                "name": name,
                "type": info.get("type", "region"),
                "parent": info.get("parent"),
                "x": int(info.get("x", 0)),
                "y": int(info.get("y", 0)),
                "width": int(info.get("width", 0)),
                "height": int(info.get("height", 0)),
                "bar_type": info.get("bar_type"),
                "color": info.get("color"),
            }

    def get(self, name):
        return self.templates.get(name)

    def list(self):
        return list(self.templates)
