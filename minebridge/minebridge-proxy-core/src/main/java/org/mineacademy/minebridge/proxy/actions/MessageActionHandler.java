package org.mineacademy.minebridge.proxy.actions;

import java.util.EnumMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import org.mineacademy.fo.Messenger;
import org.mineacademy.fo.model.SimpleComponent;
import org.mineacademy.fo.platform.FoundationPlayer;
import org.mineacademy.fo.platform.FoundationServer;
import org.mineacademy.fo.platform.Platform;
import org.mineacademy.minebridge.core.annotation.WebSocketAction;
import org.mineacademy.minebridge.core.internal.WebSocketAware;
import org.mineacademy.minebridge.core.model.MessageType;
import org.mineacademy.minebridge.core.schema.SendGlobalMessage;
import org.mineacademy.minebridge.core.schema.SendServerMessage;
import org.mineacademy.minebridge.core.schema.SendPlayerMessage;
import org.mineacademy.minebridge.core.websocket.Client;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * Handles WebSocket message actions for player and global communications
 */
@SuppressWarnings("unused")
public class MessageActionHandler implements WebSocketAware {

    /**
     * The WebSocket client used for sending responses.
     */
    private Client client;

    /**
     * Data class to hold player message context
     */
    @Getter
    @RequiredArgsConstructor
    private static class PlayerMessageContext {
        private final FoundationPlayer player;
        private final SimpleComponent message;
    }

    /**
     * Data class to hold server message context
     */
    @Getter
    @RequiredArgsConstructor
    private static class ServerMessageContext {
        private final FoundationServer server;
        private final SimpleComponent message;
        private final MessageType type;
    }

    // BiConsumer for different message types with player and message parameters
    private static final Map<MessageType, BiConsumer<FoundationPlayer, SimpleComponent>> PLAYER_MESSAGE_FUNCTIONS = new EnumMap<>(
            MessageType.class);

    // Map for handling player messages with context
    private static final Map<MessageType, Consumer<PlayerMessageContext>> PLAYER_MESSAGE_ACTIONS = new EnumMap<>(
            MessageType.class);

    // Map for handling global messages
    private static final Map<MessageType, Consumer<SimpleComponent>> GLOBAL_MESSAGE_ACTIONS = new EnumMap<>(
            MessageType.class);

    /**
     * Initialize all message handler maps
     */
    static {
        // Initialize player message functions
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.INFO, Messenger::info);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.SUCCESS, Messenger::success);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.WARN, Messenger::warn);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.ERROR, Messenger::error);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.QUESTION, Messenger::question);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.ANNOUNCE, Messenger::announce);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.NO_PREFIX, (player, message) -> player.sendMessage(message));

        // Player message actions using the functions
        for (Map.Entry<MessageType, BiConsumer<FoundationPlayer, SimpleComponent>> entry : PLAYER_MESSAGE_FUNCTIONS
                .entrySet()) {
            PLAYER_MESSAGE_ACTIONS.put(entry.getKey(),
                    ctx -> entry.getValue().accept(ctx.getPlayer(), ctx.getMessage()));
        }

        // Global message actions
        GLOBAL_MESSAGE_ACTIONS.put(MessageType.INFO, Messenger::broadcastInfo);
        GLOBAL_MESSAGE_ACTIONS.put(MessageType.SUCCESS, Messenger::broadcastSuccess);
        GLOBAL_MESSAGE_ACTIONS.put(MessageType.WARN, Messenger::broadcastWarn);
        GLOBAL_MESSAGE_ACTIONS.put(MessageType.ERROR, Messenger::broadcastError);
        GLOBAL_MESSAGE_ACTIONS.put(MessageType.QUESTION, Messenger::broadcastQuestion);
        GLOBAL_MESSAGE_ACTIONS.put(MessageType.ANNOUNCE, Messenger::broadcastAnnounce);
        GLOBAL_MESSAGE_ACTIONS.put(MessageType.NO_PREFIX, msg -> {
            for (FoundationPlayer player : Platform.getOnlinePlayers())
                player.sendMessage(msg);
        });
    }

    /**
     * Process a message for all players in a server
     * 
     * @param context The server message context
     */
    private void processServerMessage(ServerMessageContext context) {
        BiConsumer<FoundationPlayer, SimpleComponent> messageFunction = PLAYER_MESSAGE_FUNCTIONS.get(context.getType());
        if (messageFunction != null) {
            context.getServer().getPlayerUniqueIds().forEach(uuid -> {
                FoundationPlayer player = Platform.getPlayer(uuid);
                if (player != null)
                    messageFunction.accept(player, context.getMessage());
            });
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
     * Handles send-player-message action from WebSocket
     * 
     * @param data The message schema data
     */
    @WebSocketAction(value = "send-player-message", schema = SendPlayerMessage.class)
    public void sendPlayerMessage(SendPlayerMessage data) {
        final String username = data.getUsername();
        final String uuid = data.getUuid();
        final MessageType message_type = MessageType.fromString(data.getMessage_type());
        final SimpleComponent message = SimpleComponent.fromMiniAmpersand(data.getMessage());

        // Find player by username or UUID
        final FoundationPlayer player = username != null ? Platform.getPlayer(username)
                : uuid != null ? Platform.getPlayer(UUID.fromString(uuid)) : null;

        if (player != null && message_type != null) {
            Consumer<PlayerMessageContext> action = PLAYER_MESSAGE_ACTIONS.get(message_type);
            if (action != null) {
                action.accept(new PlayerMessageContext(player, message));
            }
        }
    }

    /**
     * Handles send-global-message action from WebSocket
     * 
     * @param data The message schema data
     */
    @WebSocketAction(value = "send-global-message", schema = SendGlobalMessage.class)
    public void sendGlobalMessage(SendGlobalMessage data) {
        final MessageType message_type = MessageType.fromString(data.getMessage_type());
        final SimpleComponent message = SimpleComponent.fromMiniAmpersand(data.getMessage());

        if (message_type != null) {
            Consumer<SimpleComponent> action = GLOBAL_MESSAGE_ACTIONS.get(message_type);
            if (action != null) {
                action.accept(message);
            }
        }
    }

    /**
     * Handles send-server-message action from WebSocket (sends to a specific
     * server)
     * 
     * @param data The server message schema data
     */
    @WebSocketAction(value = "send-server-message", schema = SendServerMessage.class)
    public void sendServerMessage(SendServerMessage data) {
        final String serverName = data.getServer();
        final MessageType message_type = MessageType.fromString(data.getMessage_type());
        final SimpleComponent message = SimpleComponent.fromMiniAmpersand(data.getMessage());

        if (serverName != null && message_type != null) {
            FoundationServer server = Platform.getServer(serverName);
            if (server != null) {
                processServerMessage(new ServerMessageContext(server, message, message_type));
            }
        }
    }
}