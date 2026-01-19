from typing import Callable

import hikari
from hikari import ButtonStyle
from lightbulb.components.menus import InteractiveButton, LinkButton, Menu
from pydantic import HttpUrl

from model.schemas import ActionButton, HyperlinkButton


class MenuHelper:
    @staticmethod
    def get_button(
        instance: Menu,
        key: ActionButton | HyperlinkButton,
        on_press: Callable | None = None,
        custom_id: str | None = None,
    ) -> InteractiveButton | LinkButton:
        label: str | None = key.label
        emoji: str | None = key.emoji
        disabled: bool = key.disabled

        if isinstance(key, ActionButton):
            style: str = key.style

            if not on_press:
                raise ValueError("on_press must be provided for ActionButton")

            return instance.add_interactive_button(
                style=MenuHelper._get_button_style(style),
                on_press=on_press,
                custom_id=custom_id or hikari.UNDEFINED,
                label=label or hikari.UNDEFINED,
                emoji=emoji or hikari.UNDEFINED,
                disabled=disabled,
            )
        elif isinstance(key, HyperlinkButton):
            url: HttpUrl = key.url

            return instance.add_link_button(
                url=url.encoded_string(),
                label=label or hikari.UNDEFINED,
                emoji=emoji or hikari.UNDEFINED,
                disabled=disabled,
            )

    @staticmethod
    def _get_button_style(style: str):
        if style == "PRIMARY":
            return ButtonStyle.PRIMARY
        elif style == "SECONDARY":
            return ButtonStyle.SECONDARY
        elif style == "SUCCESS":
            return ButtonStyle.SUCCESS
        elif style == "DANGER":
            return ButtonStyle.DANGER
        else:
            raise ValueError(f"Invalid button style: {style}")
