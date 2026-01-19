import lightbulb

from database.schemas import UserSchema
from database.services import UserService


@lightbulb.hook(lightbulb.ExecutionSteps.CHECKS)
async def add_or_update_user(_: lightbulb.ExecutionPipeline, ctx: lightbulb.Context) -> None:
    await UserService.create_or_update_user(
        UserSchema(id=ctx.user.id, locale=ctx.interaction.locale)
    )
