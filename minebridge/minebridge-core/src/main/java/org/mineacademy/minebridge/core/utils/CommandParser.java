package org.mineacademy.minebridge.core.utils;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

import org.mineacademy.minebridge.core.settings.Settings;

/**
 * Utility class for parsing and validating commands.
 */
public final class CommandParser {
    private static final Map<String, String> LOWERCASE_ALIAS_TO_COMMAND_TYPE = new HashMap<>();
    private static final Map<String, Set<String>> ALIASES = Settings.CommandAliases.ALIASES;
    private static final Map<String, String> SYNTAX = Settings.CommandSyntax.SYNTAX;

    // Cache for parsed syntax definitions to avoid repeated parsing
    private static final Map<String, List<SyntaxParam>> PARSED_SYNTAX_CACHE = new ConcurrentHashMap<>();

    static {
        // Pre-compute alias mappings
        for (Map.Entry<String, Set<String>> entry : ALIASES.entrySet()) {
            String commandType = entry.getKey();
            for (String alias : entry.getValue()) {
                LOWERCASE_ALIAS_TO_COMMAND_TYPE.put(alias.toLowerCase(Locale.ROOT), commandType);
            }
        }

        // Pre-parse all syntax definitions
        for (Map.Entry<String, String> entry : SYNTAX.entrySet()) {
            PARSED_SYNTAX_CACHE.put(entry.getKey(), parseSyntax(entry.getValue()));
        }
    }

    private CommandParser() {
        throw new UnsupportedOperationException("Utility class");
    }

    /**
     * Parses a command message into a structured ParsedCommand object.
     */
    public static ParsedCommand parseCommand(final String message) {
        if (message == null || message.isEmpty()) {
            return null;
        }

        final String processedMessage = message.startsWith("/") ? message.substring(1) : message;

        // Find the first space to separate command from parameters more efficiently
        final int spaceIndex = processedMessage.indexOf(' ');
        final String commandPart = spaceIndex == -1 ? processedMessage : processedMessage.substring(0, spaceIndex);
        final String commandPartLower = commandPart.toLowerCase(Locale.ROOT);

        // Direct lookup for the command
        final String commandType = LOWERCASE_ALIAS_TO_COMMAND_TYPE.get(commandPartLower);
        if (commandType == null) {
            return null;
        }

        // Parse parameters if present
        final List<String> parameters = spaceIndex == -1 ? Collections.emptyList()
                : parseParameters(processedMessage.substring(spaceIndex + 1));

        final ParsedCommand parsedCommand = new ParsedCommand(commandType, commandPart, parameters);

        // Map parameters to their names
        mapNamedParameters(parsedCommand);

        return parsedCommand;
    }

    /**
     * Maps parameters to their names based on syntax definition
     */
    private static void mapNamedParameters(ParsedCommand parsedCommand) {
        String commandType = parsedCommand.getCommandType();
        List<SyntaxParam> syntaxParams = PARSED_SYNTAX_CACHE.get(commandType);
        if (syntaxParams == null) {
            return;
        }

        // Map parameters to their names
        List<String> params = parsedCommand.getParameters();
        for (int i = 0; i < syntaxParams.size() && i < params.size(); i++) {
            parsedCommand.mapParameter(syntaxParams.get(i).name, params.get(i));
        }
    }

    /**
     * Parses a parameter string into a list of parameters.
     */
    private static List<String> parseParameters(String paramString) {
        if (paramString.isEmpty()) {
            return Collections.emptyList();
        }

        final List<String> parameters = new ArrayList<>();
        final StringBuilder currentParam = new StringBuilder(32);
        boolean inQuotes = false;
        boolean escaped = false;
        final int length = paramString.length();

        for (int i = 0; i < length; i++) {
            char c = paramString.charAt(i);

            if (escaped) {
                currentParam.append(c);
                escaped = false;
            } else if (c == '\\') {
                escaped = true;
            } else if (c == '"') {
                inQuotes = !inQuotes;
            } else if (c == ' ' && !inQuotes) {
                if (currentParam.length() > 0) {
                    parameters.add(currentParam.toString());
                    currentParam.setLength(0);
                }
            } else {
                currentParam.append(c);
            }
        }

        // Add the last parameter if there is one
        if (currentParam.length() > 0) {
            parameters.add(currentParam.toString());
        }

        return parameters;
    }

    /**
     * Validates if a parsed command matches its syntax definition.
     */
    public static ValidationResult validateCommandSyntax(ParsedCommand command) {
        if (command == null) {
            return ValidationResult.failure("Command is null");
        }

        String commandType = command.getCommandType();
        if (!SYNTAX.containsKey(commandType)) {
            return ValidationResult.failure("Unknown command type: " + commandType);
        }

        List<SyntaxParam> syntaxParams = PARSED_SYNTAX_CACHE.get(commandType);
        if (syntaxParams == null) {
            return ValidationResult.failure("Syntax not parsed for command type: " + commandType);
        }

        // Count required parameters
        int requiredParams = 0;
        for (SyntaxParam param : syntaxParams) {
            if (param.required) {
                requiredParams++;
            }
        }

        // Check if we have enough parameters
        if (command.getParameters().size() < requiredParams) {
            // Find first missing parameter
            int providedRequired = 0;
            for (SyntaxParam param : syntaxParams) {
                if (param.required) {
                    providedRequired++;
                    if (providedRequired > command.getParameters().size()) {
                        return ValidationResult.failure(
                                "Missing required parameter: " + param.name + ". Usage: " +
                                        SYNTAX.get(commandType));
                    }
                }
            }
        }

        return ValidationResult.success();
    }

    /**
     * Returns the syntax usage string for a command.
     */
    public static String getCommandUsage(String commandType) {
        return SYNTAX.getOrDefault(commandType, null);
    }

    /**
     * Compiles a command string from a command type and named parameters.
     * 
     * @param commandType The command type to compile
     * @param parameters  Map of parameter names to their values
     * @return The compiled command string, or null if the command type doesn't
     *         exist
     */
    public static String compileCommand(String commandType, Map<String, String> parameters) {
        if (!SYNTAX.containsKey(commandType)) {
            return null;
        }

        // Get the primary alias for this command
        String alias = getPrimaryAlias(commandType);
        if (alias == null) {
            return null;
        }

        // Get syntax parameters in order
        List<SyntaxParam> syntaxParams = PARSED_SYNTAX_CACHE.get(commandType);

        StringBuilder commandBuilder = new StringBuilder();
        commandBuilder.append('/').append(alias);

        // Add parameters in the correct order according to syntax
        for (SyntaxParam param : syntaxParams) {
            String paramName = param.name.toLowerCase(Locale.ROOT);
            String value = parameters.get(paramName);

            // Skip optional parameters if not provided
            if (value == null) {
                if (param.required) {
                    // Missing required parameter
                    return null;
                }
                continue;
            }

            // Add the parameter
            commandBuilder.append(' ');

            // If parameter contains spaces or special characters, wrap in quotes
            if (value.contains(" ") || value.contains("\"")) {
                // Escape any quotes in the value
                String escapedValue = value.replace("\"", "\\\"");
                commandBuilder.append('"').append(escapedValue).append('"');
            } else {
                commandBuilder.append(value);
            }
        }

        return commandBuilder.toString();
    }

    /**
     * Compiles a command string from a command type and ordered parameters.
     * 
     * @param commandType The command type to compile
     * @param parameters  List of parameter values in order
     * @return The compiled command string, or null if the command type doesn't
     *         exist
     */
    public static String compileCommand(String commandType, List<String> parameters) {
        if (!SYNTAX.containsKey(commandType)) {
            return null;
        }

        // Get the primary alias for this command
        String alias = getPrimaryAlias(commandType);
        if (alias == null) {
            return null;
        }

        // Get syntax parameters to check required parameters
        List<SyntaxParam> syntaxParams = PARSED_SYNTAX_CACHE.get(commandType);

        // Count required parameters
        int requiredParams = 0;
        for (SyntaxParam param : syntaxParams) {
            if (param.required) {
                requiredParams++;
            }
        }

        // Check if we have enough parameters
        if (parameters.size() < requiredParams) {
            return null;
        }

        StringBuilder commandBuilder = new StringBuilder();
        commandBuilder.append('/').append(alias);

        // Add all provided parameters
        for (String value : parameters) {
            commandBuilder.append(' ');

            // If parameter contains spaces or special characters, wrap in quotes
            if (value.contains(" ") || value.contains("\"")) {
                // Escape any quotes in the value
                String escapedValue = value.replace("\"", "\\\"");
                commandBuilder.append('"').append(escapedValue).append('"');
            } else {
                commandBuilder.append(value);
            }
        }

        return commandBuilder.toString();
    }

    /**
     * Gets the primary alias for a command type.
     * Uses the first alias in the set as the primary.
     * 
     * @param commandType The command type
     * @return The primary alias, or null if the command type has no aliases
     */
    private static String getPrimaryAlias(String commandType) {
        Set<String> aliases = ALIASES.get(commandType);
        if (aliases == null || aliases.isEmpty()) {
            return null;
        }
        // Return the first alias in the set
        return aliases.iterator().next();
    }

    /**
     * Helper class to represent a parameter in the command syntax.
     */
    private static class SyntaxParam {
        final String name;
        final boolean required;

        SyntaxParam(String name, boolean required) {
            this.name = name;
            this.required = required;
        }
    }

    /**
     * Parses the syntax string into parameter definitions.
     */
    private static List<SyntaxParam> parseSyntax(String syntax) {
        String[] parts = syntax.split(" ");
        List<SyntaxParam> params = new ArrayList<>(parts.length - 1);

        // Skip the command itself (first part)
        for (int i = 1; i < parts.length; i++) {
            String part = parts[i];
            if (part.startsWith("<") && part.endsWith(">")) {
                params.add(new SyntaxParam(part.substring(1, part.length() - 1), true));
            } else if (part.startsWith("[") && part.endsWith("]")) {
                params.add(new SyntaxParam(part.substring(1, part.length() - 1), false));
            }
        }

        return params;
    }

    /**
     * Class for command validation results with status and error message.
     */
    public static class ValidationResult {
        // Using static singletons for common results to reduce object creation
        private static final ValidationResult SUCCESS = new ValidationResult(true, null);

        private final boolean valid;
        private final String errorMessage;

        private ValidationResult(boolean valid, String errorMessage) {
            this.valid = valid;
            this.errorMessage = errorMessage;
        }

        public boolean isValid() {
            return valid;
        }

        public String getErrorMessage() {
            return errorMessage;
        }

        public static ValidationResult success() {
            return SUCCESS;
        }

        public static ValidationResult failure(String errorMessage) {
            return new ValidationResult(false, errorMessage);
        }
    }

    /**
     * Represents a parsed command with its type, used alias, and parameters.
     */
    public static class ParsedCommand {
        private final String commandType;
        private final String usedAlias;
        private final List<String> parameters;
        private final Map<String, String> namedParameters;

        public ParsedCommand(String commandType, String usedAlias, List<String> parameters) {
            this.commandType = commandType;
            this.usedAlias = usedAlias;
            this.parameters = Collections.unmodifiableList(
                    parameters instanceof ArrayList ? parameters : new ArrayList<>(parameters));
            // Initialize with expected capacity based on parameter size
            this.namedParameters = parameters.isEmpty() ? Collections.emptyMap() : new HashMap<>(parameters.size());
        }

        /**
         * Maps a parameter name to a parameter value
         */
        void mapParameter(String name, String value) {
            namedParameters.put(name.toLowerCase(Locale.ROOT), value);
        }

        public String getCommandType() {
            return commandType;
        }

        public String getUsedAlias() {
            return usedAlias;
        }

        public List<String> getParameters() {
            return parameters;
        }

        public String getParameter(int index) {
            return index < parameters.size() ? parameters.get(index) : null;
        }

        /**
         * Gets a parameter by its name as defined in the syntax
         */
        public String getParameter(String name) {
            return namedParameters.get(name.toLowerCase(Locale.ROOT));
        }

        /**
         * Gets a parameter by its name with a default value if not found
         */
        public String getParameter(String name, String defaultValue) {
            return namedParameters.getOrDefault(name.toLowerCase(Locale.ROOT), defaultValue);
        }

        /**
         * Checks if a named parameter exists
         */
        public boolean hasParameter(String name) {
            return namedParameters.containsKey(name.toLowerCase(Locale.ROOT));
        }

        public boolean hasParameter(int index) {
            return index < parameters.size();
        }

        /**
         * Gets a combined reason parameter (all parameters after a specific index).
         */
        public String getCombinedParameter(int startIndex) {
            if (startIndex >= parameters.size()) {
                return null;
            }

            if (startIndex == parameters.size() - 1) {
                return parameters.get(startIndex);
            }

            StringBuilder combined = new StringBuilder(64); // Pre-allocate reasonable size
            combined.append(parameters.get(startIndex));
            for (int i = startIndex + 1; i < parameters.size(); i++) {
                combined.append(' ').append(parameters.get(i));
            }

            return combined.toString();
        }

        /**
         * Gets a combined parameter string starting from a named parameter.
         * Especially useful for parameters like "reason" that may contain multiple
         * words.
         *
         * @param paramName The name of the parameter to start from
         * @return The combined parameter string or null if the named parameter isn't
         *         found
         */
        public String getCombinedNamedParameter(String paramName) {
            if (!hasParameter(paramName)) {
                return null;
            }

            // Find the parameter index in the original parameters list
            String paramNameLower = paramName.toLowerCase(Locale.ROOT);
            List<SyntaxParam> syntaxParams = PARSED_SYNTAX_CACHE.get(commandType);
            if (syntaxParams == null) {
                return getParameter(paramName);
            }

            // Find the index of this named parameter
            int paramIndex = -1;
            for (int i = 0; i < syntaxParams.size() && i < parameters.size(); i++) {
                if (syntaxParams.get(i).name.toLowerCase(Locale.ROOT).equals(paramNameLower)) {
                    paramIndex = i;
                    break;
                }
            }

            if (paramIndex == -1) {
                return getParameter(paramName);
            }

            // Get the combined parameter from this index
            return getCombinedParameter(paramIndex);
        }

        @Override
        public String toString() {
            return String.format("ParsedCommand[type=%s, alias=%s, params=%s, namedParams=%s]",
                    commandType, usedAlias, parameters, namedParameters);
        }
    }
}