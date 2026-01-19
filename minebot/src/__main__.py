import asyncio
import os
import sys
from logging import Logger

os.environ["LINKD_DI_DISABLED"] = "true"

import hikari
import lightbulb

from core import GlobalState
from database import close_database, initialize_database
from debug import get_logger, setup_logging
from exceptions.command import CommandExecutionError
from exceptions.utility import EmptyException
from hooks.database import add_or_update_user
from model import BotKeys, CommandsKeys, SecretKeys
from settings import Localization, Settings
from websocket import WebSocketServer

if __name__ == "__main__":
    setup_logging()

    logger: Logger = get_logger(__name__)
    logger.info("Starting bot initialization")

    if os.name != "nt":
        import uvloop

        logger.debug("Using uvloop as the event loop policy")
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    else:
        logger.debug("Using default asyncio event loop policy")

    try:
        Settings.initialize()
        Localization.initialize()
        websocket = WebSocketServer()

        bot = hikari.GatewayBot(
            token=Settings.get(SecretKeys.TOKEN),
            intents=hikari.Intents.ALL,
            suppress_optimization_warning=True,
            banner=None,
        )

        client = lightbulb.client_from_app(
            bot, localization_provider=Localization.serialize(), hooks=[add_or_update_user]
        )

        GlobalState.bot.set_bot(bot)
        GlobalState.bot.set_client(client)

        @client.error_handler
        async def handler(exc: lightbulb.exceptions.ExecutionPipelineFailedException) -> bool:
            from datetime import timedelta

            from helper import MessageHelper, TimeHelper
            from model import MessageKeys

            if isinstance(exc.causes[0], EmptyException):
                return True
            elif isinstance(exc.causes[0], CommandExecutionError):
                await exc.context.respond(
                    MessageHelper(
                        key=MessageKeys.error.COMMAND_EXECUTION,
                        locale=exc.context.interaction.locale,
                        error_message=exc.causes[0],
                    ).decode(),
                    ephemeral=True,
                )
                return True
            elif isinstance(exc.causes[0], lightbulb.prefab.OnCooldown):
                await exc.context.respond(
                    MessageHelper(
                        key=MessageKeys.error.COMMAND_ON_COOLDOWN,
                        locale=exc.context.interaction.locale,
                        remaining_cooldown=TimeHelper(
                            exc.context.interaction.locale
                        ).from_timedelta(timedelta(seconds=exc.causes[0].remaining)),
                    ).decode(),
                    ephemeral=True,
                )
                return True
            else:
                await exc.context.respond(
                    MessageHelper(
                        key=MessageKeys.error.UNKNOWN, locale=exc.context.interaction.locale
                    ).decode(),
                    ephemeral=True,
                )
                logger.error(exc.causes[0], exc_info=True)
                return True

        @bot.listen(hikari.StartingEvent)
        async def on_starting(_: hikari.StartingEvent) -> None:
            logger.info("Starting bot")
            await initialize_database()

            # Import extensions and events
            import events
            import extensions

            # Import helper for wiki data loading
            # Import helper for getting command data
            from helper import CommandHelper, WikiHelper

            WikiHelper.load_wiki_data()

            # Import menu for suggest command
            if CommandHelper(CommandsKeys.SUGGEST).command_enabled:
                from components.menus.suggest import SuggestConfirmMenu

                menu = SuggestConfirmMenu()

                menu.attach_persistent(client, timeout=None)

            # Inıtialize ticket system if enabled
            from helper.ticket import TicketHelper

            await TicketHelper.initialize()

            # Load extensions and events
            await client.load_extensions_from_package(events, recursive=True)
            await client.load_extensions_from_package(extensions, recursive=True)
            await client.start()
            await websocket.start()

        @bot.listen(hikari.StoppingEvent)
        async def on_stopping(_: hikari.StoppingEvent) -> None:
            logger.info("Stopping bot")
            await websocket.stop()
            await client.stop()
            await close_database()

        # Prepare status
        status_value = Settings.get(BotKeys.STATUS)
        status = (
            getattr(hikari.Status, status_value)
            if status_value is not None
            else hikari.Status.ONLINE
        )

        # Prepare activity
        activity = None
        name = Settings.get(BotKeys.NAME)
        if name is not None:
            activity_args = {"name": name}

            # Add optional parameters
            state = Settings.get(BotKeys.STATE)
            if state is not None:
                activity_args["state"] = state

            url = Settings.get(BotKeys.URL)
            if url is not None:
                activity_args["url"] = url

            type_value = Settings.get(BotKeys.TYPE)
            if type_value is not None:
                activity_args["type"] = getattr(hikari.ActivityType, type_value)

            activity = hikari.Activity(**activity_args)

        bot.run(
            status=status,
            activity=activity,
        )
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        sys.exit(1)
