package org.mineacademy.minebridge.core.schema;

import org.mineacademy.minebridge.core.internal.BaseSchema;

import lombok.Getter;

public class PlayerServerCheck extends BaseSchema {

    @Getter
    private final String username;

    @Getter
    private final String uuid;

    public PlayerServerCheck(String username, String uuid, String server) {
        super("player-server-check", server);
        this.username = username;
        this.uuid = uuid;
    }

}
