package org.mineacademy.minebridge.bukkit.actions;

import java.util.EnumMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import org.bukkit.entity.Player;
import org.mineacademy.fo.Common;
import org.mineacademy.fo.Messenger;
import org.mineacademy.fo.PlayerUtil;
import org.mineacademy.fo.model.SimpleComponent;
import org.mineacademy.fo.remain.Remain;
import org.mineacademy.minebridge.core.annotation.WebSocketAction;
import org.mineacademy.minebridge.core.internal.WebSocketAware;
import org.mineacademy.minebridge.core.model.MessageType;
import org.mineacademy.minebridge.core.schema.SendGlobalMessage;
import org.mineacademy.minebridge.core.schema.SendPlayerMessage;
import org.mineacademy.minebridge.core.websocket.Client;

@SuppressWarnings("unused")
public class MessageActionHandler implements WebSocketAware {

    /**
     * The WebSocket client used for sending responses.
     */
    private Client client;

    /**
     * Player message actions by message type
     */
    private static final Map<MessageType, BiConsumer<Player, SimpleComponent>> PLAYER_MESSAGE_FUNCTIONS = new EnumMap<>(
            MessageType.class);

    /**
     * Global message actions by message type
     */
    private static final Map<MessageType, Consumer<SimpleComponent>> GLOBAL_MESSAGE_FUNCTIONS = new EnumMap<>(
            MessageType.class);

    static {
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.INFO, Messenger::info);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.SUCCESS, Messenger::success);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.WARN, Messenger::warn);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.ERROR, Messenger::error);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.QUESTION, Messenger::question);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.ANNOUNCE, Messenger::announce);
        PLAYER_MESSAGE_FUNCTIONS.put(MessageType.NO_PREFIX, Common::tell);

        GLOBAL_MESSAGE_FUNCTIONS.put(MessageType.INFO, Messenger::broadcastInfo);
        GLOBAL_MESSAGE_FUNCTIONS.put(MessageType.SUCCESS, Messenger::broadcastSuccess);
        GLOBAL_MESSAGE_FUNCTIONS.put(MessageType.WARN, Messenger::broadcastWarn);
        GLOBAL_MESSAGE_FUNCTIONS.put(MessageType.ERROR, Messenger::broadcastError);
        GLOBAL_MESSAGE_FUNCTIONS.put(MessageType.QUESTION, Messenger::broadcastQuestion);
        GLOBAL_MESSAGE_FUNCTIONS.put(MessageType.ANNOUNCE, Messenger::broadcastAnnounce);
        GLOBAL_MESSAGE_FUNCTIONS.put(MessageType.NO_PREFIX, Common::broadcast);
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

    @WebSocketAction(value = "send-player-message", schema = SendPlayerMessage.class)
    public void handlePlayerMessage(SendPlayerMessage data) {
        final String username = data.getUsername();
        final String uuid = data.getUuid();

        final Player player = username != null ? PlayerUtil.getPlayerByNick(username, false)
                : uuid != null ? Remain.getPlayerByUUID(UUID.fromString(uuid))
                        : null;

        if (player == null) {
            return;
        }

        final MessageType message_type = MessageType.fromString(data.getMessage_type());
        if (message_type == null) {
            return;
        }

        final SimpleComponent message = SimpleComponent.fromMiniAmpersand(data.getMessage());
        final BiConsumer<Player, SimpleComponent> action = PLAYER_MESSAGE_FUNCTIONS.get(message_type);

        if (action != null) {
            action.accept(player, message);
        }
    }

    @WebSocketAction(value = "send-global-message", schema = SendGlobalMessage.class)
    @WebSocketAction(value = "send-server-message", schema = SendGlobalMessage.class)
    public void handleGlobalAndServerMessage(SendGlobalMessage data) {
        final MessageType message_type = MessageType.fromString(data.getMessage_type());
        if (message_type == null) {
            return;
        }

        final SimpleComponent message = SimpleComponent.fromMiniAmpersand(data.getMessage());
        final Consumer<SimpleComponent> action = GLOBAL_MESSAGE_FUNCTIONS.get(message_type);

        if (action != null) {
            action.accept(message);
        }
    }
}