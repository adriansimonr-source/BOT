import json
import os
from copy import deepcopy

from core.runtime_paths import data_path


class ConfigManager:
    def __init__(self, path=None):
        self.path = str(data_path("config.json") if path is None else path)
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
        return {"ignore_enabled": bool(filters.get("ignore_enabled", False))}

    def set_game_target_filters(
        self,
        game_id,
        ignore_enabled=False,
    ):
        game_id = str(game_id or "").strip()
        if not game_id:
            return False

        filters = {"ignore_enabled": bool(ignore_enabled)}
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

    def get_automation_profile_names(self):
        profiles = self.config.get("automation_profiles")
        if not isinstance(profiles, dict):
            return []
        return sorted(
            (
                name
                for name, settings in profiles.items()
                if isinstance(name, str)
                and name.strip()
                and isinstance(settings, dict)
            ),
            key=str.casefold,
        )

    def get_automation_profile(self, name):
        requested_name = str(name or "").strip().casefold()
        if not requested_name:
            return None

        profiles = self.config.get("automation_profiles")
        if not isinstance(profiles, dict):
            return None
        for profile_name, settings in profiles.items():
            if (
                isinstance(profile_name, str)
                and profile_name.casefold() == requested_name
                and isinstance(settings, dict)
            ):
                return deepcopy(settings)
        return None

    def set_automation_profile(self, name, settings):
        profile_name = str(name or "").strip()
        if not profile_name:
            raise ValueError("El perfil necesita un nombre.")
        if len(profile_name) > 40:
            raise ValueError("El nombre del perfil no puede superar 40 caracteres.")
        if not isinstance(settings, dict):
            raise ValueError("La configuración del perfil no es válida.")

        profiles = self.config.get("automation_profiles")
        if not isinstance(profiles, dict):
            profiles = {}
            self.config["automation_profiles"] = profiles

        stored_name = next(
            (
                current_name
                for current_name in profiles
                if isinstance(current_name, str)
                and current_name.casefold() == profile_name.casefold()
            ),
            profile_name,
        )
        profile_settings = deepcopy(settings)
        if profiles.get(stored_name) != profile_settings:
            profiles[stored_name] = profile_settings
            self.save()
        return stored_name

    def remove_automation_profile(self, name):
        requested_name = str(name or "").strip().casefold()
        profiles = self.config.get("automation_profiles")
        if not requested_name or not isinstance(profiles, dict):
            return False

        stored_name = next(
            (
                profile_name
                for profile_name in profiles
                if isinstance(profile_name, str)
                and profile_name.casefold() == requested_name
            ),
            None,
        )
        if stored_name is None:
            return False
        del profiles[stored_name]
        self.save()
        return True
