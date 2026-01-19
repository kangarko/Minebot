package org.mineacademy.minebridge.core.schema;

import org.mineacademy.minebridge.core.internal.BaseSchema;

import lombok.Getter;

public class SendGlobalMessage extends BaseSchema {

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

    public SendGlobalMessage(String message_type, String message) {
        super("send-global-message", false);
        this.message_type = message_type;
        this.message = message;
    }

}
