package org.mineacademy.minebridge.core.internal;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import org.mineacademy.minebridge.core.schema.CommandExecuted;
import org.mineacademy.minebridge.core.utils.CommandParser;
import org.mineacademy.minebridge.core.utils.CommandParser.ParsedCommand;
import org.mineacademy.minebridge.core.websocket.Client;

/**
 * Abstract command handler that provides platform-agnostic command processing
 */
public abstract class CommandHandler {

    // Command constants to avoid string duplication
    private static final String CMD_KICK = "kick";
    private static final String CMD_BAN = "ban";
    private static final String CMD_TEMPBAN = "tempban";
    private static final String CMD_UNBAN = "unban";
    private static final String CMD_TIMEOUT = "timeout";
    private static final String CMD_UNTIMEOUT = "untimeout";

    // Parameter constants
    private static final String PARAM_TARGET = "target";
    private static final String PARAM_DURATION = "duration";
    private static final String PARAM_REASON = "reason";

    // Expected command count for initial HashMap capacity
    private static final int EXPECTED_COMMAND_COUNT = 6;

    // Shared empty set for commands with no parameters
    private static final Set<String> EMPTY_PARAMS = Collections.emptySet();

    // Command registry map for O(1) command lookup, initialized with capacity
    private final Map<String, CommandSpec> commandSpecs = new HashMap<>(EXPECTED_COMMAND_COUNT * 4 / 3 + 1);

    /**
     * Command specification that includes parameter requirements
     */
    private static class CommandSpec {
        final Set<String> requiredParams;

        CommandSpec(String... requiredParams) {
            // Use empty set singleton when no parameters are required
            this.requiredParams = requiredParams.length > 0
                    ? Collections.unmodifiableSet(new HashSet<>(Arrays.asList(requiredParams)))
                    : EMPTY_PARAMS;
        }
    }

    /**
     * Constructor initializes all command handlers
     */
    public CommandHandler() {
        registerCommands();
    }

    /**
     * Register all available commands
     */
    protected void registerCommands() {
        // Register commands with their required parameters
        registerCommand(CMD_KICK, PARAM_TARGET);
        registerCommand(CMD_BAN, PARAM_TARGET);
        registerCommand(CMD_TEMPBAN, PARAM_TARGET, PARAM_DURATION);
        registerCommand(CMD_UNBAN, PARAM_TARGET);
        registerCommand(CMD_TIMEOUT, PARAM_TARGET, PARAM_DURATION);
        registerCommand(CMD_UNTIMEOUT, PARAM_TARGET);
    }

    /**
     * Register a command with its required parameters
     * 
     * @param commandType    The command name
     * @param requiredParams Required parameter names
     */
    private void registerCommand(final String commandType, final String... requiredParams) {
        commandSpecs.put(commandType, new CommandSpec(requiredParams));
    }

    /**
     * Process incoming commands and route to appropriate handlers
     *
     * @param message         The raw command message
     * @param executor        The name of who executed the command
     * @param webSocketClient The WebSocket client
     * @return true if the command was handled, false otherwise
     */
    protected boolean processCommand(final String message, final String executor, final Client webSocketClient) {
        // Parse the command
        final ParsedCommand parsedCommand = CommandParser.parseCommand(message);
        if (parsedCommand == null)
            return false;

        final String commandType = parsedCommand.getCommandType().toLowerCase();

        // Get the command spec
        final CommandSpec spec = commandSpecs.get(commandType);
        if (spec == null)
            return false;

        // Validate required parameters
        if (!validateParameters(parsedCommand, spec.requiredParams)) {
            return false;
        }

        // Extract parameters efficiently
        final Map<String, String> params = extractParameters(parsedCommand);

        // Create and send command
        final CommandExecuted commandExecuted = new CommandExecuted(commandType, executor, params);
        webSocketClient.send(commandExecuted.toJson());

        return true;
    }

    /**
     * Validate that all required parameters are present
     */
    private boolean validateParameters(ParsedCommand command, Set<String> requiredParams) {
        for (final String param : requiredParams) {
            String value = command.getParameter(param);
            if (value == null || value.isEmpty()) {
                return false;
            }
        }
        return true;
    }

    /**
     * Extract needed parameters from the parsed command
     */
    private Map<String, String> extractParameters(ParsedCommand command) {
        // Initial capacity with expected parameter count to avoid resizing
        final Map<String, String> params = new HashMap<>(4);

        String target = command.getParameter(PARAM_TARGET);
        if (target != null && !target.isEmpty()) {
            params.put(PARAM_TARGET, target);
        }

        String duration = command.getParameter(PARAM_DURATION);
        if (duration != null && !duration.isEmpty()) {
            params.put(PARAM_DURATION, duration);
        }

        String reason = command.getCombinedNamedParameter(PARAM_REASON);
        if (reason != null && !reason.isEmpty()) {
            params.put(PARAM_REASON, reason);
        }

        return params;
    }
}