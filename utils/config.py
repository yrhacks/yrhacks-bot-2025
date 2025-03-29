from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Generator

import discord

class ConfigNamespace(Mapping[str, Any]):
    def __init__(self, data: dict) -> None:
        self.__dict__.update(data) # namespace = ConfigNamespace({'foo': 'bar'}) -> namespace.foo -> 'bar'

    def __iter__(self) -> Generator[str, None]:
        yield from self.__dict__.keys() # e.g. list(ConfigNamespace(...)) -> ['key1', 'key2']

    def __getitem__(self, key: str) -> Any:
        return self.__dict__[key] # e.g ConfigNamespace(...)['foo']

    def __len__(self) -> int:
        return len(self.__dict__) # e.g. equivalent to len(list(ConfigNamespace(...)))

    def __getattr__(self, name: str) -> Any:
        try:
            return self.__dict__[name] # e.g. ConfigNamespace(...).foo
        except IndexError:
            raise AttributeError(name)

    def __repr__(self) -> str:
        return f"ConfigNamespace({self.__dict__})"

class Config(ConfigNamespace):
    def __init__(self, data: Mapping[str, Any]) -> None:
        self.transform_data(data)
        self.bot = ConfigNamespace(data['bot'])
        self.embeds = ConfigNamespace(data['embeds'])
        self.database = ConfigNamespace(data['database'])

    def transform_data(self, data: Mapping[str, Any]) -> None:
        data['embeds']['info_color'] = discord.Color(int(data['embeds']['info_color'], 16))
        data['embeds']['success_color'] = discord.Color(int(data['embeds']['success_color'], 16))
        data['embeds']['error_color'] = discord.Color(int(data['embeds']['error_color'], 16))
