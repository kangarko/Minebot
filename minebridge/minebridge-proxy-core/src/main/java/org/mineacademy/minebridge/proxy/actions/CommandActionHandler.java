package org.mineacademy.minebridge.proxy.actions;

import java.util.Arrays;
import java.util.stream.Stream;

import org.mineacademy.fo.platform.FoundationServer;
import org.mineacademy.fo.platform.Platform;
import org.mineacademy.fo.proxy.message.OutgoingMessage;
import org.mineacademy.minebridge.core.annotation.WebSocketAction;
import org.mineacademy.minebridge.core.internal.WebSocketAware;
import org.mineacademy.minebridge.core.model.MineBridgeProxyMessage;
import org.mineacademy.minebridge.core.schema.CommandExecuted;
import org.mineacademy.minebridge.core.schema.DispatchCommand;
import org.mineacademy.minebridge.core.utils.CommandParser;
import org.mineacademy.minebridge.core.websocket.Client;

@SuppressWarnings("unused")
public class CommandActionHandler implements WebSocketAware {

    /**
     * The WebSocket client used for sending responses.
     */
    private Client client;

    /**
     * Sets the WebSocket client for this handler.
     * 
     * @param client The WebSocket client instance to use for communication
     */
    @Override
    public void setClient(Client client) {
        this.client = client;
    }

    @WebSocketAction(value = "dispatch-command", schema = DispatchCommand.class)
    public void dispatchCommand(DispatchCommand data) {
        final String server = data.getServer();
        final Stream<String> commands = Arrays.stream(data.getCommands())
                .filter(cmd -> cmd != null && !cmd.isEmpty());

        if ("all".equals(server)) {
            Platform.getServers().forEach(srv -> dispatchCommandsToServer(commands, srv));
        } else {
            dispatchCommandsToServer(commands, Platform.getServer(server));
        }
    }

    @WebSocketAction(value = "command-executed", schema = CommandExecuted.class)
    public void commandExecuted(CommandExecuted data) {
        final String server = data.getServer();
        final String commandString = CommandParser.compileCommand(data.getCommand_type(), data.getArgs());

        if (commandString == null || commandString.isEmpty()) {
            return; // Ignore empty commands
        }

        if ("all".equals(server)) {
            Platform.getServers().forEach(srv -> dispatchCommandToServer(commandString, srv));
        } else {
            dispatchCommandToServer(commandString, Platform.getServer(server));
        }
    }

    /**
     * Sends multiple commands to a specific server
     * 
     * @param commands Array of commands to dispatch
     * @param server   The target server
     */
    private void dispatchCommandsToServer(final Stream<String> commands, final FoundationServer server) {
        commands.forEach(cmd -> {
            final OutgoingMessage msg = new OutgoingMessage(MineBridgeProxyMessage.DISPATCH_COMMAND);
            msg.writeString(cmd);
            msg.sendToServer("proxy", server);
        });
    }

    /**
     * Sends a single command to a specific server
     * 
     * @param command Command to dispatch
     * @param server  The target server
     */
    private void dispatchCommandToServer(final String command, final FoundationServer server) {
        final OutgoingMessage msg = new OutgoingMessage(MineBridgeProxyMessage.DISPATCH_COMMAND);
        msg.writeString(command);
        msg.sendToServer("proxy", server);
    }
}