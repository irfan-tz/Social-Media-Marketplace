# -WEBSITE ONLY MEANT FOR DESKTOP-
## Tech Stack

- Backend: Django
- Frontend: React.js
- Database: PostgreSQL
- Chat and Realtime:- Django Channels (For WebSocket-based real-time chat features), Redis (For handling WebSocket connections and message queues)
- Web Server: Nginx (for reverse proxy and to serve static files)
## Security 

- Authentication and Security: 
	- JWT (JSON Web Tokens) or **OAuth2**: user authentication. 
	- **password hashing** using Django's `PBKDF2` or `Argon2`.
	- Use Django's CSRF protection and XSS safeguards.
	- HTTPS with **Let's Encrypt** for free SSL/TLS certificates.
- **libsodium** (via PyNaCl in Python) for implementing E2EE for chats. (Keys can be generated and stored on the client-side (browser) for true encryption, might look for other implementation)
- Sanitize inputs using libraries like **DOMPurify**.
- Set Content Security Policy (CSP) headers.

