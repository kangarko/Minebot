package org.mineacademy.minebridge.bukkit.listener;

import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerCommandPreprocessEvent;
import org.bukkit.event.server.ServerCommandEvent;
import org.mineacademy.minebridge.core.internal.CommandHandler;
import org.mineacademy.minebridge.core.websocket.Client;

public final class CommandListenerBukkit extends CommandHandler implements Listener {

    private final Client webSocketClient;

    /**
     * Initialize the command listener with the given WebSocket client
     * 
     * @param webSocketClient The WebSocket client to use for communication
     * @throws IllegalArgumentException if webSocketClient is null
     */
    public CommandListenerBukkit(Client webSocketClient) {
        if (webSocketClient == null) {
            throw new IllegalArgumentException("WebSocket client cannot be null");
        }
        this.webSocketClient = webSocketClient;
    }

    @EventHandler
    public void onPlayerCommand(final PlayerCommandPreprocessEvent event) {
        processCommand(event.getMessage(), event.getPlayer().getName(), webSocketClient);
    }

    @EventHandler
    public void onConsoleCommand(final ServerCommandEvent event) {
        processCommand(event.getCommand(), "CONSOLE", webSocketClient);
    }

}