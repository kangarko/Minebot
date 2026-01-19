from enum import Enum


class EventMessageKeys(Enum):
    """Event message keys for the bot"""

    GUILD_BOOST_LOG_SUCCESS = "events.guild_boost.messages.log.success"


class CommandMessageKeys(Enum):
    """Command message keys for the bot"""

    LINK_ACCOUNT_MINECRAFT_CONFIRMATION_CODE = (
        "commands.link_account.messages.minecraft.confirmation_code"
    )
    LINK_ACCOUNT_MINECRAFT_SUCCESS = "commands.link_account.messages.minecraft.success"
    LINK_ACCOUNT_MINECRAFT_FAILURE = "commands.link_account.messages.minecraft.failure"
    LINK_ACCOUNT_USER_SUCCESS = "commands.link_account.messages.user.success"
    LINK_ACCOUNT_USER_FAILURE = "commands.link_account.messages.user.failure"
    LINK_ACCOUNT_LOG_SUCCESS = "commands.link_account.messages.log.success"
    LINK_ACCOUNT_LOG_FAILURE = "commands.link_account.messages.log.failure"

    WITHDRAW_REWARDS_USER_SUCCESS = "commands.withdraw_rewards.messages.user.success"
    WITHDRAW_REWARDS_USER_FAILURE = "commands.withdraw_rewards.messages.user.failure"
    WITHDRAW_REWARDS_LOG_SUCCESS = "commands.withdraw_rewards.messages.log.success"
    WITHDRAW_REWARDS_LOG_FAILURE = "commands.withdraw_rewards.messages.log.failure"

    KICK_USER_SUCCESS = "commands.kick.messages.user.success"
    KICK_LOG_SUCCESS = "commands.kick.messages.log.success"

    BAN_USER_SUCCESS = "commands.ban.messages.user.success"
    BAN_LOG_SUCCESS = "commands.ban.messages.log.success"

    UNBAN_USER_SUCCESS = "commands.unban.messages.user.success"
    UNBAN_LOG_SUCCESS = "commands.unban.messages.log.success"

    TIMEOUT_USER_SUCCESS = "commands.timeout.messages.user.success"
    TIMEOUT_LOG_SUCCESS = "commands.timeout.messages.log.success"

    UNTIMEOUT_USER_SUCCESS = "commands.untimeout.messages.user.success"
    UNTIMEOUT_LOG_SUCCESS = "commands.untimeout.messages.log.success"

    CLEAR_USER_SUCCESS = "commands.clear.messages.user.success"
    CLEAR_LOG_SUCCESS = "commands.clear.messages.log.success"

    LOCK_USER_SUCCESS = "commands.lock.messages.user.success"
    LOCK_LOG_SUCCESS = "commands.lock.messages.log.success"

    UNLOCK_USER_SUCCESS = "commands.unlock.messages.user.success"
    UNLOCK_LOG_SUCCESS = "commands.unlock.messages.log.success"

    SLOWMODE_USER_SUCCESS = "commands.slowmode.messages.user.success"
    SLOWMODE_LOG_SUCCESS = "commands.slowmode.messages.log.success"

    SUGGEST_MINECRAFT_APPROVE = "commands.suggest.messages.minecraft.approve"
    SUGGEST_MINECRAFT_REJECT = "commands.suggest.messages.minecraft.reject"
    SUGGEST_USER_SUCCESS = "commands.suggest.messages.user.success"
    SUGGEST_USER_FAILURE = "commands.suggest.messages.user.failure"
    SUGGEST_PENDING_SUCCESS = "commands.suggest.messages.pending.success"
    SUGGEST_PENDING_FAILURE = "commands.suggest.messages.pending.failure"
    SUGGEST_RESULT_APPROVE = "commands.suggest.messages.result.approve"
    SUGGEST_RESULT_REJECT = "commands.suggest.messages.result.reject"

    WIKI_USER_SUCCESS = "commands.wiki.messages.user.success"
    WIKI_USER_FAILURE = "commands.wiki.messages.user.failure"


class SystemMessageKeys(Enum):
    TICKET_SYSTEM_STARTUP = "systems.ticket.messages.system.startup"
    TICKET_SYSTEM_CREATIONS = "systems.ticket.messages.system.creation"
    TICKET_SYSTEM_CLOSING = "systems.ticket.messages.system.closing"
    TICKET_USER_SUCCESS = "systems.ticket.messages.user.success"
    TICKET_USER_FAILURE = "systems.ticket.messages.user.failure"
    TICKET_LOG_TRANSCRIPT = "systems.ticket.messages.log.transcript"


class GeneralMessageKeys(Enum):
    """General message keys for the bot"""

    SUCCESS = "general.success"
    FAILURE = "general.failure"
    NO_REASON = "general.no_reason"


class ErrorMessageKeys(Enum):
    """Error message keys for the bot"""

    UNKNOWN = "error.unknown_error"
    TIMEOUT = "error.timeout_error"
    COMMAND_ON_COOLDOWN = "error.command_on_cooldown"
    USER_NOT_FOUND = "error.user_not_found"
    MEMBER_NOT_FOUND = "error.member_not_found"
    CHANNEL_NOT_FOUND = "error.channel_not_found"
    COMMAND_EXECUTION = "error.command_execution_error"
    USER_RECORD_NOT_FOUND = "error.user_record_not_found"
    ACCOUNT_ALREADY_LINKED = "error.account_already_linked"
    ACCOUNT_NOT_LINKED = "error.account_not_linked"
    PLAYER_NOT_ONLINE = "error.player_not_online"
    CAN_NOT_MODERATE = "error.can_not_moderate"
    USER_ALREADY_TIMED_OUT = "error.user_already_timed_out"
    USER_NOT_TIMED_OUT = "error.user_not_timed_out"
    DURATION_OUT_OF_RANGE = "error.duration_out_of_range"
    MAX_AMOUNT_OF_TICKETS_REACHED = "error.max_amount_of_tickets_reached"


class MessageKeys:
    """Message keys for the bot"""

    events = EventMessageKeys
    commands = CommandMessageKeys
    systems = SystemMessageKeys
    general = GeneralMessageKeys
    error = ErrorMessageKeys


class ModalKeys(Enum):
    """Modal keys for the bot"""

    LINK_ACCOUNT_CONFIRMATION = "commands.link_account.modal.confirmation"
    SUGGEST_SEND = "commands.suggest.modal.send"
    SUGGEST_RESPOND = "commands.suggest.modal.respond"

    TICKET_MODALS = "systems.ticket.modal"


class MenuKeys(Enum):
    """Menu keys for the bot"""

    SUGGEST_CONFIRMATION = "commands.suggest.menu.confirmation"

    TICKET_CLOSE = "systems.ticket.menu.inner.close"
    TICKET_CONFIRM = "systems.ticket.menu.outer.confirm"
    TICKET_CANCEL = "systems.ticket.menu.outer.cancel"


class TimeUnitKeys(Enum):
    """Time unit keys for the bot"""

    YEAR = "time_units.year"
    MONTH = "time_units.month"
    WEEK = "time_units.week"
    DAY = "time_units.day"
    HOUR = "time_units.hour"
    MINUTE = "time_units.minute"
    SECOND = "time_units.second"
