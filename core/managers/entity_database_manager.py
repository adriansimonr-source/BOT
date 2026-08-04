import json
import os
import re
import threading
from difflib import SequenceMatcher

from core.databases.entity_database import EntityDatabase


_DATABASE_LOCK = threading.RLock()


class EntityDatabaseManager:

    ENEMY_SIMILARITY_THRESHOLD = 0.90
    ENEMY_ALIAS_MAX_EXTRA_CHARS = 3
    ENEMY_CONFIRMATIONS_REQUIRED = 2
    MAX_ENTITY_NAME_LENGTH = 64
    ALLOWED_NAME_PUNCTUATION = frozenset(" -'’().+&[]")
    TIMER_PATTERNS = (
        re.compile(r"^\d+\s*[mh]\s*\d*\s*s?$", re.IGNORECASE),
        re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$"),
        re.compile(r"^\d+\s*[/,]\s*\d+$"),
    )
    LEVEL_PATTERN = re.compile(
        r"^(?:lv|lvl|level)\.?\s*\d+$",
        re.IGNORECASE,
    )

    def __init__(self, path="data/entities"):
        self.path = path
        self.database = EntityDatabase()
        self.players_file = os.path.join(path, "players.json")
        self.enemies_file = os.path.join(path, "enemies.json")
        self.items_file = os.path.join(path, "items.json")
        self._enemies_mtime_ns = None
        self._items_mtime_ns = None
        self._enemy_lists_cache = None
        self._pending_enemies = {}
        self.load()

    def load(self):
        with _DATABASE_LOCK:
            self.database.players.clear()
            self.database.enemies.clear()
            self.database.items.clear()
            self.load_file(self.players_file, self.database.players)
            self.load_file(self.enemies_file, self.database.enemies)
            self.load_file(self.items_file, self.database.items)
            self._enemies_mtime_ns = self._get_mtime(self.enemies_file)
            self._items_mtime_ns = self._get_mtime(self.items_file)
            self._enemy_lists_cache = None

    @staticmethod
    def load_file(file, container):
        if not os.path.exists(file):
            return False
        try:
            with open(file, "r", encoding="utf-8") as stream:
                data = json.load(stream)
            if not isinstance(data, dict):
                return False
            container.update(data)
        except (OSError, json.JSONDecodeError):
            return False
        return True

    def save(self):
        with _DATABASE_LOCK:
            os.makedirs(self.path, exist_ok=True)
            self.save_file(self.players_file, self.database.players)
            self.save_file(self.enemies_file, self.database.enemies)
            self.save_file(self.items_file, self.database.items)
            self._enemies_mtime_ns = self._get_mtime(self.enemies_file)
            self._items_mtime_ns = self._get_mtime(self.items_file)
            self._enemy_lists_cache = None

    @staticmethod
    def save_file(file, data):
        os.makedirs(os.path.dirname(file), exist_ok=True)
        temporary_file = f"{file}.{threading.get_ident()}.tmp"
        try:
            with open(temporary_file, "w", encoding="utf-8") as stream:
                json.dump(data, stream, indent=4, ensure_ascii=False)
            os.replace(temporary_file, file)
        finally:
            if os.path.exists(temporary_file):
                os.remove(temporary_file)

    def refresh_enemies(self, force=False):
        with _DATABASE_LOCK:
            current_mtime = self._get_mtime(self.enemies_file)
            if not force and current_mtime == self._enemies_mtime_ns:
                return False
            enemies = {}
            if not self.load_file(self.enemies_file, enemies):
                return False
            self.database.enemies.clear()
            self.database.enemies.update(enemies)
            self._enemies_mtime_ns = current_mtime
            self._enemy_lists_cache = None
            return True

    def refresh_items(self, force=False):
        with _DATABASE_LOCK:
            current_mtime = self._get_mtime(self.items_file)
            if not force and current_mtime == self._items_mtime_ns:
                return False
            items = {}
            if not self.load_file(self.items_file, items):
                return False
            self.database.items.clear()
            self.database.items.update(items)
            self._items_mtime_ns = current_mtime
            return True

    def resolve_enemy_name(self, name, verified=False):
        normalized = self.normalize_entity_name(name)
        if not self.is_valid_enemy_name(normalized):
            return None

        with _DATABASE_LOCK:
            self.refresh_enemies()
            canonical = self._canonical_enemy_name(normalized)
            if canonical:
                self._pending_enemies.pop(normalized.casefold(), None)
                return canonical

            confirmed_name = (
                normalized
                if verified
                else self._confirm_enemy_candidate(normalized)
            )
            if confirmed_name:
                self.database.add_enemy(confirmed_name)
                self.database.enemies[confirmed_name]["verified"] = True
                self._save_enemies()
                return confirmed_name
            return normalized

    def resolve_item_name(self, name):
        normalized = self.normalize_entity_name(name)
        if not self.is_valid_item_name(normalized):
            return None

        with _DATABASE_LOCK:
            self.refresh_items()
            canonical = self._exact_name(normalized, self.database.items)
            if canonical:
                return canonical
            self.database.add_item(normalized)
            self.database.items[normalized]["source"] = "vision_no_hp"
            self._save_items()
            return normalized

    def resolve_player_name(self, name):
        normalized = self.normalize_entity_name(name)
        if not normalized:
            return None
        if self.database.is_player(normalized):
            return normalized

        similar = self.find_similar(normalized, self.database.get_players())
        if similar:
            return similar
        self.database.add_player(normalized)
        self.save_file(self.players_file, self.database.players)
        return normalized

    @staticmethod
    def find_similar(name, collection, threshold=0.85):
        best_name = None
        best_score = 0.0
        for current in collection:
            score = SequenceMatcher(
                None,
                name.casefold(),
                current.casefold(),
            ).ratio()
            if score > best_score:
                best_score = score
                best_name = current
        return best_name if best_score >= threshold else None

    def get_enemy_lists(self):
        with _DATABASE_LOCK:
            self.refresh_enemies()
            if self._enemy_lists_cache is not None:
                enemy_names, ignored_names = self._enemy_lists_cache
                return list(enemy_names), list(ignored_names)

            canonical_names = {}
            ignored_names = {}
            for name, data in self.database.get_enemies().items():
                ignored = bool(data.get("ignore", False))
                if ignored and self.is_valid_entity_name(name):
                    canonical = self._canonical_enemy_name(name) or name
                elif self._is_trusted_enemy_record(name, data):
                    canonical = self._canonical_enemy_name(name)
                else:
                    continue
                if not canonical:
                    continue
                key = canonical.casefold()
                canonical_names[key] = canonical
                if ignored:
                    ignored_names[key] = canonical

            enemy_names = sorted(canonical_names.values(), key=str.casefold)
            ignored_names = sorted(ignored_names.values(), key=str.casefold)
            self._enemy_lists_cache = (enemy_names, ignored_names)
            return list(enemy_names), list(ignored_names)

    def get_enemy_names(self):
        return self.get_enemy_lists()[0]

    def get_ignored_enemy_names(self):
        return self.get_enemy_lists()[1]

    def get_item_names(self):
        with _DATABASE_LOCK:
            self.refresh_items()
            return sorted(
                (
                    name
                    for name in self.database.get_items()
                    if self.is_valid_item_name(name)
                ),
                key=str.casefold,
            )

    def set_enemy_ignored(self, name, ignored):
        with _DATABASE_LOCK:
            self.refresh_enemies(force=True)
            canonical = self._canonical_enemy_name(name) or name
            if not self.database.is_enemy(canonical):
                self.database.add_enemy(canonical)
                self.database.enemies[canonical]["verified"] = True

            canonical_name = canonical.casefold()
            for current, data in self.database.get_enemies().items():
                resolved = self._canonical_enemy_name(current)
                if resolved and resolved.casefold() == canonical_name:
                    data["ignore"] = bool(ignored)
            self._save_enemies()

    def get_enemy(self, name):
        with _DATABASE_LOCK:
            self.refresh_enemies()
            canonical = self._canonical_enemy_name(name) or name
            return self.database.get_enemy(canonical)

    def get_item(self, name):
        with _DATABASE_LOCK:
            self.refresh_items()
            canonical = self._exact_name(name, self.database.items) or name
            return self.database.get_item(canonical)

    def should_ignore_enemy(self, name):
        enemy = self.get_enemy(name)
        return bool(enemy and enemy.get("ignore", False))

    def get_enemy_priority(self, name):
        enemy = self.get_enemy(name)
        return enemy.get("priority", 0) if enemy else 0

    def register_enemy_seen(self, name):
        if not self.is_valid_enemy_name(name):
            return False
        with _DATABASE_LOCK:
            self.refresh_enemies(force=True)
            canonical = self._canonical_enemy_name(name)
            if not canonical:
                return False
            self.database.register_enemy_encounter(canonical)
            self._save_enemies()
            return True

    def register_item_seen(self, name):
        if not self.is_valid_item_name(name):
            return False
        with _DATABASE_LOCK:
            self.refresh_items(force=True)
            canonical = self._exact_name(name, self.database.items)
            if not canonical:
                return False
            self.database.register_item_encounter(canonical)
            self._save_items()
            return True

    def get_player(self, name):
        return self.database.get_player(name)

    def add_item(self, name, data=None):
        normalized = self.normalize_entity_name(name)
        if not self.is_valid_item_name(normalized):
            return False
        with _DATABASE_LOCK:
            self.refresh_items(force=True)
            canonical = self._exact_name(normalized, self.database.items)
            if canonical:
                return False
            self.database.add_item(normalized, data)
            self._save_items()
            return True

    def _confirm_enemy_candidate(self, name):
        key = name.casefold()
        display_name, count = self._pending_enemies.get(key, (name, 0))
        count += 1
        if count < self.ENEMY_CONFIRMATIONS_REQUIRED:
            self._pending_enemies[key] = (display_name, count)
            return None
        self._pending_enemies.pop(key, None)
        return display_name

    def _canonical_enemy_name(self, name):
        if not name:
            return None
        current_name = name
        visited = set()
        while current_name.casefold() not in visited:
            visited.add(current_name.casefold())
            best_name = self._best_enemy_match(current_name)
            if best_name is None:
                return None
            if best_name.casefold() == current_name.casefold():
                return best_name
            current_name = best_name
        return current_name

    def _best_enemy_match(self, name):
        candidates = []
        exact_match = None
        for current, data in self.database.get_enemies().items():
            if not self.is_valid_enemy_name(current):
                continue
            score = SequenceMatcher(
                None,
                name.casefold(),
                current.casefold(),
            ).ratio()
            is_exact = name.casefold() == current.casefold()
            is_alias = self._is_likely_enemy_alias(name, current)
            if (
                not is_exact
                and not is_alias
                and score < self.ENEMY_SIMILARITY_THRESHOLD
            ):
                continue
            candidate = (
                current,
                data.get("encounters", 0),
                score,
                is_alias,
            )
            candidates.append(candidate)
            if is_exact:
                exact_match = candidate

        if not candidates:
            return None
        if exact_match is not None:
            minimum_encounters = max(3, exact_match[1] * 3)
            aliases = [
                candidate
                for candidate in candidates
                if candidate[0].casefold() != exact_match[0].casefold()
                and candidate[3]
                and candidate[1] >= minimum_encounters
            ]
            if not aliases:
                return exact_match[0]
            candidates = [exact_match, *aliases]

        return max(
            candidates,
            key=lambda candidate: (
                candidate[2] if exact_match is None else candidate[1],
                candidate[1] if exact_match is None else candidate[2],
                -len(candidate[0]),
                candidate[0].casefold(),
            ),
        )[0]

    @classmethod
    def _is_likely_enemy_alias(cls, first, second):
        first_compact = cls._compact_enemy_name(first)
        second_compact = cls._compact_enemy_name(second)
        if not first_compact or not second_compact:
            return False
        shorter, longer = sorted((first_compact, second_compact), key=len)
        return (
            len(shorter) >= 4
            and shorter in longer
            and len(longer) - len(shorter)
            <= cls.ENEMY_ALIAS_MAX_EXTRA_CHARS
        )

    @staticmethod
    def _compact_enemy_name(name):
        return "".join(
            character
            for character in name.casefold()
            if character.isalnum()
        )

    @classmethod
    def normalize_entity_name(cls, name):
        normalized = " ".join(str(name or "").replace("\n", " ").split())
        return normalized.strip("|_~`\";,:")

    @classmethod
    def is_valid_entity_name(cls, name):
        normalized = cls.normalize_entity_name(name)
        if not 2 <= len(normalized) <= cls.MAX_ENTITY_NAME_LENGTH:
            return False
        if sum(character.isalpha() for character in normalized) < 2:
            return False
        if normalized[0] in cls.ALLOWED_NAME_PUNCTUATION:
            return False
        if normalized[-1] in cls.ALLOWED_NAME_PUNCTUATION:
            return False
        if any(
            not character.isalnum()
            and character not in cls.ALLOWED_NAME_PUNCTUATION
            for character in normalized
        ):
            return False
        if any(pattern.fullmatch(normalized) for pattern in cls.TIMER_PATTERNS):
            return False
        return cls.LEVEL_PATTERN.fullmatch(normalized) is None

    @classmethod
    def is_valid_enemy_name(cls, name):
        normalized = cls.normalize_entity_name(name)
        return bool(
            cls.is_valid_entity_name(normalized)
            and normalized[0].isalpha()
        )

    @classmethod
    def is_valid_item_name(cls, name):
        return cls.is_valid_entity_name(name)

    @classmethod
    def _is_trusted_enemy_record(cls, name, data):
        return bool(
            cls.is_valid_enemy_name(name)
            and (
                data.get("verified", False)
                or data.get("ignore", False)
                or data.get("priority", 0)
                or data.get("boss", False)
                or data.get("elite", False)
                or data.get("encounters", 0) >= cls.ENEMY_CONFIRMATIONS_REQUIRED
            )
        )

    @staticmethod
    def _exact_name(name, collection):
        normalized = str(name or "").casefold()
        return next(
            (
                current
                for current in collection
                if current.casefold() == normalized
            ),
            None,
        )

    def _save_enemies(self):
        self.save_file(self.enemies_file, self.database.enemies)
        self._enemies_mtime_ns = self._get_mtime(self.enemies_file)
        self._enemy_lists_cache = None

    def _save_items(self):
        self.save_file(self.items_file, self.database.items)
        self._items_mtime_ns = self._get_mtime(self.items_file)

    @staticmethod
    def _get_mtime(path):
        try:
            return os.stat(path).st_mtime_ns
        except FileNotFoundError:
            return None
