package org.mineacademy.minebridge.core.internal;

import org.mineacademy.fo.platform.Platform;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.annotations.SerializedName;

import lombok.Getter;

/**
 * Base class for all schema objects used for WebSocket communication
 */
public abstract class BaseSchema {

    // Use ThreadLocal for better thread safety with Gson
    private static final ThreadLocal<Gson> GSON = ThreadLocal
            .withInitial(() -> new GsonBuilder().disableHtmlEscaping().create());

    // Initialize server name once at class load time
    private static final String SERVER_NAME = initServerName();

    @Getter
    @SerializedName("action")
    private final String action;

    @Getter
    @SerializedName("server")
    private final String server;

    /**
     * Creates a schema with a specified action and server name
     * 
     * @param action The action identifier
     * @param server The server name
     */
    protected BaseSchema(String action, String server) {
        this.action = action;
        this.server = server;
    }

    /**
     * Creates a schema with a specified action and the default server name
     * 
     * @param action The action identifier
     */
    protected BaseSchema(String action) {
        this(action, SERVER_NAME);
    }

    /**
     * Creates a schema with a specified action and optionally includes the server
     * name
     * 
     * @param action        The action identifier
     * @param includeServer Whether to include the server name
     */
    protected BaseSchema(String action, boolean includeServer) {
        this(action, includeServer ? SERVER_NAME : null);
    }

    /**
     * Converts this schema to a JSON string
     * 
     * @return The JSON representation
     */
    public String toJson() {
        return GSON.get().toJson(this);
    }

    /**
     * Creates a schema from a JSON string
     * 
     * @param <T>         The schema type
     * @param json        The JSON string
     * @param schemaClass The schema class
     * @return The parsed schema
     */
    public static <T extends BaseSchema> T fromJson(String json, Class<T> schemaClass) {
        return GSON.get().fromJson(json, schemaClass);
    }

    /**
     * Initializes the server name based on the platform type
     * 
     * @return The server name
     */
    private static String initServerName() {
        Platform.Type type = Platform.getType();
        return type == Platform.Type.BUKKIT ? Platform.getCustomServerName() : type.toString().toLowerCase();
    }
}