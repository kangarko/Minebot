package org.mineacademy.minebridge.core.internal;

import org.mineacademy.minebridge.core.websocket.Client;

/**
 * Interface for classes that need access to the WebSocket client.
 */
public interface WebSocketAware {
    /**
     * Sets the WebSocket client for this class to use.
     * 
     * @param client The WebSocket client
     */
    void setClient(Client client);
}