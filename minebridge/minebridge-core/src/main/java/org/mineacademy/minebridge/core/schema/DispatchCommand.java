package org.mineacademy.minebridge.core.schema;

import org.mineacademy.minebridge.core.internal.BaseSchema;

import lombok.Getter;

public class DispatchCommand extends BaseSchema {

    @Getter
    private final String[] commands;

    public DispatchCommand(String[] commands, String server) {
        super("dispatch-command", server);
        this.commands = commands;
    }
}
