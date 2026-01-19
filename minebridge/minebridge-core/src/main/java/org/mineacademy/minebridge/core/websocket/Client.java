package org.mineacademy.minebridge.core.websocket;

import java.io.File;
import java.io.FileInputStream;
import java.net.URI;
import java.net.URISyntaxException;
import java.security.KeyStore;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManagerFactory;

import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.mineacademy.fo.CommonCore;
import org.mineacademy.fo.debug.Debugger;

import com.google.gson.JsonObject;

public class Client extends WebSocketClient {

    private final WebSocketActionHandler actionHandler;
    private final String host;
    private final String password;
    private final String[] server_list;
    private final File data_folder;

    // Static executor for all reconnection attempts
    private static final ScheduledExecutorService reconnectExecutor = Executors.newSingleThreadScheduledExecutor(r -> {
        Thread thread = new Thread(r, "WebSocket-Reconnect-Thread");
        thread.setDaemon(true);
        return thread;
    });

    // Flag to track if reconnection is in progress
    private final AtomicBoolean reconnecting = new AtomicBoolean(false);

    /**
     * Creates a new WebSocket client with SSL certificate path
     * 
     * @param serverUri   The server URI to connect to
     * @param password    The password for authentication
     * @param server_list The list of servers to register with
     * @param dataFolder  Path to plugin data folder
     * @throws URISyntaxException If the URI syntax is invalid
     */
    public Client(String host, Integer port, String password, String[] server_list, File data_folder)
            throws URISyntaxException {
        super(new URI("wss://" + host + ":" + port));

        this.actionHandler = new WebSocketActionHandler();
        this.actionHandler.setClient(this);
        this.host = host;
        this.password = password;
        this.server_list = server_list;
        this.data_folder = data_folder;

        try {
            setupSSL();
        } catch (Exception e) {
            CommonCore.error(e, "Failed to set up SSL context: " + e.getMessage());
        }
    }

    /**
     * Sets up SSL context with the provided certificate path
     * If the path is a directory, it will search for .crt files
     */
    private void setupSSL() throws Exception {

        // Ensure the certs directory exists
        File certsDir = new File(data_folder, "certs");
        if (!certsDir.exists()) {
            certsDir.mkdirs();
            Debugger.debug("websocket", "Created certificates directory: " + certsDir.getAbsolutePath());
        }

        String actualCertPath = certsDir.getAbsolutePath() + File.separator + host + ".crt";

        // Create a KeyStore containing our trusted CAs
        KeyStore keyStore = KeyStore.getInstance(KeyStore.getDefaultType());
        keyStore.load(null, null);

        // Load the certificate
        CertificateFactory cf = CertificateFactory.getInstance("X.509");
        try (FileInputStream fis = new FileInputStream(actualCertPath)) {
            X509Certificate cert = (X509Certificate) cf.generateCertificate(fis);
            keyStore.setCertificateEntry("ca", cert);
        }

        // Create a TrustManager that trusts the CAs in our KeyStore
        TrustManagerFactory tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        tmf.init(keyStore);

        // Create an SSLContext that uses our TrustManager
        SSLContext sslContext = SSLContext.getInstance("TLS");
        sslContext.init(null, tmf.getTrustManagers(), null);

        // Set the SSLContext to the WebSocketClient
        this.setSocketFactory(sslContext.getSocketFactory());
        Debugger.debug("websocket", "SSL context initialized with certificate: " + actualCertPath);
    }

    @Override
    public void onOpen(ServerHandshake handshakedata) {
        Debugger.debug("websocket", "Opened connection to server: " + getURI());
        this.authenticate(password, server_list);
    }

    @Override
    public void onMessage(String message) {
        Debugger.debug("websocket", "Received message: " + message);

        if (!actionHandler.handleMessage(message)) {
            Debugger.debug("websocket", "No handler found for message: " + message);
        }
    }

    @Override
    public void onClose(int code, String reason, boolean remote) {
        Debugger.debug("websocket", "Closed connection: " + reason);

        // Don't attempt to reconnect if we're already trying
        if (!reconnecting.compareAndSet(false, true)) {
            Debugger.debug("websocket", "Reconnection already in progress, skipping new attempt");
            return;
        }

        final AtomicInteger attemptCount = new AtomicInteger(0);
        final int maxAttempts = 10; // Set a reasonable maximum attempts
        final long initialDelayMs = 5000; // Start with 5 seconds
        final long maxDelayMs = 60000; // Cap at 1 minute

        // Schedule reconnection with exponential backoff
        Runnable reconnectTask = new Runnable() {
            @Override
            public void run() {
                int currentAttempt = attemptCount.incrementAndGet();

                try {
                    if (currentAttempt > maxAttempts) {
                        Debugger.debug("websocket",
                                "Maximum reconnection attempts (" + maxAttempts + ") reached. Giving up.");
                        reconnecting.set(false);
                        return;
                    }

                    Debugger.debug("websocket", "Attempting to reconnect... (Attempt " + currentAttempt + ")");

                    // Check if we're already connected somehow
                    if (Client.this.isOpen()) {
                        Debugger.debug("websocket", "Connection is already open, canceling reconnection attempts");
                        reconnecting.set(false);
                        return;
                    }

                    // Attempt to reconnect
                    boolean reconnected = Client.this.reconnectBlocking();

                    if (reconnected) {
                        Debugger.debug("websocket", "Reconnected successfully after " + currentAttempt + " attempts.");
                        reconnecting.set(false);
                    } else {
                        // Calculate next delay with exponential backoff and jitter
                        long baseDelay = Math.min(maxDelayMs,
                                initialDelayMs * (1L << Math.min(currentAttempt - 1, 30)));
                        long jitter = (long) (baseDelay * 0.2 * Math.random()); // 20% jitter
                        long nextDelayMs = baseDelay + jitter;

                        Debugger.debug("websocket", "Reconnection attempt " + currentAttempt +
                                " failed. Trying again in " + (nextDelayMs / 1000) + " seconds...");

                        // Schedule next attempt
                        reconnectExecutor.schedule(this, nextDelayMs, TimeUnit.MILLISECONDS);
                    }
                } catch (Exception e) {
                    long nextDelayMs = Math.min(maxDelayMs, initialDelayMs * (1L << Math.min(currentAttempt - 1, 30)));
                    Debugger.debug("websocket", "Error during reconnection attempt: " + e.getMessage() +
                            ". Trying again in " + (nextDelayMs / 1000) + " seconds...");

                    // Schedule next attempt despite error
                    reconnectExecutor.schedule(this, nextDelayMs, TimeUnit.MILLISECONDS);
                }
            }
        };

        // Start the first attempt with initial delay
        reconnectExecutor.schedule(reconnectTask, initialDelayMs, TimeUnit.MILLISECONDS);
    }

    @Override
    public void onError(Exception ex) {
        CommonCore.error(ex, "WebSocket error: " + ex.getMessage());
    }

    public void authenticate(String password, String[] server_list) {
        JsonObject jsonObject = new JsonObject();
        jsonObject.addProperty("action", "authenticate");
        jsonObject.addProperty("password", password);

        // Convert String array to JSON array
        com.google.gson.JsonArray serverArray = new com.google.gson.JsonArray();
        for (String server : server_list) {
            serverArray.add(new com.google.gson.JsonPrimitive(server));
        }
        jsonObject.add("server_list", serverArray);

        this.send(jsonObject.toString());
    }

    /**
     * Register a class containing methods annotated with
     * {@link org.mineacademy.minebridge.annotation.WebSocketAction}
     * 
     * @param instance The instance of the class containing annotated methods
     */
    public void registerActionHandler(Object instance) {
        actionHandler.registerClass(instance);
    }

    /**
     * Register multiple action handler classes at once
     * 
     * @param instances Array of instances containing annotated methods
     */
    public void registerActionHandler(Object... instances) {
        for (Object instance : instances) {
            actionHandler.registerClass(instance);
        }
        Debugger.debug("websocket", "Registered " + instances.length + " action handlers");
    }
}
