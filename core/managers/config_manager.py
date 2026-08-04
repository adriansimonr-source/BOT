import json
import os


class ConfigManager:
    def __init__(self, path="data/config.json"):
        self.path = path
        self.config = {}
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"No existe configuración: {self.path}")
        with open(self.path, "r", encoding="utf-8") as file:
            self.config = json.load(file)

    def save(self):
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        temporary_path = f"{self.path}.tmp"
        try:
            with open(temporary_path, "w", encoding="utf-8") as file:
                json.dump(self.config, file, indent=4, ensure_ascii=False)
            os.replace(temporary_path, self.path)
        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

    def get(self, *keys):
        value = self.config
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        return value

    def set(self, key, value):
        self.config[key] = value

    def get_window_title(self):
        return self.get("window", "title")

    def get_process_name(self):
        return self.get("window", "process")

    def get_capture_size(self):
        return (
            self.get("capture", "width"),
            self.get("capture", "height"),
        )
