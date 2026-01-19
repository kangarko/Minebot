package org.mineacademy.minebridge.bungee;

import java.net.URISyntaxException;

import org.mineacademy.fo.Common;
import org.mineacademy.fo.platform.BungeePlugin;
import org.mineacademy.fo.platform.Platform;
import org.mineacademy.minebridge.bungee.listener.CommandListenerBungeeCord;
import org.mineacademy.minebridge.core.settings.Settings;
import org.mineacademy.minebridge.core.websocket.Client;
import org.mineacademy.minebridge.proxy.actions.CommandActionHandler;
import org.mineacademy.minebridge.proxy.actions.MessageActionHandler;
import org.mineacademy.minebridge.proxy.actions.PlayerActionHandler;

public class MineBridgeBungeeCord extends BungeePlugin {

    private Client webSocketClient;

    @Override
    public String[] getStartupLogo() {
        return new String[] {
                "&c  __  __ _____ _   _ ______ ____  _____  _____ _____   _____ ______ ",
                "&4 |  \\/  |_   _| \\ | |  ____|  _ \\|  __ \\|_   _|  __ \\ / ____|  ____|",
                "&4 | \\  / | | | |  \\| | |__  | |_) | |__) | | | | |  | | |  __| |__   ",
                "&4 | |\\/| | | | | . ` |  __| |  _ <|  _  /  | | | |  | | | |_ |  __|  ",
                "&4 | |  | |_| |_| |\\  | |____| |_) | | \\ \\ _| |_| |__| | |__| | |____ ",
                "&4 |_|  |_|_____|_| \\_|______|____/|_|  \\_\\_____|_____/ \\_____|______|",
                "&0                                                                    ",
        };
    }

    @Override
    protected void onPluginStart() {
        try {
            // Create WebSocket client
            webSocketClient = new Client(
                    Settings.WebSocket.HOST,
                    Settings.WebSocket.PORT,
                    Settings.WebSocket.PASSWORD,
                    getServerNames(),
                    getDataFolder());

            // Register handler classes with WebSocketAction annotations
            webSocketClient.registerActionHandler(new PlayerActionHandler(), new MessageActionHandler(),
                    new CommandActionHandler());

            // Connect to the WebSocket server
            webSocketClient.connect();

            // Register the command listener
            registerEvents(new CommandListenerBungeeCord(webSocketClient));

            Common.log("Client started and connected successfully");
        } catch (URISyntaxException e) {
            Common.error(e, "Failed to create client: " + e.getMessage());
        }
    }

    @Override
    protected void onPluginStop() {
        // Close the WebSocket connection when the plugin is disabled
        if (webSocketClient != null && webSocketClient.isOpen()) {
            webSocketClient.close();
            Common.log("Client connection closed");
        }
    }

    private String[] getServerNames() {
        return Platform.getServers().stream()
                .map(server -> server.getName())
                .toArray(size -> new String[size]);
    }
}
