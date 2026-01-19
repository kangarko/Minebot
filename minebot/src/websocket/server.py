import asyncio
import datetime
import ipaddress
import ssl
from logging import Logger
from pathlib import Path

import websockets

from debug import get_logger
from model import WebSocketKeys
from settings import Settings

from .action_registry import action_handlers
from .listener import handle_connection

logger: Logger = get_logger(__name__)


class WebSocketServer:
    """
    Manager class for the WebSocket server.
    Handles initialization, running, and graceful shutdown of the WebSocket server.
    """

    def __init__(self) -> None:
        """
        Initialize the WebSocket manager with host and port configuration.

        Sets up the server configuration and determines if the WebSocket server
        should be enabled based on settings availability.
        """
        self.host: str | None = Settings.get(WebSocketKeys.HOST)
        self.port: int | None = Settings.get(WebSocketKeys.PORT)
        self.server = None
        self._task = None
        self._shutdown_event = asyncio.Event()
        self.ssl_context = None

        if self.host is None or self.port is None:
            logger.info("WebSocket server is disabled (host or port not set)")
            self.is_enabled = False
        else:
            self.is_enabled = True

    def generate_self_signed_cert(self):
        """
        Generate a self-signed certificate for the WebSocket server.

        Returns:
            tuple: Paths to the certificate and key files
        """
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.x509.oid import NameOID

            # Create certificate directory if it doesn't exist
            cert_path = Path("configuration/certs")
            cert_path.mkdir(parents=True, exist_ok=True)

            # Always use 'localhost' for local development certificates
            cert_name = self.host or "localhost"
            key_file = cert_path / f"{cert_name}.key"
            cert_file = cert_path / f"{cert_name}.crt"

            # Check if certificates already exist
            if key_file.exists() and cert_file.exists():
                logger.debug(f"Using existing SSL certificates in {cert_path}")
                return str(cert_file), str(key_file)

            logger.debug("Generating new self-signed SSL certificate")

            # Generate private key
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

            # Write private key to file
            with open(key_file, "wb") as f:
                f.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )

            # Subject and issuer are the same for self-signed certificates
            # Always use 'localhost' for local development
            subject = issuer = x509.Name(
                [
                    x509.NameAttribute(NameOID.COMMON_NAME, cert_name),
                    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MineBotSSL"),
                ]
            )

            # Build certificate
            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(private_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
                .not_valid_after(
                    # Valid for 1 year
                    datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
                )
                .add_extension(
                    x509.SubjectAlternativeName(
                        [
                            x509.DNSName("localhost"),
                            x509.IPAddress(ipaddress.IPv4Address(cert_name))
                            if self._is_valid_ip(cert_name)
                            else x509.DNSName(cert_name),
                        ]
                    ),
                    critical=False,
                )
                .sign(private_key, hashes.SHA256())
            )

            # Write certificate to file
            with open(cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

            logger.debug(f"Generated SSL certificates in {cert_path}")
            return str(cert_file), str(key_file)

        except ImportError:
            logger.error("Failed to create SSL certificates: cryptography package required")
            return None, None
        except Exception as e:
            logger.error(f"Failed to create SSL certificates: {e}", exc_info=True)
            return None, None

    def _is_valid_ip(self, host: str) -> bool:
        try:
            ipaddress.IPv4Address(host)
            return True
        except ipaddress.AddressValueError:
            return False

    def _setup_ssl_context(self):
        """
        Set up an SSL context for secure WebSocket connections.

        Returns:
            ssl.SSLContext or None: Configured SSL context if successful, None otherwise
        """
        try:
            # Generate or use existing self-signed certificate
            cert_file, key_file = self.generate_self_signed_cert()

            if not cert_file or not key_file:
                logger.error("SSL certificate generation failed")
                return None

            # Create and configure SSL context
            logger.debug(f"Setting up SSL context with cert: {cert_file}, key: {key_file}")
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

            # Load the certificate
            try:
                ssl_context.load_cert_chain(cert_file, key_file)
            except ssl.SSLError as e:
                logger.error(f"Failed to load SSL certificates: {e}")
                return None

            logger.debug("SSL context created successfully")
            return ssl_context

        except Exception as e:
            logger.error(f"Failed to setup SSL context: {e}", exc_info=True)
            return None

    async def start(self) -> None:
        """
        Start the WebSocket server as an asyncio task.

        Returns:
            None
        """
        if not self.is_enabled:
            return

        if self._task is not None:
            logger.warning("WebSocket server already running")
            return

        logger.info("Starting WebSocket server")

        # Import actions here to avoid circular imports
        # This triggers registration of action handlers
        try:
            logger.debug("Loading WebSocket action handlers")
            import websocket.actions.event  # noqa: F401
            import websocket.actions.request  # noqa: F401
            import websocket.actions.response  # noqa: F401

            # Keep this as info since it's a summary of handlers
            logger.info(
                f"Starting WebSocket server with {len(action_handlers)} registered action handlers"
            )
        except Exception as e:
            logger.error(f"Failed to load WebSocket action handlers: {e}", exc_info=True)
            return

        self.ssl_context = self._setup_ssl_context()
        if not self.ssl_context:
            logger.error("SSL context setup failed, WebSocket server will not start")
            return
        self._task = asyncio.create_task(self._run_server())

    async def _run_server(self) -> None:
        """
        Internal method that runs the actual server.

        Returns:
            None
        """
        try:
            if not self.ssl_context:
                logger.error("Cannot start WebSocket server without SSL context")
                return

            try:
                self.server = await websockets.serve(
                    handle_connection,
                    self.host,
                    self.port,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=5,
                    ssl=self.ssl_context,
                )
            except Exception as e:
                logger.error(f"Failed to start WebSocket server: {e}", exc_info=True)
                return

            logger.info(f"WebSocket server started on wss://{self.host}:{self.port}")

            # Run until shutdown event is set
            await self._shutdown_event.wait()

        except OSError as e:
            logger.critical(f"Failed to start WebSocket server: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error in WebSocket server: {e}", exc_info=True)
            raise

    async def stop(self) -> None:
        """
        Stop the WebSocket server gracefully.

        Returns:
            None
        """
        if not self.is_enabled or not self._task:
            return

        if not self._task:
            return

        logger.info("Shutting down WebSocket server")

        # Signal the server to stop
        self._shutdown_event.set()

        # Close the server if it exists
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Cancel the task if it's running
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                logger.warning("Forced WebSocket server task cancellation")
            finally:
                self._task = None
                self.server = None
                self._shutdown_event.clear()
                logger.info("WebSocket server shutdown complete")
