package org.mineacademy.minebridge.core.model;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;

@NoArgsConstructor(access = AccessLevel.PRIVATE)
public final class ProxyConstants {

    /**
     * The default channel we are broadcasting, legacy format.
     */
    public static final String BUNGEECORD_CHANNEL = "BungeeCord";

    /**
     * The channel we are broadcasting at, new format.
     */
    public static final String MINEBRIDGE_CHANNEL = "plugin:minebridge";
}
