from pathlib import Path

import hikari
import lightbulb

from helper import CommandHelper, MessageHelper, WikiHelper
from model import CommandsKeys, MessageKeys

# Helper that manages command configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.WIKI)
loader: lightbulb.Loader = helper.get_loader()


async def autocomplete_callback(ctx: lightbulb.AutocompleteContext[str]) -> None:
    # Get the current input from the user and convert to lowercase for case-insensitive matching
    current_value = ctx.focused.value.lower() if isinstance(ctx.focused.value, str) else ""

    # Fetch wiki data specific to the user's locale/language
    wiki_data = WikiHelper.get_wiki_files(ctx.interaction.locale)

    if wiki_data is not None:
        values_to_recommend = []

        # Iterate through available wiki entries and filter based on user input
        for key in wiki_data.keys():
            # Check if current user input is a substring of any wiki entry (case-insensitive)
            if current_value in key.lower():
                values_to_recommend.append(key)
                # Limit results to 25 entries to prevent overwhelming the UI
                if len(values_to_recommend) >= 25:
                    break

        # Return the filtered wiki entries as autocomplete suggestions
        await ctx.respond(values_to_recommend)


@loader.command
class Wiki(
    lightbulb.SlashCommand,
    name="extensions.wiki.label",
    description="extensions.wiki.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    # Define the query parameter that users will provide
    query: str = lightbulb.string(
        "extensions.wiki.options.query.label",
        "extensions.wiki.options.query.description",
        autocomplete=autocomplete_callback,
        localize=True,
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        # Get the user's locale for localized responses
        user_locale: str = ctx.interaction.locale

        # Get wiki files available for the user's locale
        wiki_data: dict[str, Path] | None = WikiHelper.get_wiki_files(user_locale)

        # Check if the requested wiki entry exists
        if not wiki_data or self.query not in wiki_data.keys():
            # Send failure message if wiki entry not found
            await MessageHelper(
                MessageKeys.commands.WIKI_USER_FAILURE,
                locale=user_locale,
            ).send_response(ctx, ephemeral=True)
            return

        # Retrieve the content of the requested wiki entry
        content: str | None = WikiHelper.get_wiki_file_content(user_locale, self.query)

        # Send successful response with wiki content to the user
        await MessageHelper(
            MessageKeys.commands.WIKI_USER_SUCCESS,
            locale=user_locale,
            query=self.query,
            result=content,
        ).send_response(ctx, ephemeral=True)
