package org.mineacademy.minebridge.velocity.listener;

import org.mineacademy.minebridge.core.internal.CommandHandler;
import org.mineacademy.minebridge.core.websocket.Client;

import com.velocitypowered.api.command.CommandSource;
import com.velocitypowered.api.event.Subscribe;
import com.velocitypowered.api.event.command.CommandExecuteEvent;
import com.velocitypowered.api.proxy.Player;

public final class CommandListenerVelocity extends CommandHandler {

    private final Client webSocketClient;

    /**
     * Initialize the command listener with the given WebSocket client
     * 
     * @param webSocketClient The WebSocket client to use for communication
     * @throws IllegalArgumentException if webSocketClient is null
     */
    public CommandListenerVelocity(Client webSocketClient) {
        if (webSocketClient == null) {
            throw new IllegalArgumentException("WebSocket client cannot be null");
        }
        this.webSocketClient = webSocketClient;
    }

    @Subscribe
    public void onCommandExecuted(final CommandExecuteEvent event) {
        CommandSource sender = event.getCommandSource();
        String executor = sender instanceof Player ? ((Player) sender).getUsername() : "CONSOLE";

        processCommand(event.getCommand(), executor, webSocketClient);
    }

}
