import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const hmrHost = process.env.HMR_HOST || "localhost";
const isProd = process.env.NODE_ENV === "production";

// Create a plugin to disable React DevTools in production
const disableReactDevTools = {
    name: "disable-react-devtools",
    transformIndexHtml(html) {
        if (isProd) {
            return {
                html,
                tags: [
                    {
                        tag: "script",
                        injectTo: "head",
                        children: `
              if (typeof window.__REACT_DEVTOOLS_GLOBAL_HOOK__ === 'object') {
                window.__REACT_DEVTOOLS_GLOBAL_HOOK__.inject = function() {};
              }
            `,
                    },
                ],
            };
        }
    },
};

const securityHeaders = {
    name: 'security-headers',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        // Apply CSP in both dev and production
        res.setHeader("Content-Security-Policy", "default-src 'self'; script-src 'self'");
        // Add other security headers
        res.setHeader("X-Content-Type-Options", "nosniff");
        res.setHeader("X-Frame-Options", "DENY");
        res.setHeader("X-XSS-Protection", "1; mode=block");
        next();
      });
    }
};

const clientErrorHandler = {
    name: "client-error-handler",
    configureServer(server) {
        // Attach error handler to catch 'clientError' events
        server.httpServer.on("clientError", (err, socket) => {
            console.error("Client error:", err);
            // Send a basic HTTP error response and destroy the socket
            socket.end("HTTP/1.1 400 Bad Request\r\n\r\n");
            socket.destroy();
        });
    },
};

export default defineConfig({
    build: {
        sourcemap: false, // Disable source maps in all environments
    },
    plugins: [
        react(),
        disableReactDevTools,
        securityHeaders,
        clientErrorHandler,
    ],
    server: {
        port: 8080,
        https: true, // Use HTTPS for local development
        host: isProd ? "localhost" : "0.0.0.0", // Only expose to all interfaces in dev
        hmr: {
            protocol: "wss", // Use WSS for secure HMR
            host: hmrHost,
        },
        proxy: {
            "/api": {
                target: "http://backend:8000", // Match the Docker network alias
                changeOrigin: true,
                secure: false,
            },
            "/ws": {
                target: "ws://backend:8000",
                ws: true,
                secure: false,
                rewrite: (path) => path, // Pass through as-is
            },
        },
    },
});