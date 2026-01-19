package org.mineacademy.minebridge.core.settings;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.mineacademy.fo.exception.FoException;
import org.mineacademy.fo.settings.SimpleSettings;

@SuppressWarnings("unused")
public class Settings extends SimpleSettings {

    // Using immutable set for better performance and safety
    private static final Set<String> COMMAND_LIST = Collections.unmodifiableSet(
            new HashSet<>(Arrays.asList("kick", "ban", "tempban", "unban", "timeout", "untimeout")));

    // Cached uncommented sections list
    private static final List<String> UNCOMMENTED_SECTIONS = Collections.unmodifiableList(Arrays.asList("websocket"));

    @Override
    protected List<String> getUncommentedSections() {
        return UNCOMMENTED_SECTIONS;
    }

    /*
     * Settings for the WebSocket connection
     */
    public static class WebSocket {
        public static String HOST;
        public static Integer PORT;
        public static String PASSWORD;

        private static void init() {
            setPathPrefix("websocket");
            HOST = getString("host");
            PORT = getInteger("port");
            PASSWORD = getString("password");

            // Enhanced validation
            if (HOST == null || HOST.isEmpty())
                throw new FoException("WebSocket host cannot be empty");

            if (PORT == null)
                throw new FoException("WebSocket port cannot be null");

            if (PORT < 1 || PORT > 65535)
                throw new FoException("Invalid WebSocket port: " + PORT + " (must be between 1-65535)");

            if (PASSWORD == null || PASSWORD.isEmpty())
                throw new FoException("WebSocket password cannot be empty");
        }
    }

    /*
     * Settings for the command aliases
     */
    public static class CommandAliases {
        // Using final and initialized with capacity for better performance
        public static final Map<String, Set<String>> ALIASES;

        static {
            // Initialize with expected capacity
            Map<String, Set<String>> aliases = new HashMap<>(COMMAND_LIST.size() * 4 / 3 + 1);
            setPathPrefix("aliases");

            for (String command : COMMAND_LIST) {
                aliases.put(command, Collections.unmodifiableSet(
                        new HashSet<>(getSet(command, String.class))));
            }

            ALIASES = Collections.unmodifiableMap(aliases);
        }

        private static void init() {
            // Initialization moved to static block for earlier evaluation
        }
    }

    /*
     * Settings for the syntax of commands
     */
    public static class CommandSyntax {
        // Using final and initialized with capacity for better performance
        public static final Map<String, String> SYNTAX;

        static {
            // Initialize with expected capacity
            Map<String, String> syntax = new HashMap<>(COMMAND_LIST.size() * 4 / 3 + 1);
            setPathPrefix("syntax");

            for (String command : COMMAND_LIST) {
                String syntaxStr = getString(command);
                if (syntaxStr == null || syntaxStr.isEmpty()) {
                    throw new FoException("Missing syntax definition for command: " + command);
                }
                syntax.put(command, syntaxStr);
            }

            SYNTAX = Collections.unmodifiableMap(syntax);
        }

        private static void init() {
            // Initialization moved to static block for earlier evaluation
        }
    }
}