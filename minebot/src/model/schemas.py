from datetime import datetime

import hikari
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    PositiveInt,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_extra_types.color import Color


# ==== Shared Base Models ====
class DescriptiveElement(BaseModel):
    """Base model for labeled descriptive elements."""

    label: str
    description: str


# ==== Message Schema ====
class TextMessage(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class EmbedFieldData(BaseModel):
    name: str = Field(..., max_length=256)
    value: str = Field(..., max_length=1024)
    inline: bool = Field(default=False)


class EmbedFooterData(BaseModel):
    text: str = Field(..., max_length=2048)
    icon: HttpUrl | None = None


class EmbedAuthorData(BaseModel):
    name: str | None = Field(default=None, max_length=256)
    url: HttpUrl | None = None
    icon: HttpUrl | None = None


class DiscordEmbed(BaseModel):
    title: str | None = Field(default=None, max_length=256)
    description: str | None = Field(default=None, max_length=4096)
    url: HttpUrl | None = None
    color: Color | None = None
    timestamp: datetime | None = None
    fields: list[EmbedFieldData] | None = None
    footer: EmbedFooterData | None = None
    image: HttpUrl | None = None
    thumbnail: HttpUrl | None = None
    author: EmbedAuthorData | None = None

    @field_validator("fields", mode="before")
    @classmethod
    def ensure_fields_are_list(
        cls, v: list[EmbedFieldData] | EmbedFieldData
    ) -> list[EmbedFieldData]:
        return [v] if isinstance(v, EmbedFieldData) else v

    @model_validator(mode="after")
    def validate_title_or_description(self) -> "DiscordEmbed":
        if not self.title and not self.description:
            raise ValueError("Either title or description must be provided.")
        return self


class DiscordMessage(BaseModel):
    message_type: str = Field(..., pattern=r"^(?i)(plain|embed)$")
    content: TextMessage | DiscordEmbed

    @field_validator("message_type", mode="after")
    @classmethod
    def lowercase_message_type(cls, v: str) -> str:
        return v.lower()

    @field_validator("content")
    @classmethod
    def validate_content_by_type(
        cls, v: TextMessage | DiscordEmbed, info: ValidationInfo
    ) -> TextMessage | DiscordEmbed:
        expected = TextMessage if info.data.get("message_type") == "plain" else DiscordEmbed
        if not isinstance(v, expected):
            raise ValueError(
                f"Content must be of type {expected.__name__} for message_type '{info.data.get('message_type')}'."
            )
        return v


class StatusMessagePair(BaseModel):
    """Model for success/failure message pairs."""

    success: DiscordMessage
    failure: DiscordMessage


# ==== Menu Schema =====
class ButtonBase(BaseModel):
    label: str | None = Field(..., max_length=80)
    emoji: str | None = Field(default=None, max_length=1)
    disabled: bool = False

    @model_validator(mode="after")
    def validate_label_nor_emoji(self) -> "ButtonBase":
        if not self.label and not self.emoji:
            raise ValueError("Either label or emoji must be provided.")
        return self


class SelectBase(BaseModel):
    placeholder: str | None = Field(default=None, max_length=150)
    disabled: bool | None = False


class ActionButton(ButtonBase):
    style: str = Field(..., pattern=r"^(?i)(PRIMARY|SECONDARY|SUCCESS|DANGER)$")

    @field_validator("style", mode="after")
    @classmethod
    def uppercase_style(cls, v: str) -> str:
        return v.upper()


class HyperlinkButton(ButtonBase):
    url: HttpUrl


# ==== Modal Schema ====
class ModalBase(BaseModel):
    title: str = Field(..., max_length=80)


class TextInputField(BaseModel):
    style: str = Field(..., pattern=r"^(?i)(SHORT|PARAGRAPH)$")
    label: str = Field(..., max_length=80)
    placeholder: str | None = Field(default=None, max_length=150)
    value: str | None = Field(default=None, max_length=4000)

    @field_validator("style", mode="after")
    @classmethod
    def uppercase_style(cls, v: str) -> str:
        return v.upper()


# ==== Reward Schema =====
class UserReward(BaseModel):
    mode: str = Field(..., pattern=r"^(?i)(ROLE|ITEM|BOTH)$")
    role: PositiveInt | list[PositiveInt] | None = None
    item: dict[str, str | list[str]] | None = None

    @field_validator("mode", mode="after")
    @classmethod
    def uppercase_mode(cls, v: str) -> str:
        return v.upper()

    @field_validator("role", mode="before")
    @classmethod
    def ensure_role_id_is_list(cls, v: PositiveInt | list[PositiveInt]) -> list[PositiveInt]:
        return [v] if isinstance(v, int) else v

    @field_validator("item", mode="before")
    @classmethod
    def ensure_command_is_list(cls, v: str | list[str]) -> list[str]:
        return [v] if isinstance(v, str) else v

    @model_validator(mode="after")
    def validate_reward(self) -> "UserReward":
        if self.mode == "ROLE" and not self.role:
            raise ValueError("Role reward must be provided when mode is 'ROLE'.")
        elif self.mode == "ITEM" and not self.item:
            raise ValueError("Item reward must be provided when mode is 'ITEM'.")
        elif self.mode == "BOTH" and (not self.role or not self.item):
            raise ValueError("Both role and item rewards must be provided when mode is 'BOTH'.")
        return self


# ==== Synchronization Schema ====
class MinecraftSynchronization(BaseModel):
    minecraft_to_discord: bool = False
    discord_to_minecraft: bool = False


# ==== Settings Schema ====
class BotCredentials(BaseModel):
    token: str
    default_guild: PositiveInt

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Token cannot be empty or whitespace")
        return v


class BotActivity(BaseModel):
    name: str
    state: str | None = None
    url: str | None = Field(
        default=None,
        pattern=r"^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$",
    )
    type: str = Field(
        default="PLAYING",
        pattern=r"^(?i)(PLAYING|STREAMING|LISTENING|WATCHING|COMPETING)$",
    )

    @field_validator("type", mode="after")
    @classmethod
    def uppercase_type(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode="after")
    def validate_streaming_url(self) -> "BotActivity":
        is_streaming = self.type.upper() == "STREAMING"
        has_url = self.url is not None
        if is_streaming and not has_url:
            raise ValueError("URL must be provided if type is 'STREAMING'")
        elif has_url and not is_streaming:
            raise ValueError("URL must be None if type is not 'STREAMING'")
        return self


class BotConfiguration(BaseModel):
    status: str | None = Field(default=None, pattern=r"^(?i)(ONLINE|IDLE|DO_NOT_DISTURB|OFFLINE)$")
    activity: BotActivity

    @field_validator("status", mode="after")
    @classmethod
    def uppercase_status(cls, v: str | None) -> str | None:
        if v is not None:
            return v.upper()
        return v


class DatabaseConnection(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        import re

        if not v.strip():
            raise ValueError("Database URL cannot be empty or whitespace")

        patterns = {
            "sqlite+aiosqlite://": r"sqlite\+aiosqlite:///.*",
            "mysql+aiomysql://": r"mysql\+aiomysql://[^:]+:.*@[^:]+:[0-9]+/[^/]+",
            "postgresql+asyncpg://": r"postgresql\+asyncpg://[^:]+:.*@[^:]+:[0-9]+/[^/]+",
        }

        for prefix, pattern in patterns.items():
            if v.startswith(prefix) and re.match(pattern, v):
                return v

        raise ValueError(
            "Invalid database URL format. Supported formats: sqlite+aiosqlite:///, mysql+aiomysql://, postgresql+asyncpg://"
        )


class WebSocketAuthentication(BaseModel):
    allowed_ip: str = "127.0.0.1"
    password: str = Field(default="MineAcademy", min_length=8)


class WebSocketConfig(BaseModel):
    host: str = "localhost"
    port: PositiveInt = Field(default=8080, ge=1, le=65535)
    auth: WebSocketAuthentication


class ServerConfiguration(BaseModel):
    websocket: WebSocketConfig


class BasicEvent(BaseModel):
    log: PositiveInt | None = None


class GuildBoostEvent(BasicEvent):
    reward: UserReward | None = None


class EventConfiguration(BaseModel):
    guild_boost: GuildBoostEvent | None = None


class CommandCooldown(BaseModel):
    algorithm: str = Field(..., pattern=r"^(?i)(fixed_window|sliding_window)$")
    bucket: str = Field(..., pattern=r"^(?i)(global|user|channel|guild)$")
    window_length: PositiveInt
    allowed_invocations: PositiveInt

    @field_validator("algorithm", "bucket", mode="after")
    @classmethod
    def lowercase_algorithm_and_bucket(cls, v: str) -> str:
        return v.lower()


class BasicCommand(BaseModel):
    permissions: list[str] = Field(default=["NONE"])
    cooldown: CommandCooldown | None = None

    @model_validator(mode="after")
    def validate_permissions(self) -> "BasicCommand":
        if isinstance(self.permissions, list):
            valid = hikari.Permissions.__members__
            for perm in self.permissions:
                if perm not in valid and perm != "NONE":
                    raise ValueError(f"Invalid permission: {perm}. Valid: {', '.join(valid)}")
        return self


class LoggedCommandConfig(BasicCommand):
    log: PositiveInt | None = None


class RewardableCommandConfig(BasicCommand):
    reward: UserReward | None = None


class TransferableCommandConfig(BasicCommand):
    synchronization: MinecraftSynchronization | None = None


class LoggedRewardableCommandConfig(RewardableCommandConfig, LoggedCommandConfig):
    pass


class LoggedTransferableCommandConfig(TransferableCommandConfig, LoggedCommandConfig):
    pass


class LoggedRewardableTransferableCommandConfig(
    LoggedCommandConfig, RewardableCommandConfig, TransferableCommandConfig
):
    pass


class RewardableTransferableCommandConfig(RewardableCommandConfig, TransferableCommandConfig):
    pass


class SuggestCommandConfig(RewardableCommandConfig):
    pending_channel: PositiveInt
    result_channel: PositiveInt


class CommandConfiguration(BaseModel):
    link_account: LoggedRewardableCommandConfig | None = None
    withdraw_rewards: LoggedCommandConfig | None = None
    kick: LoggedTransferableCommandConfig | None = None
    ban: LoggedTransferableCommandConfig | None = None
    unban: LoggedTransferableCommandConfig | None = None
    timeout: LoggedTransferableCommandConfig | None = None
    untimeout: LoggedTransferableCommandConfig | None = None
    clear: LoggedCommandConfig | None = None
    lock: LoggedCommandConfig | None = None
    unlock: LoggedCommandConfig | None = None
    slowmode: LoggedCommandConfig | None = None
    suggest: SuggestCommandConfig | None = None
    wiki: BasicCommand | None = None


# ==== Ticket System Schema ====
class BasicTicketCategory(BaseModel):
    category_button_style: str | None = Field(
        default=None, pattern=r"^(?i)(PRIMARY|SECONDARY|SUCCESS|DANGER)$"
    )
    category_emoji: str | None = Field(default=None, max_length=1)
    category_name: str = Field(..., max_length=100)
    category_description: str | None = Field(default=None, max_length=100)
    channel_format: str = Field(
        ..., min_length=1, max_length=100, pattern=r"^(?:[a-zA-Z0-9_-]|\{[a-zA-Z0-9_-]+\})+$"
    )
    staff_role: PositiveInt

    @model_validator(mode="after")
    def validate_description_or_button_style(self) -> "BasicTicketCategory":
        if self.category_description and self.category_button_style:
            raise ValueError(
                "Only one of category_description or category_button_style can be provided, not both."
            )
        return self


class ThreadTicketCategory(BasicTicketCategory):
    channel_id: PositiveInt


class ChannelTicketCategory(BasicTicketCategory):
    category_id: PositiveInt


class TicketCreation(BaseModel):
    channel_id: PositiveInt
    max_tickets_per_user: PositiveInt


class BasicTicketTranscription(BaseModel):
    file_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r"^(?:[a-zA-Z0-9_-]|\{[a-zA-Z0-9_-]+\})+\.(txt|html)$",
    )


class ChannelTicketTranscription(BaseModel):
    channel_id: PositiveInt


class GithubTicketTranscription(BaseModel):
    token: str
    repository: str
    branch: str


class TicketTranscription(BasicTicketTranscription):
    upload: ChannelTicketTranscription | GithubTicketTranscription | None = None


class TicketSystem(BaseModel):
    categories: dict[str, ThreadTicketCategory | ChannelTicketCategory] = Field(
        min_length=1, max_length=25
    )
    creation: TicketCreation
    transcript: TicketTranscription | None = None
    log: PositiveInt

    @field_validator("categories", mode="after")
    @classmethod
    def validate_categories(
        cls, v: dict[str, ThreadTicketCategory | ChannelTicketCategory]
    ) -> dict[str, ThreadTicketCategory | ChannelTicketCategory]:
        # Check if first category uses a button style
        first_category = next(iter(v.values()))
        has_button_style = first_category.category_button_style is not None

        # Get the type of the first category
        first_category_type = type(first_category)

        # Ensure all categories consistently use or don't use button styles
        # and are of the same type
        for category_name, category_info in v.items():
            current_has_button = category_info.category_button_style is not None
            if current_has_button != has_button_style:
                raise ValueError(
                    "Either all categories must use a button style, or none of them should."
                )

            # Check if all categories are of the same type
            if not isinstance(category_info, first_category_type):
                raise ValueError(
                    f"All categories must be of the same type. Expected {first_category_type.__name__}, but got {type(category_info).__name__} for category '{category_name}'."
                )

        return v


class SystemConfiguration(BaseModel):
    ticket: TicketSystem | None = None


class BotSettings(BaseModel):
    secret: BotCredentials
    database: DatabaseConnection
    bot: BotConfiguration | None = None
    server: ServerConfiguration | None = None
    events: EventConfiguration | None = None
    commands: CommandConfiguration | None = None
    systems: SystemConfiguration | None = None


# ==== Localization Schema ====
class GuildBoostMessages(BaseModel):
    class Log(BaseModel):
        success: DiscordMessage

    log: Log


class GuildBoostLocalization(BaseModel):
    messages: GuildBoostMessages


class EventLocalization(BaseModel):
    guild_boost: GuildBoostLocalization


class LinkAccountParameters(BaseModel):
    username: DescriptiveElement


class LinkAccountCommandInfo(DescriptiveElement):
    options: LinkAccountParameters


class LinkAccountMessages(BaseModel):
    class Minecraft(BaseModel):
        confirmation_code: TextMessage
        success: TextMessage
        failure: TextMessage

    minecraft: Minecraft
    user: StatusMessagePair
    log: StatusMessagePair


class LinkAccountConfirmationFields(BaseModel):
    code: TextInputField


class LinkAccountConfirmationModal(ModalBase):
    fields: LinkAccountConfirmationFields


class LinkAccountModals(BaseModel):
    confirmation: LinkAccountConfirmationModal


class LinkAccountLocalization(BaseModel):
    command: LinkAccountCommandInfo
    messages: LinkAccountMessages
    modal: LinkAccountModals


class WithdrawRewardsMessages(BaseModel):
    user: StatusMessagePair
    log: StatusMessagePair


class WithdrawRewardsLocalization(BaseModel):
    command: DescriptiveElement
    messages: WithdrawRewardsMessages


class KickParameters(BaseModel):
    user: DescriptiveElement
    reason: DescriptiveElement


class KickCommandParameters(DescriptiveElement):
    options: KickParameters


class KickMessages(BaseModel):
    class SuccessMessage(BaseModel):
        success: DiscordMessage

    user: SuccessMessage
    log: SuccessMessage


class KickLocalization(BaseModel):
    command: KickCommandParameters
    messages: KickMessages


class BanParameters(BaseModel):
    user: DescriptiveElement
    duration: DescriptiveElement
    reason: DescriptiveElement


class BanCommandParameters(DescriptiveElement):
    options: BanParameters


class BanMessages(BaseModel):
    class SuccessMessage(BaseModel):
        success: DiscordMessage

    user: SuccessMessage
    log: SuccessMessage


class BanLocalization(BaseModel):
    command: BanCommandParameters
    messages: BanMessages


class UnBanParameters(BaseModel):
    user: DescriptiveElement
    reason: DescriptiveElement


class UnBanCommandParameters(DescriptiveElement):
    options: UnBanParameters


class UnBanMessages(BaseModel):
    class SuccessMessage(BaseModel):
        success: DiscordMessage

    user: SuccessMessage
    log: SuccessMessage


class UnBanLocalization(BaseModel):
    command: UnBanCommandParameters
    messages: UnBanMessages


class TimeoutParameters(BaseModel):
    user: DescriptiveElement
    duration: DescriptiveElement
    reason: DescriptiveElement


class TimeoutCommandParameters(DescriptiveElement):
    options: TimeoutParameters


class TimeoutMessages(BaseModel):
    class SuccessMessage(BaseModel):
        success: DiscordMessage

    user: SuccessMessage
    log: SuccessMessage


class TimeoutLocalization(BaseModel):
    command: TimeoutCommandParameters
    messages: TimeoutMessages


class UnTimeoutParameters(BaseModel):
    user: DescriptiveElement
    reason: DescriptiveElement


class UnTimeoutCommandParameters(DescriptiveElement):
    options: UnTimeoutParameters


class UnTimeoutMessages(BaseModel):
    class SuccessMessage(BaseModel):
        success: DiscordMessage

    user: SuccessMessage
    log: SuccessMessage


class UnTimeoutLocalization(BaseModel):
    command: UnTimeoutCommandParameters
    messages: UnTimeoutMessages


class ClearParamters(BaseModel):
    amount: DescriptiveElement
    reason: DescriptiveElement


class ClearCommandParameters(DescriptiveElement):
    options: ClearParamters


class ClearMessages(BaseModel):
    class SuccessMessage(BaseModel):
        success: DiscordMessage

    user: SuccessMessage
    log: SuccessMessage


class ClearLocalization(BaseModel):
    command: ClearCommandParameters
    messages: ClearMessages


class LockParameters(BaseModel):
    channel: DescriptiveElement
    reason: DescriptiveElement


class LockCommandParameters(DescriptiveElement):
    options: LockParameters


class LockMessages(BaseModel):
    class SuccessMessage(BaseModel):
        success: DiscordMessage

    user: SuccessMessage
    log: SuccessMessage


class LockLocalization(BaseModel):
    command: LockCommandParameters
    messages: LockMessages


class UnlockParameters(BaseModel):
    channel: DescriptiveElement
    reason: DescriptiveElement


class UnlockCommandParameters(DescriptiveElement):
    options: UnlockParameters


class UnlockMessages(BaseModel):
    class SuccessMessage(BaseModel):
        success: DiscordMessage

    user: SuccessMessage
    log: SuccessMessage


class UnlockLocalization(BaseModel):
    command: UnlockCommandParameters
    messages: UnlockMessages


class SlowmodeParameters(BaseModel):
    channel: DescriptiveElement
    duration: DescriptiveElement
    reason: DescriptiveElement


class SlowmodeCommandParameters(DescriptiveElement):
    options: SlowmodeParameters


class SlowmodeMessages(BaseModel):
    class SuccessMessage(BaseModel):
        success: DiscordMessage

    user: SuccessMessage
    log: SuccessMessage


class SlowmodeLocalization(BaseModel):
    command: SlowmodeCommandParameters
    messages: SlowmodeMessages


class SuggestMessages(BaseModel):
    class Minecraft(BaseModel):
        approve: TextMessage
        reject: TextMessage

    class Result(BaseModel):
        approve: DiscordMessage
        reject: DiscordMessage

    minecraft: Minecraft
    user: StatusMessagePair
    pending: StatusMessagePair
    result: Result


class SuggestConfirmationButtons(BaseModel):
    approve: ActionButton
    reject: ActionButton


class SuggestMenus(BaseModel):
    confirmation: SuggestConfirmationButtons


class SuggestSendModalFields(BaseModel):
    suggestion: TextInputField


class SuggestSendModal(ModalBase):
    fields: SuggestSendModalFields


class SuggestRespondModalFields(BaseModel):
    response: TextInputField


class SuggestRespondModal(ModalBase):
    fields: SuggestRespondModalFields


class SuggestModals(BaseModel):
    send: SuggestSendModal
    respond: SuggestRespondModal


class SuggestLocalization(BaseModel):
    command: DescriptiveElement
    messages: SuggestMessages
    menu: SuggestMenus
    modal: SuggestModals


class WikiParameters(BaseModel):
    query: DescriptiveElement


class WikiCommandParameters(DescriptiveElement):
    options: WikiParameters


class WikiMessages(BaseModel):
    user: StatusMessagePair


class WikiLocalization(BaseModel):
    command: WikiCommandParameters
    messages: WikiMessages


class CommandLocalization(BaseModel):
    link_account: LinkAccountLocalization
    withdraw_rewards: WithdrawRewardsLocalization
    kick: KickLocalization
    ban: BanLocalization
    unban: UnBanLocalization
    timeout: TimeoutLocalization
    untimeout: UnTimeoutLocalization
    clear: ClearLocalization
    lock: LockLocalization
    unlock: UnlockLocalization
    slowmode: SlowmodeLocalization
    suggest: SuggestLocalization
    wiki: WikiLocalization


class TicketMessages(BaseModel):
    class System(BaseModel):
        startup: DiscordMessage
        creation: dict[str, DiscordMessage]
        closing: DiscordMessage

    class Log(BaseModel):
        transcript: DiscordMessage

    system: System
    user: StatusMessagePair
    log: Log


class TicketInnerMenu(BaseModel):
    close: ActionButton


class TicketOuterMenu(BaseModel):
    confirm: ActionButton
    cancel: ActionButton


class TicketMenu(BaseModel):
    inner: TicketInnerMenu
    outer: TicketOuterMenu


class BasicTicketModal(ModalBase):
    fields: dict[str, TextInputField] = Field(min_length=1, max_length=5)


class TicketLocalization(BaseModel):
    messages: TicketMessages
    menu: TicketMenu
    modal: dict[str, BasicTicketModal] = Field(min_length=1, max_length=25)


class SystemLocalization(BaseModel):
    ticket: TicketLocalization | None = None


class GeneralLocalization(BaseModel):
    success: DiscordMessage
    failure: DiscordMessage
    no_reason: TextMessage


class ErrorLocalization(BaseModel):
    unknown_error: DiscordMessage
    timeout_error: DiscordMessage
    command_on_cooldown: DiscordMessage
    user_not_found: DiscordMessage
    member_not_found: DiscordMessage
    channel_not_found: DiscordMessage
    command_execution_error: DiscordMessage
    user_record_not_found: DiscordMessage
    account_already_linked: DiscordMessage
    account_not_linked: DiscordMessage
    player_not_online: DiscordMessage
    can_not_moderate: DiscordMessage
    user_already_timed_out: DiscordMessage
    user_not_timed_out: DiscordMessage
    duration_out_of_range: DiscordMessage
    max_amount_of_tickets_reached: DiscordMessage


class TimeUnitsLocalization(BaseModel):
    class BasicUnit(BaseModel):
        singular: str | list[str]
        plural: str | list[str]

        @field_validator("singular", "plural", mode="before")
        @classmethod
        def ensure_as_list(cls, v: str | list[str]) -> list[str]:
            return [v] if isinstance(v, str) else v

    year: BasicUnit
    month: BasicUnit
    week: BasicUnit
    day: BasicUnit
    hour: BasicUnit
    minute: BasicUnit
    second: BasicUnit


class LocalizationData(BaseModel):
    locale: str
    events: EventLocalization
    commands: CommandLocalization
    systems: SystemLocalization
    general: GeneralLocalization
    error: ErrorLocalization
    time_units: TimeUnitsLocalization
