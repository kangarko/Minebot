package org.mineacademy.minebridge.core.model;

import java.util.HashMap;
import java.util.Map;

/**
 * Enum representing different types of messages with their formatting styles.
 */
public enum MessageType {
    INFO,
    SUCCESS,
    WARN,
    ERROR,
    QUESTION,
    ANNOUNCE,
    NO_PREFIX;

    // Cache for string representations to avoid repeated string creation
    private final String lowercaseName;

    // Cache for lookups by string to avoid repeated enum parsing
    private static final Map<String, MessageType> LOOKUP_MAP = new HashMap<>();

    // Initialize lookup map
    static {
        for (MessageType type : values()) {
            LOOKUP_MAP.put(type.name().toUpperCase(), type);
        }
    }

    /**
     * Constructor that pre-computes the lowercase name
     */
    MessageType() {
        this.lowercaseName = name().toLowerCase();
    }

    /**
     * Converts a string to a MessageType, case insensitive.
     * Returns null if the string doesn't match any message type.
     *
     * @param type The string to convert
     * @return The corresponding MessageType or null if not found
     */
    public static MessageType fromString(String type) {
        if (type == null)
            return null;

        return LOOKUP_MAP.get(type.toUpperCase());
    }

    /**
     * Returns the lowercase representation of this message type
     * 
     * @return The lowercase name of this message type
     */
    @Override
    public String toString() {
        return lowercaseName;
    }
}