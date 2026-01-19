import lightbulb

from database.schemas import UserSchema
from database.services import UserService
from exceptions.utility import EmptyException


async def _retrieve_user_and_validate_minecraft_status(
    ctx: lightbulb.Context, link_status_requirement: bool | None = None
) -> UserSchema:
    """
    Retrieve user record and validate their Minecraft account link status.

    This helper function fetches a user from the database and validates their
    Minecraft account connection according to the specified requirements.

    Args:
        ctx: The command context containing user information
        link_status_requirement: Validation requirement for Minecraft link:
            - True: User must have a linked Minecraft account
            - False: User must NOT have a linked Minecraft account
            - None: No validation of link status is performed

    Returns:
        UserSchema: The validated user database record

    Raises:
        EmptyException: If user not found or link status requirement not met
    """
    from helper import MessageHelper
    from model import MessageKeys

    # Retrieve user from database
    user_record: UserSchema | None = await UserService.get_user(ctx.user.id)

    # Validate user exists
    if not user_record:
        await MessageHelper(
            key=MessageKeys.error.USER_RECORD_NOT_FOUND,
            locale=ctx.interaction.locale,
            discord_username=ctx.user.username,
            discord_user_id=ctx.user.id,
            discord_user_mention=ctx.user.mention,
        ).send_response(ctx, ephemeral=True)
        raise EmptyException

    # Extract Minecraft UUID for validation
    minecraft_uuid: str | None = user_record.minecraft_uuid

    # Validate link status based on requirement
    if link_status_requirement is True and not minecraft_uuid:
        await MessageHelper(
            key=MessageKeys.error.ACCOUNT_NOT_LINKED,
            locale=ctx.interaction.locale,
            discord_username=ctx.user.username,
            discord_user_id=ctx.user.id,
            discord_user_mention=ctx.user.mention,
        ).send_response(ctx, ephemeral=True)
        raise EmptyException
    elif link_status_requirement is False and minecraft_uuid:
        await MessageHelper(
            key=MessageKeys.error.ACCOUNT_ALREADY_LINKED,
            locale=ctx.interaction.locale,
            discord_username=ctx.user.username,
            discord_user_id=ctx.user.id,
            discord_user_mention=ctx.user.mention,
            minecraft_username=user_record.minecraft_username,
            minecraft_uuid=user_record.minecraft_uuid,
        ).send_response(ctx, ephemeral=True)
        raise EmptyException

    return user_record


def verify_minecraft_account_link(link_required: bool = True) -> lightbulb.ExecutionHook:
    """
    Create a command hook that verifies Minecraft account link status.

    This function returns a hook that checks if the user has a Minecraft account
    linked according to the specified requirement.

    Args:
        link_required: If True, requires a linked account; if False, requires no linked account

    Returns:
        lightbulb.ExecutionHook: Hook that performs the verification
    """

    @lightbulb.hook(lightbulb.ExecutionSteps.CHECKS)
    async def _inner(pipeline: lightbulb.ExecutionPipeline, ctx: lightbulb.Context) -> None:
        await _retrieve_user_and_validate_minecraft_status(ctx, link_required)

    return _inner


@lightbulb.hook(lightbulb.ExecutionSteps.CHECKS)
async def require_minecraft_player_online(
    pipeline: lightbulb.ExecutionPipeline, ctx: lightbulb.Context
) -> None:
    """
    Command hook that verifies the user is currently online in Minecraft.

    This hook checks that:
    1. The user has a linked Minecraft account
    2. The player is currently online on the Minecraft server

    Args:
        pipeline: The command execution pipeline
        ctx: The command context containing user information

    Raises:
        EmptyException: If user isn't linked or isn't online in Minecraft
    """
    from helper import MessageHelper, MinecraftHelper
    from model import MessageKeys

    # First verify user exists and has a linked account
    user_record: UserSchema = await _retrieve_user_and_validate_minecraft_status(
        ctx, link_status_requirement=True
    )

    # Check if player is online in Minecraft
    is_online: bool = await MinecraftHelper.fetch_player_status(uuid=user_record.minecraft_uuid)  # type: ignore

    if not is_online:
        await MessageHelper(
            key=MessageKeys.error.PLAYER_NOT_ONLINE,
            locale=ctx.interaction.locale,
            discord_username=ctx.user.username,
            discord_user_id=ctx.user.id,
            discord_user_mention=ctx.user.mention,
            minecraft_username=user_record.minecraft_username,
            minecraft_uuid=user_record.minecraft_uuid,
        ).send_response(ctx, ephemeral=True)
        raise EmptyException
