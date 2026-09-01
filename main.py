from __future__ import annotations

import json
import math
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import astrbot.api.message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

ENABLE_MEME = True
DATA_FILE = "meme_data.json"

MEME_PATTERN = re.compile(r"<meme:([^<>]+)>")


@dataclass(slots=True)
class MemeItem:
    url: str
    tags: frozenset[str]
    weight: float


def _normalize_tags(tags: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for tag in tags:
        if not isinstance(tag, str):
            continue

        value = tag.strip().lower()
        if not value or value in seen:
            continue

        seen.add(value)
        normalized.append(value)

    return normalized


def _is_valid_http_url(url: object) -> bool:
    if not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def _extract_and_clean_meme_marks(text: str) -> tuple[str, list[list[str]]]:
    found_tags: list[list[str]] = []

    def _replace(match: re.Match[str]) -> str:
        raw_tags = match.group(1)
        found_tags.append(_normalize_tags(raw_tags.split(",")))
        return ""

    cleaned = MEME_PATTERN.sub(_replace, text)
    return cleaned, found_tags


@register(
    "astrbot_plugin_ayling_meme",
    "ayling",
    "基于 <meme:...> 标记的极简 URL 表情包发送插件",
    "1.0.0",
)
class AylingMemePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.last_sent_url: str | None = None

    @staticmethod
    def _parse_weight(raw_weight: object) -> float:
        if raw_weight is None or isinstance(raw_weight, bool):
            return 1.0

        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            return 1.0

        if not math.isfinite(weight) or weight <= 0:
            return 1.0

        return weight

    def _data_path(self) -> Path:
        return Path(__file__).resolve().parent / DATA_FILE

    def _load_meme_items(self) -> list[MemeItem]:
        data_path = self._data_path()
        if not data_path.is_file():
            return []

        try:
            raw_data = data_path.read_text(encoding="utf-8")
            payload = json.loads(raw_data)
        except (OSError, json.JSONDecodeError):
            return []

        if not isinstance(payload, list):
            return []

        items: list[MemeItem] = []
        for item in payload:
            if not isinstance(item, dict):
                continue

            url = item.get("url")
            if not _is_valid_http_url(url):
                continue

            raw_tags = item.get("tags")
            if not isinstance(raw_tags, list):
                continue

            tags = _normalize_tags(raw_tags)
            if not tags:
                continue

            items.append(
                MemeItem(
                    url=url,
                    tags=frozenset(tags),
                    weight=self._parse_weight(item.get("weight")),
                )
            )

        return items

    def _pick_meme_url(self, input_tags: list[str]) -> str | None:
        tags = _normalize_tags(input_tags)
        if not tags:
            return None

        memes = self._load_meme_items()
        if not memes:
            return None

        input_tag_set = set(tags)
        # 先做全量标签匹配，只有没有全匹配时才退化到“命中最多”的候选集合。
        full_match_candidates = [
            meme for meme in memes if input_tag_set.issubset(meme.tags)
        ]

        if full_match_candidates:
            candidates = full_match_candidates
        else:
            best_hit_count = 0
            candidates: list[MemeItem] = []

            for meme in memes:
                hit_count = len(input_tag_set & meme.tags)
                if hit_count <= 0:
                    continue

                if hit_count > best_hit_count:
                    best_hit_count = hit_count
                    candidates = [meme]
                elif hit_count == best_hit_count:
                    candidates.append(meme)

            if best_hit_count <= 0:
                return None

        if self.last_sent_url and len(candidates) > 1:
            filtered = [meme for meme in candidates if meme.url != self.last_sent_url]
            if filtered:
                candidates = filtered

        chosen = random.choices(
            population=candidates,
            weights=[meme.weight for meme in candidates],
            k=1,
        )[0]

        self.last_sent_url = chosen.url
        return chosen.url

    @staticmethod
    def _replace_chain(result: object, new_chain: list[object]) -> None:
        chain = getattr(result, "chain", None)
        if chain is None:
            return

        try:
            chain.clear()
            chain.extend(new_chain)
        except Exception:
            try:
                result.chain = new_chain
            except Exception:
                pass

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        result = event.get_result()
        if result is None or not hasattr(result, "chain"):
            return

        chain = getattr(result, "chain", None)
        if chain is None:
            return

        new_chain: list[object] = []
        found_meme_mark = False
        first_tags: list[str] | None = None

        for component in list(chain):
            if not isinstance(component, Comp.Plain):
                new_chain.append(component)
                continue

            text = getattr(component, "text", None)
            if not isinstance(text, str):
                new_chain.append(component)
                continue

            # 只从 Plain 里提取标记，并把所有 <meme:...> 从最终文本中移除。
            cleaned_text, found_tags = _extract_and_clean_meme_marks(text)
            if found_tags:
                found_meme_mark = True
                if first_tags is None:
                    first_tags = found_tags[0]

            if cleaned_text:
                new_chain.append(Comp.Plain(text=cleaned_text))

        if not found_meme_mark:
            return

        self._replace_chain(result, new_chain)

        if not ENABLE_MEME:
            return

        image_url = self._pick_meme_url(first_tags or [])
        if not _is_valid_http_url(image_url):
            return

        try:
            result.chain.append(Comp.Image.fromURL(image_url))
        except Exception:
            return
