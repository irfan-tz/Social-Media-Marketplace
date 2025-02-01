# -WEBSITE ONLY MEANT FOR DESKTOP-
## Tech Stack

- Backend: Django (Built-in security protection against SQL injection, CSRF, and XSS)
- API: GraphQL (https://youtu.be/eIQh02xuVw4) (https://youtu.be/Zg4XIpnLWQg) 
- Frontend: React.js
- Database: PostgreSQL 
- Chat and Realtime:- Django Channels (For WebSocket-based real-time chat features), Redis (For handling WebSocket connections and message queues)
- Web Server: Nginx (for reverse proxy and to serve static files) (https://youtu.be/JKxlsvZXG7c) (https://youtu.be/9nyiY-psbMs) (https://youtu.be/q8OleYuqntY **IMPORTANT**)

## Security 

- Authentication and Security: 
	- JWT (JSON Web Tokens) or **OAuth2**: user authentication. 
	- **password hashing** using Django's `PBKDF2` or `Argon2`.
	- Use Django's CSRF protection and XSS safeguards.
	- HTTPS with **Let's Encrypt** for free SSL/TLS certificates.
- **libsodium** (via PyNaCl in Python) for implementing E2EE for chats. (Keys can be generated and stored on the client-side (browser) for true encryption, might look for other implementation)
- Sanitize inputs using libraries like **DOMPurify**.
- Set Content Security Policy (CSP) headers.

- When recieving from client, change timestamp to of server's.

# Future Implementation
## Firewall:
- Hide all other ports from public, show only port 443 (https)

## File Permission:
- Make sure appropriate user permission to nginx.conf

## Resources:

What to understand first and then what:
Nginx -> Django -> (Not sequential but preferrably PostgreSQL) -> GraphQL -> React

SSL/TLS: https://youtu.be/hExRDVZHhig, https://youtu.be/J7fI_jH7L84
