package org.mineacademy.minebridge.core.schema;

import org.mineacademy.minebridge.core.internal.BaseSchema;

import lombok.Getter;

public class SendPlayerMessage extends BaseSchema {

    /**
     * The username of the player to send the message to.
     */
    @Getter
    private final String username;

    /**
     * The UUID of the player to send the message to.
     */
    @Getter
    private final String uuid;

    /**
     * The message type to send to the player.
     */
    @Getter
    private final String message_type;

    /**
     * The message to send to the player.
     */
    @Getter
    private final String message;

    public SendPlayerMessage(String username, String uuid, String message_type, String message) {
        super("send-player-message", false);
        this.username = username;
        this.uuid = uuid;
        this.message_type = message_type;
        this.message = message;
    }

}
