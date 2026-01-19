package org.mineacademy.minebridge.core.schema;

import org.mineacademy.minebridge.core.internal.BaseSchema;

import lombok.Getter;

public class SendServerMessage extends BaseSchema {

    /**
     * The message type to send to all players.
     */
    @Getter
    private final String message_type;

    /**
     * The message to send to all players.
     */
    @Getter
    private final String message;

    public SendServerMessage(String message_type, String message, String server) {
        super("send-server-message", server);
        this.message_type = message_type;
        this.message = message;
    }
}
