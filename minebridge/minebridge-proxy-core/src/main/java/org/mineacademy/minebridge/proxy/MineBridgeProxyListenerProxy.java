package org.mineacademy.minebridge.proxy;

import org.mineacademy.fo.CommonCore;
import org.mineacademy.fo.annotation.AutoRegister;
import org.mineacademy.fo.platform.Platform;
import org.mineacademy.fo.proxy.ProxyListener;
import org.mineacademy.fo.proxy.message.IncomingMessage;
import org.mineacademy.minebridge.core.model.MineBridgeProxyMessage;
import org.mineacademy.minebridge.core.model.ProxyConstants;

import lombok.Getter;

@SuppressWarnings("unused")
@AutoRegister(requirePlatform = { Platform.Type.BUNGEECORD, Platform.Type.VELOCITY })
public final class MineBridgeProxyListenerProxy extends ProxyListener {

    private String action;

    @Getter
    private static final MineBridgeProxyListenerProxy instance = new MineBridgeProxyListenerProxy();

    private MineBridgeProxyListenerProxy() {
        super(ProxyConstants.MINEBRIDGE_CHANNEL, MineBridgeProxyMessage.class);
    }

    @Override
    public void onMessageReceived(IncomingMessage message) {
        try {
            final byte[] data = message.getData();

            final MineBridgeProxyMessage packet = (MineBridgeProxyMessage) message.getMessage();

            /*
             * if (packet == MineBridgeProxyMessage.TEST) {
             * final String text = message.readString();
             * CommonCore.log("Received message: " + text);
             * }
             */

        } catch (final Throwable t) {
            CommonCore.error(t, "Error while processing message");
        }
    }

}
