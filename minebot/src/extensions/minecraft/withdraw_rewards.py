import hikari
import lightbulb

from database.schemas import UserSchema
from database.services import UserService
from helper import CommandHelper, MessageHelper, MinecraftHelper
from hooks.minecraft import verify_minecraft_account_link
from model import CommandsKeys, MessageKeys

# Helper that manages command configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.WITHDRAW_REWARDS)
loader: lightbulb.Loader = helper.get_loader()


@loader.command
class WithdrawRewards(
    lightbulb.SlashCommand,
    name="extensions.withdraw_rewards.label",
    description="extensions.withdraw_rewards.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(verify_minecraft_account_link()),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        # Prepare default parameters with Discord user information
        default_params: dict[str, str] = {
            "discord_user_id": str(ctx.user.id),
            "discord_username": ctx.user.username,
            "discord_user_mention": ctx.user.mention,
        }

        # Attempt to give rewards to the user's Minecraft account
        if await MinecraftHelper.give_rewards(user_id=ctx.user.id):
            # Rewards were successfully given - retrieve user's Minecraft data
            user_data: UserSchema = await UserService.get_user(ctx.user.id)  # type: ignore

            # Prepare Minecraft parameters with account information
            minecraft_params: dict[str, str | None] = {
                "minecraft_username": user_data.minecraft_username,
                "minecraft_uuid": user_data.minecraft_uuid,
            }

            # Send success message to the user
            await MessageHelper(
                MessageKeys.commands.WITHDRAW_REWARDS_USER_SUCCESS,
                locale=ctx.interaction.locale,
                **default_params,
                **minecraft_params,
            ).send_response(ctx, ephemeral=True)
            # Log successful reward withdrawal in log channel
            await MessageHelper(
                MessageKeys.commands.WITHDRAW_REWARDS_LOG_SUCCESS,
                **default_params,
                **minecraft_params,
            ).send_to_log_channel(helper)
        else:
            # Rewards could not be given - notify user of failure
            await MessageHelper(
                MessageKeys.commands.WITHDRAW_REWARDS_USER_FAILURE, **default_params
            ).send_response(ctx, ephemeral=True)
            # Log failed reward withdrawal attempt in log channel
            await MessageHelper(
                MessageKeys.commands.WITHDRAW_REWARDS_LOG_FAILURE, **default_params
            ).send_to_log_channel(helper)
