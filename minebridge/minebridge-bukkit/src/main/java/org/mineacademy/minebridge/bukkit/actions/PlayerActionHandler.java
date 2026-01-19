package org.mineacademy.minebridge.bukkit.actions;

import java.util.UUID;
import java.util.function.Function;

import org.bukkit.entity.Player;
import org.mineacademy.fo.PlayerUtil;
import org.mineacademy.fo.debug.Debugger;
import org.mineacademy.fo.remain.Remain;
import org.mineacademy.minebridge.core.annotation.WebSocketAction;
import org.mineacademy.minebridge.core.internal.WebSocketAware;
import org.mineacademy.minebridge.core.schema.PlayerStatusCheck;
import org.mineacademy.minebridge.core.websocket.Client;

import lombok.RequiredArgsConstructor;

/**
 * Handles WebSocket actions related to player status on the Bukkit server.
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
        public Player findPlayer() {
            return username != null ? PlayerUtil.getPlayerByNick(username, false)
                    : uuid != null ? Remain.getPlayerByUUID(UUID.fromString(uuid))
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
                        player != null && player.isConnected()).toJson());

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
            Function<Player, String> responseGenerator) {

        // Find player by username or UUID
        final PlayerLookupParams params = new PlayerLookupParams(username, uuid);
        final Player player = params.findPlayer();

        // Generate response
        final String response = responseGenerator.apply(player);

        // Log the response for debugging
        Debugger.debug("websocket", "Sending player response: " + response);

        return response;
    }
}