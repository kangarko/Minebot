package org.mineacademy.minebridge.core.model;

import org.mineacademy.fo.proxy.ProxyMessage;

import lombok.Getter;

public enum MineBridgeProxyMessage implements ProxyMessage {

    DISPATCH_COMMAND(
            String.class // Command
    );

    @Getter
    private final Class<?>[] content;

    MineBridgeProxyMessage(Class<?>... validValues) {
        this.content = validValues;
    }

}
