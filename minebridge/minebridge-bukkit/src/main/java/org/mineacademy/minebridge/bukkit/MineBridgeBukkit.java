package org.mineacademy.minebridge.bukkit;

import java.io.File;
import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.file.Files;
import java.util.Properties;

import org.mineacademy.fo.Common;
import org.mineacademy.fo.MinecraftVersion;
import org.mineacademy.fo.MinecraftVersion.V;
import org.mineacademy.fo.exception.FoException;
import org.mineacademy.fo.platform.BukkitPlugin;
import org.mineacademy.fo.platform.Platform;
import org.mineacademy.minebridge.bukkit.actions.CommandActionHandler;
import org.mineacademy.minebridge.bukkit.actions.MessageActionHandler;
import org.mineacademy.minebridge.bukkit.actions.PlayerActionHandler;
import org.mineacademy.minebridge.bukkit.listener.CommandListenerBukkit;
import org.mineacademy.minebridge.bukkit.model.ServerType;
import org.mineacademy.minebridge.core.settings.Settings;
import org.mineacademy.minebridge.core.websocket.Client;

import lombok.Getter;

public final class MineBridgeBukkit extends BukkitPlugin {

	private Client webSocketClient;

	@Getter
	private static ServerType serverType;

	@Override
	public String[] getStartupLogo() {
		return new String[] {
				"&c  __  __ _____ _   _ ______ ____  _____  _____ _____   _____ ______ ",
				"&4 |  \\/  |_   _| \\ | |  ____|  _ \\|  __ \\|_   _|  __ \\ / ____|  ____|",
				"&4 | \\  / | | | |  \\| | |__  | |_) | |__) | | | | |  | | |  __| |__   ",
				"&4 | |\\/| | | | | . ` |  __| |  _ <|  _  /  | | | |  | | | |_ |  __|  ",
				"&4 | |  | |_| |_| |\\  | |____| |_) | | \\ \\ _| |_| |__| | |__| | |____ ",
				"&4 |_|  |_|_____|_| \\_|______|____/|_|  \\_\\_____|_____/ \\_____|______|",
				"&0                                                                    ",
		};
	}

	@Override
	protected void onPluginPreStart() {
		parseServerName();
		parseServerType();
	}

	@Override
	protected void onPluginStart() {
		if (serverType.equals(ServerType.STANDALONE)) {
			try {
				// Create WebSocket client
				webSocketClient = new Client(
						Settings.WebSocket.HOST,
						Settings.WebSocket.PORT,
						Settings.WebSocket.PASSWORD,
						new String[] { Platform.getCustomServerName() },
						getDataFolder());

				// Register handler classes with WebSocketAction annotations
				webSocketClient.registerActionHandler(new PlayerActionHandler(), new MessageActionHandler(),
						new CommandActionHandler());

				// Connect to the WebSocket server
				webSocketClient.connect();

				// Register command listeners
				registerEvents(new CommandListenerBukkit(webSocketClient));

				Common.log("Client started and connected successfully");
			} catch (URISyntaxException e) {
				Common.error(e, "Failed to create client: " + e.getMessage());
			}
		} else {
			Common.log("Server is running in proxied mode.");
		}
	}

	@Override
	protected void onPluginStop() {
		// Close the WebSocket connection when the plugin is disabled
		if (webSocketClient != null && webSocketClient.isOpen()) {
			webSocketClient.close();
			Common.log("Client connection closed");
		}
	}

	/**
	 * Parses the server name from the server.properties file.
	 * The server name is read from the "server-name" property.
	 * 
	 * @throws FoException if the server name is not found or empty in the
	 *                     server.properties file
	 */
	private void parseServerName() {
		final File serverProperties = new File("server.properties");
		final Properties properties = new Properties();

		try {
			properties.load(Files.newInputStream(serverProperties.toPath()));
		} catch (final IOException ex) {
			Common.error(ex, "Failed to load server.properties file: " + ex.getMessage());
		}

		final String name = properties.getProperty("server-name");

		if (name == null || name.isEmpty()) {
			Common.throwError(new FoException("Server name not found in server.properties"));
		}

		if ("all".equals(name))
			Common.throwError(new FoException("Server name cannot be 'all'"));

		Platform.setCustomServerName(name);
	}

	/**
	 * Detects and sets the server type based on the server's configuration files.
	 * 
	 * This method examines spigot.yml and paper-global.yml/paper.yml (depending on
	 * Minecraft version)
	 * to determine if the server is configured to work with a proxy like BungeeCord
	 * or Velocity.
	 * 
	 * If proxy support is enabled in either configuration file, the server type is
	 * set to PROXIED.
	 * Otherwise, it defaults to STANDALONE.
	 * 
	 * @see ServerType
	 */
	private void parseServerType() {
		final File spigotFile = new File("spigot.yml");
		File paperFile = null;
		final Properties spigotProperties = new Properties();
		final Properties paperProperties = new Properties();

		// Determine the Paper config file path based on Minecraft version
		if (MinecraftVersion.atLeast(V.v1_18)) {
			paperFile = new File("config/paper-global.yml");
		} else if (MinecraftVersion.atLeast(V.v1_13)) {
			paperFile = new File("paper.yml");
		}

		try {
			// Load Spigot configuration if it exists
			if (spigotFile.exists()) {
				spigotProperties.load(Files.newInputStream(spigotFile.toPath()));
			}

			// Load Paper configuration if it exists
			if (paperFile != null && paperFile.exists()) {
				paperProperties.load(Files.newInputStream(paperFile.toPath()));
			}
		} catch (final IOException ex) {
			Common.error(ex, "Failed to load server configuration files: " + ex.getMessage());
		}

		// Check if Velocity or BungeeCord proxy support is enabled in configs
		final String velocity = paperFile != null ? paperProperties.getProperty("proxies.velocity") : null;
		final String bungeecord = spigotProperties.getProperty("bungeecord");

		// Set server type to PROXIED if either Velocity or BungeeCord is enabled
		if ("true".equalsIgnoreCase(velocity) || "true".equalsIgnoreCase(bungeecord)) {
			serverType = ServerType.PROXIED;
			return;
		}

		// Default to STANDALONE if no proxy support is configured
		serverType = ServerType.STANDALONE;
	}
}
