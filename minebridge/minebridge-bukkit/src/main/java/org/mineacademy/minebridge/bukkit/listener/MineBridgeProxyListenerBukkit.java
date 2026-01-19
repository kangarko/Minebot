package org.mineacademy.minebridge.bukkit.listener;

import org.mineacademy.fo.platform.Platform;
import org.mineacademy.fo.proxy.ProxyListener;
import org.mineacademy.fo.proxy.message.IncomingMessage;
import org.mineacademy.minebridge.core.model.MineBridgeProxyMessage;
import org.mineacademy.minebridge.core.model.ProxyConstants;

import lombok.Getter;

@SuppressWarnings("unused")
public final class MineBridgeProxyListenerBukkit extends ProxyListener {

    @Getter
    private static final MineBridgeProxyListenerBukkit instance = new MineBridgeProxyListenerBukkit();

    private MineBridgeProxyMessage packet;

    private String server;

    private MineBridgeProxyListenerBukkit() {
        super(ProxyConstants.MINEBRIDGE_CHANNEL, MineBridgeProxyMessage.class);
    }

    @Override
    public void onMessageReceived(IncomingMessage input) {
        this.packet = (MineBridgeProxyMessage) input.getMessage();

        if (this.packet == MineBridgeProxyMessage.DISPATCH_COMMAND)
            Platform.dispatchConsoleCommand(null, input.readString());
    }
}
