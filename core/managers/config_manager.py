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

    def get_game_target_filters(self, game_id):
        filters = self.get("target_filters", str(game_id or ""))
        if not isinstance(filters, dict):
            filters = {}
        unique_targets = self._normalize_names(filters.get("unique_targets", []))
        return {
            "unique_targets": unique_targets,
            "ignore_enabled": bool(filters.get("ignore_enabled", False)),
            "unique_enabled": bool(
                filters.get("unique_enabled", False) and unique_targets
            ),
        }

    def set_game_target_filters(
        self,
        game_id,
        unique_targets,
        ignore_enabled=False,
        unique_enabled=False,
    ):
        game_id = str(game_id or "").strip()
        if not game_id:
            return False

        normalized_targets = self._normalize_names(unique_targets)
        filters = {
            "unique_targets": normalized_targets,
            "ignore_enabled": bool(ignore_enabled),
            "unique_enabled": bool(unique_enabled and normalized_targets),
        }
        all_filters = self.config.get("target_filters")
        if not isinstance(all_filters, dict):
            all_filters = {}
            self.config["target_filters"] = all_filters
        if all_filters.get(game_id) == filters:
            return False
        all_filters[game_id] = filters
        self.save()
        return True

    def remove_game_target_filters(self, game_id):
        all_filters = self.config.get("target_filters")
        if not isinstance(all_filters, dict) or game_id not in all_filters:
            return False
        del all_filters[game_id]
        self.save()
        return True

    @staticmethod
    def _normalize_names(names):
        if isinstance(names, str):
            names = [names]
        normalized = {}
        for name in names or []:
            display_name = str(name or "").strip()
            if display_name:
                normalized.setdefault(display_name.casefold(), display_name)
        return list(normalized.values())

    def get_window_title(self):
        return self.get("window", "title")

    def get_process_name(self):
        return self.get("window", "process")

    def get_capture_size(self):
        return (
            self.get("capture", "width"),
            self.get("capture", "height"),
        )
