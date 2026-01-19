package org.mineacademy.minebridge.proxy.actions;

import java.util.UUID;
import java.util.function.Function;

import org.mineacademy.fo.debug.Debugger;
import org.mineacademy.fo.platform.FoundationPlayer;
import org.mineacademy.fo.platform.Platform;
import org.mineacademy.minebridge.core.annotation.WebSocketAction;
import org.mineacademy.minebridge.core.internal.WebSocketAware;
import org.mineacademy.minebridge.core.schema.PlayerServerCheck;
import org.mineacademy.minebridge.core.schema.PlayerStatusCheck;
import org.mineacademy.minebridge.core.websocket.Client;

import lombok.RequiredArgsConstructor;

/**
 * Handles WebSocket actions related to player status on the BungeeCord server.
 * This class implements WebSocketAware to handle communication with external
 * services.
 */
public class PlayerActionHandler implements WebSocketAware {

    /**
     * The WebSocket client used for sending responses.
     */
    private Client client;

    /**
     * Helper record to store player lookup parameters
     */
    @RequiredArgsConstructor
    private static class PlayerLookupParams {
        private final String username;
        private final String uuid;

        /**
         * Gets the player based on the provided parameters
         * 
         * @return The found player or null if not found
         */
        public FoundationPlayer findPlayer() {
            return username != null ? Platform.getPlayer(username)
                    : uuid != null ? Platform.getPlayer(UUID.fromString(uuid))
                            : null;
        }
    }

    /**
     * Sets the WebSocket client for this handler.
     * 
     * @param client The WebSocket client instance to use for communication
     */
    @Override
    public void setClient(Client client) {
        this.client = client;
    }

    /**
     * Handles player status check requests from WebSocket.
     * This method checks if a player is online based on username or UUID,
     * then sends back the status information.
     * 
     * @param data The schema containing request data (username and/or UUID)
     */
    @WebSocketAction(value = "player-status-check", schema = PlayerStatusCheck.class)
    public void playerStatusCheck(PlayerStatusCheck data) {
        // Process the request and get the response
        String response = processPlayerRequest(data.getUsername(), data.getUuid(),
                (player) -> new PlayerStatusCheck(
                        player != null ? player.getName() : data.getUsername(),
                        player != null ? player.getUniqueId().toString() : data.getUuid(),
                        player != null ? player.isPlayerOnline() : false).toJson());

        // Send the response
        client.send(response);
    }

    @WebSocketAction(value = "player-server-check", schema = PlayerServerCheck.class)
    public void playerServerCheck(PlayerServerCheck data) {
        // Process the request and get the response
        String response = processPlayerRequest(data.getUsername(), data.getUuid(),
                (player) -> new PlayerServerCheck(
                        player != null ? player.getName() : data.getUsername(),
                        player != null ? player.getUniqueId().toString() : data.getUuid(),
                        player != null ? player.getServer().getName() : null).toJson());

        // Send the response
        client.send(response);
    }

    /**
     * Processes a player request by finding the player and generating a response
     * 
     * @param username          Username to look up
     * @param uuid              UUID to look up
     * @param responseGenerator Function to generate a response from the found
     *                          player
     * @return The JSON response
     */
    private String processPlayerRequest(String username, String uuid,
            Function<FoundationPlayer, String> responseGenerator) {

        // Find player by username or UUID
        final PlayerLookupParams params = new PlayerLookupParams(username, uuid);
        final FoundationPlayer player = params.findPlayer();

        // Generate response
        final String response = responseGenerator.apply(player);

        // Log the response for debugging
        Debugger.debug("websocket", "Sending player response: " + response);

        return response;
    }
}