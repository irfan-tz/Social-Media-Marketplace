import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { useNavigate, useLocation, Navigate } from "react-router-dom";
import "@fortawesome/fontawesome-free/css/all.min.css";
import "../assets/styles/Messaging.css";

export default function Messaging() {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState("");
    const [attachment, setAttachment] = useState(null);
    const [receiverId, setReceiverId] = useState("");
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { user, loading: authLoading } = useAuth();
    const messageListRef = useRef(null);
    const navigate = useNavigate();
    const location = useLocation();
    const [friendRequests, setFriendRequests] = useState([]);

    // Safe user data access
    const socketRef = useRef(null);
    const currentUserId = user?.user_id;
    const dataFetchedRef = useRef(false);

    // Maximum allowed message length
    const MAX_MESSAGE_LENGTH = 5000;

    // Data fetching effect
    useEffect(() => {
        if (authLoading || !user || !user.user_id) {
            return;
        }

        // Prevent duplicate fetches
        if (dataFetchedRef.current) return;

        const fetchData = async () => {
            try {
                setLoading(true);

                const [usersResponse, messagesResponse, requestsResponse] =
                    await Promise.all([
                        axios.get("/api/users/", {
                            withCredentials: true,
                        }),
                        axios.get("/api/messages/", {
                            withCredentials: true,
                        }),
                        axios.get("/api/friendships/", {
                            withCredentials: true,
                        }),
                    ]);

                setUsers(usersResponse.data);
                setMessages(messagesResponse.data);
                setFriendRequests(requestsResponse.data);
                dataFetchedRef.current = true;

                if (location.state?.username) {
                    const targetUser = usersResponse.data.find(
                        (u) => u.username === location.state.username,
                    );
                    if (targetUser) setReceiverId(targetUser.id);
                }
            } catch (err) {
                setError(err.response?.data?.detail || "Failed to load data");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [user, authLoading, location.state]);

    // WebSocket connection for real-time messages
    useEffect(() => {
        if (authLoading || !user || !user.user_id) {
            return;
        }

        // Close any existing connection
        if (socketRef.current) {
            // Clear ping interval if it exists
            if (socketRef.current.pingInterval) {
                clearInterval(socketRef.current.pingInterval);
            }
            socketRef.current.close();
        }

        // Determine WebSocket protocol based on whether page is served over HTTPS
        const wsProtocol =
            window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/messages/`;

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            // Set up ping interval to keep connection alive
            const pingInterval = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: "ping" }));
                } else {
                    clearInterval(pingInterval);
                }
            }, 30000); // Send ping every 30 seconds

            // Store the interval ID for cleanup
            ws.pingInterval = pingInterval;
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                // Handle ping messages
                if (data.type === "ping") {
                    ws.send(JSON.stringify({ type: "pong" }));
                    return;
                }

                // Handle new message or attachment notification
                if (
                    data.type === "new_message" ||
                    data.type === "chat_message" ||
                    data.type === "new_attachment"
                ) {
                    // For attachment notifications, we need to fetch the complete message
                    if (data.type === "new_attachment") {
                        // Fetch the complete message with attachment data
                        axios
                            .get(`/api/messages/${data.message.id}/`, {
                                withCredentials: true,
                            })
                            .then((response) => {
                                // Add the full message to state
                                setMessages((prevMessages) => {
                                    // Check if the message already exists
                                    const exists = prevMessages.some(
                                        (msg) => msg.id === response.data.id,
                                    );
                                    if (exists) return prevMessages;

                                    // Add the message
                                    return [...prevMessages, response.data];
                                });

                                // Auto-scroll
                                if (messageListRef.current) {
                                    messageListRef.current.scrollTop =
                                        messageListRef.current.scrollHeight;
                                }
                            })
                            .catch((error) => {
                                console.error(
                                    "Error fetching attachment message:",
                                    error,
                                );
                            });

                        return;
                    }

                    // Normal message handling
                    setMessages((prevMessages) => {
                        // Check if message already exists (including temporary messages)
                        const existingIndex = prevMessages.findIndex(
                            (msg) =>
                                msg.id === data.message.id ||
                                (msg.isTempMessage &&
                                    msg.sender === data.message.sender_id &&
                                    msg.receiver === data.message.receiver_id &&
                                    msg.decrypted_content ===
                                        data.message.content),
                        );

                        if (existingIndex >= 0) {
                            // Replace temporary message with real one
                            const newMessages = [...prevMessages];
                            newMessages[existingIndex] = {
                                id: data.message.id,
                                sender: data.message.sender_id,
                                sender_username: data.message.sender_username,
                                receiver: data.message.receiver_id,
                                decrypted_content: data.message.content,
                                timestamp: data.message.timestamp,
                            };
                            return newMessages;
                        }

                        // Otherwise add as new message
                        return [
                            ...prevMessages,
                            {
                                id: data.message.id,
                                sender: data.message.sender_id,
                                sender_username: data.message.sender_username,
                                receiver: data.message.receiver_id,
                                decrypted_content: data.message.content,
                                timestamp: data.message.timestamp,
                            },
                        ];
                    });

                    // Auto-scroll to new message
                    if (messageListRef.current) {
                        messageListRef.current.scrollTop =
                            messageListRef.current.scrollHeight;
                    }
                } else if (data.type === "error") {
                    setError(data.message);
                }
            } catch (error) {
                console.error(
                    "Error handling WebSocket message:",
                    error,
                    event.data,
                );
            }
        };

        ws.onerror = (error) => {
            console.error("WebSocket error:", error);
            setError("WebSocket connection error");
        };

        ws.onclose = () => {
            if (ws.pingInterval) {
                clearInterval(ws.pingInterval);
            }
        };

        socketRef.current = ws;

        return () => {
            if (ws.pingInterval) {
                clearInterval(ws.pingInterval);
            }
            ws.close();
        };
    }, [user, authLoading]);

    // Auto-scroll when new messages arrive or when switching conversations
    useEffect(() => {
        if (messageListRef.current) {
            messageListRef.current.scrollTop =
                messageListRef.current.scrollHeight;
        }
    }, [messages, receiverId]);

    // Send message function
    const sendMessage = async (e) => {
        e.preventDefault();
        if (!receiverId || (!newMessage.trim() && !attachment)) {
            setError("Select a receiver and add content");
            return;
        }

        // Validate message length
        if (newMessage.length > MAX_MESSAGE_LENGTH) {
            setError(
                `Message is too long (maximum ${MAX_MESSAGE_LENGTH} characters)`,
            );
            return;
        }

        try {
            const selectedUser = users?.find((u) => u.id === receiverId);
            if (selectedUser?.friendship_status?.status !== "accepted") {
                setError("You must be friends to message");
                return;
            }

            const messageContent = newMessage.trim();

            // Handle file attachments
            if (attachment) {
                setLoading(true);

                // Create a temp message with attachment preview
                const tempFileId = `temp-file-${Date.now()}`;
                const tempAttachmentUrl = URL.createObjectURL(attachment);

                // Create a placeholder message to show immediately
                const tempMessage = {
                    id: `temp-${Date.now()}`,
                    sender: currentUserId,
                    sender_username: user.username,
                    receiver: receiverId,
                    decrypted_content: messageContent, // Show text part immediately
                    attachment_url: tempAttachmentUrl, // Show local preview
                    attachment_content_type: attachment.type,
                    timestamp: new Date().toISOString(),
                    isTempMessage: true,
                };

                // Add to UI immediately (optimistic update)
                setMessages((prev) => [...prev, tempMessage]);

                // Scroll to the new message
                if (messageListRef.current) {
                    setTimeout(() => {
                        messageListRef.current.scrollTop =
                            messageListRef.current.scrollHeight;
                    }, 50);
                }

                // Send via API since WebSockets aren't ideal for files
                const formData = new FormData();
                formData.append("receiver", receiverId);
                if (messageContent) {
                    formData.append("content", messageContent);
                }
                formData.append("attachment", attachment);

                const response = await axios.post("/api/messages/", formData, {
                    withCredentials: true,
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                });

                // Replace the temp message with the real one from the response
                if (response.data) {
                    setMessages((prev) =>
                        prev.map((msg) =>
                            msg.id === tempMessage.id ? response.data : msg,
                        ),
                    );

                    // Clean up the temporary URL
                    URL.revokeObjectURL(tempAttachmentUrl);
                }
            }
            // Send text messages via WebSocket
            else if (messageContent) {
                // Create a placeholder message to show immediately
                const tempMessage = {
                    id: `temp-${Date.now()}`,
                    sender: currentUserId,
                    sender_username: user.username,
                    receiver: receiverId,
                    decrypted_content: messageContent,
                    timestamp: new Date().toISOString(),
                    isTempMessage: true,
                };

                // Add to UI immediately (optimistic update)
                setMessages((prev) => [...prev, tempMessage]);

                // If WebSocket is connected
                if (
                    socketRef.current &&
                    socketRef.current.readyState === WebSocket.OPEN
                ) {
                    socketRef.current.send(
                        JSON.stringify({
                            type: "chat_message",
                            receiver_id: receiverId,
                            message: messageContent,
                        }),
                    );
                } else {
                    // Fallback to API if WebSocket isn't available
                    const formData = new FormData();
                    formData.append("receiver", receiverId);
                    formData.append("content", messageContent);

                    await axios.post("/api/messages/", formData, {
                        withCredentials: true,
                        headers: {
                            "Content-Type": "multipart/form-data",
                        },
                    });
                }

                // Scroll to bottom
                if (messageListRef.current) {
                    setTimeout(() => {
                        messageListRef.current.scrollTop =
                            messageListRef.current.scrollHeight;
                    }, 50);
                }
            }

            setNewMessage("");
            setAttachment(null);
            const fileInput = document.getElementById("attachmentInput");
            if (fileInput) fileInput.value = "";
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to send message");
        } finally {
            setLoading(false);
        }
    };

    // Friendship handlers
    const sendFriendRequest = async (receiverId) => {
        try {
            await axios.post(
                "/api/friendships/",
                { receiver: receiverId },
                { withCredentials: true },
            );
            const updatedUsers = users.map((u) =>
                u.id === receiverId
                    ? {
                          ...u,
                          friendship_status: {
                              status: "pending",
                              is_sender: true,
                          },
                      }
                    : u,
            );
            setUsers(updatedUsers);
        } catch (err) {
            setError(
                err.response?.data?.detail || "Failed to send friend request",
            );
        }
    };

    const handleAcceptRequest = async (friendId) => {
        try {
            // Find the pending request
            const response = await axios.get(
                `/api/friendships/?receiver=${user.user_id}&sender=${friendId}&status=pending`,
                { withCredentials: true },
            );
            const request = response.data[0]; // Get first matching request

            if (!request) {
                setError("No pending request found");
                return;
            }

            // Send accept request
            await axios.post(
                `/api/friendships/${request.id}/accept/`,
                {},
                {
                    withCredentials: true,
                },
            );

            // Update UI
            setUsers(
                users.map((u) =>
                    u.id === friendId
                        ? { ...u, friendship_status: { status: "accepted" } }
                        : u,
                ),
            );
        } catch (err) {
            setError(err.response?.data?.error || "Failed to accept request");
        }
    };

    const handleRejectRequest = async (friendId) => {
        try {
            // Find the pending request
            const response = await axios.get(
                `/api/friendships/?receiver=${user.user_id}&sender=${friendId}&status=pending`,
                { withCredentials: true },
            );
            const request = response.data[0];

            if (!request) {
                setError("No pending request found");
                return;
            }

            // Send reject request
            await axios.post(
                `/api/friendships/${request.id}/reject/`,
                {},
                {
                    withCredentials: true,
                },
            );

            // Update UI
            setUsers(
                users.map((u) =>
                    u.id === friendId ? { ...u, friendship_status: null } : u,
                ),
            );
        } catch (err) {
            setError(err.response?.data?.error || "Failed to reject request");
        }
    };

    const renderAttachment = (msg) => {
        if (!msg.attachment_url) return null;

        try {
            const contentType = msg.attachment_content_type;

            if (contentType?.startsWith("video/")) {
                return (
                    <div className="video-wrapper">
                        <video controls>
                            <source
                                src={msg.attachment_url}
                                type={contentType}
                            />
                            Your browser does not support the video tag.
                        </video>
                    </div>
                );
            }
            if (contentType?.startsWith("image/")) {
                return (
                    <img
                        src={msg.attachment_url}
                        alt="attachment"
                        className="message-attachment"
                        onError={(e) => {
                            console.error("Image failed to load:", e);
                            e.target.src =
                                "https://via.placeholder.com/200x200?text=Image+Error";
                            e.target.alt = "Error loading image";
                        }}
                    />
                );
            }
            return <p>Unsupported attachment type.</p>;
        } catch (error) {
            console.error("Error rendering attachment:", error);
            return <p>Error displaying attachment</p>;
        }
    };

    const handleAttachmentChange = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const allowedTypes = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "video/mp4",
        ];
        const maxSize = 10 * 1024 * 1024;

        if (!allowedTypes.includes(file.type)) {
            setError("Only images and videos are allowed");
            e.target.value = "";
            return;
        }
        if (file.size > maxSize) {
            setError("File size must be under 10MB");
            e.target.value = "";
            return;
        }
        setAttachment(file);
        setError(null);
    };

    const isCurrentUserSender = (message) =>
        message.sender === currentUserId ||
        message.sender_username === user?.username;

    // Authentication handling
    if (authLoading) {
        return (
            <div className="page-container">
                <div className="loading-overlay">
                    <div className="loading-spinner"></div>
                    <p>Authenticating...</p>
                </div>
            </div>
        );
    }

    // If auth is complete but no user, redirect to login
    if (!user) {
        return <Navigate to="/login" replace />;
    }

    // Data initialization
    const selectedUser = users?.find((u) => u.id === receiverId) || null;
    const filteredMessages =
        messages
            ?.filter(
                (msg) =>
                    (msg.sender === currentUserId &&
                        msg.receiver === receiverId) ||
                    (msg.sender === receiverId &&
                        msg.receiver === currentUserId),
            )
            ?.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)) ||
        [];
    const filteredUsers = users?.filter((u) => u.id !== currentUserId) || [];

    return (
        <div className="page-container">
            <div className="messaging-wrapper">
                {error && <div className="error-message">{error}</div>}
                {loading && <div className="loading-overlay">Loading...</div>}

                <div className="chat-sidebar">
                    <h2>Contacts</h2>
                    <div className="chat-list">
                        {filteredUsers.length === 0 && !loading ? (
                            <div className="no-contacts">
                                <p>No contacts found</p>
                            </div>
                        ) : (
                            filteredUsers.map((contact) => (
                                <div
                                    key={contact.id}
                                    className={`chat-item ${receiverId === contact.id ? "active" : ""}`}
                                >
                                    <div
                                        className="chat-avatar-wrapper"
                                        onClick={() =>
                                            setReceiverId(contact.id)
                                        }
                                    >
                                        <img
                                            src={
                                                contact.profile_picture_url ||
                                                `https://api.dicebear.com/7.x/avataaars/svg?seed=${contact.username}`
                                            }
                                            alt={contact.username}
                                            className="chat-avatar"
                                        />
                                    </div>
                                    <div className="chat-info">
                                        <div className="contact-header">
                                            <h3
                                                onClick={() =>
                                                    navigate(
                                                        `/users/${contact.username}`,
                                                    )
                                                }
                                            >
                                                {contact.username}
                                                <i className="fas fa-external-link-alt"></i>
                                            </h3>
                                            <div className="friend-status">
                                                {contact.friendship_status
                                                    ?.status === "accepted" ? (
                                                    <span className="friend-badge">
                                                        Friend
                                                    </span>
                                                ) : contact.friendship_status
                                                      ?.status === "pending" ? (
                                                    contact.friendship_status
                                                        .is_sender ? (
                                                        <span className="pending-badge">
                                                            Request Sent
                                                        </span>
                                                    ) : (
                                                        <div className="request-actions">
                                                            <button
                                                                className="accept-btn"
                                                                onClick={(
                                                                    e,
                                                                ) => {
                                                                    e.stopPropagation();
                                                                    handleAcceptRequest(
                                                                        contact.id,
                                                                    );
                                                                }}
                                                            >
                                                                Accept
                                                            </button>
                                                            <button
                                                                className="reject-btn"
                                                                onClick={(
                                                                    e,
                                                                ) => {
                                                                    e.stopPropagation();
                                                                    handleRejectRequest(
                                                                        contact.id,
                                                                    );
                                                                }}
                                                            >
                                                                Reject
                                                            </button>
                                                        </div>
                                                    )
                                                ) : (
                                                    <button
                                                        className="add-friend-btn"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            sendFriendRequest(
                                                                contact.id,
                                                            );
                                                        }}
                                                    >
                                                        Add Friend
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                        <div
                                            onClick={() =>
                                                setReceiverId(contact.id)
                                            }
                                        >
                                            {contact.last_interaction && (
                                                <small className="last-interaction">
                                                    Last message:{" "}
                                                    {new Date(
                                                        contact.last_interaction,
                                                    ).toLocaleString()}
                                                </small>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
                <div className="chat-main">
                    <div className="chat-header">
                        <h2>
                            {selectedUser ? (
                                <>
                                    <img
                                        src={
                                            selectedUser.profile_picture_url ||
                                            `https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedUser.username}`
                                        }
                                        alt={selectedUser.username}
                                        className="chat-avatar"
                                    />
                                    Chat with
                                    <span
                                        onClick={() =>
                                            navigate(
                                                `/users/${selectedUser.username}`,
                                            )
                                        }
                                    >
                                        {selectedUser.username}
                                        <i className="fas fa-external-link-alt"></i>
                                    </span>
                                    {selectedUser.friendship_status?.status !==
                                        "accepted" && (
                                        <span className="not-friend-warning">
                                            (Must be friends to message)
                                        </span>
                                    )}
                                </>
                            ) : (
                                "Select a contact"
                            )}
                        </h2>
                    </div>

                    <div className="message-list" ref={messageListRef}>
                        {filteredMessages.length > 0 ? (
                            filteredMessages.map((msg) => (
                                <div
                                    key={msg.id}
                                    className={`message ${isCurrentUserSender(msg) ? "sent" : "received"} ${msg.isTempMessage ? "temp-message" : ""}`}
                                >
                                    <div className="message-content">
                                        {msg.attachment_url &&
                                            renderAttachment(msg)}
                                        {msg.decrypted_content &&
                                        msg.decrypted_content !== "" ? (
                                            <p>{msg.decrypted_content}</p>
                                        ) : msg.attachment_url ? null /* Don't show anything for attachment-only messages */ : (
                                            <p className="error-text">
                                                {msg.decrypted_content ===
                                                "Error decrypting message"
                                                    ? "Error decrypting message"
                                                    : ""}
                                            </p>
                                        )}
                                    </div>
                                    <span className="message-time">
                                        {new Date(
                                            msg.timestamp,
                                        ).toLocaleTimeString([], {
                                            hour: "2-digit",
                                            minute: "2-digit",
                                        })}
                                    </span>
                                </div>
                            ))
                        ) : (
                            <div className="no-messages">
                                <p>
                                    {selectedUser?.friendship_status?.status ===
                                    "accepted"
                                        ? "No messages yet. Start a conversation!"
                                        : "You must be friends to message this user"}
                                </p>
                                {selectedUser &&
                                    selectedUser.friendship_status?.status !==
                                        "accepted" && (
                                        <button
                                            className="friend-request-btn"
                                            onClick={() => {
                                                if (
                                                    selectedUser
                                                        .friendship_status
                                                        ?.status === "pending"
                                                ) {
                                                    if (
                                                        selectedUser
                                                            .friendship_status
                                                            .is_sender
                                                    ) {
                                                        alert(
                                                            "Request already sent",
                                                        );
                                                    } else {
                                                        handleAcceptRequest(
                                                            selectedUser.id,
                                                        );
                                                    }
                                                } else {
                                                    sendFriendRequest(
                                                        selectedUser.id,
                                                    );
                                                }
                                            }}
                                        >
                                            {selectedUser.friendship_status
                                                ?.status === "pending"
                                                ? selectedUser.friendship_status
                                                      .is_sender
                                                    ? "Request Pending"
                                                    : "Accept Request"
                                                : "Send Friend Request"}
                                        </button>
                                    )}
                            </div>
                        )}
                    </div>

                    <form className="message-input" onSubmit={sendMessage}>
                        <input
                            type="text"
                            value={newMessage}
                            onChange={(e) => {
                                setNewMessage(e.target.value);
                                setError(null);
                            }}
                            placeholder={
                                !receiverId
                                    ? "Select a contact first"
                                    : selectedUser?.friendship_status
                                            ?.status === "accepted"
                                      ? "Type a message..."
                                      : "Must be friends to message"
                            }
                            disabled={
                                !receiverId ||
                                selectedUser?.friendship_status?.status !==
                                    "accepted"
                            }
                        />
                        <input
                            type="file"
                            id="attachmentInput"
                            accept="image/*,video/*"
                            onChange={handleAttachmentChange}
                            style={{ display: "none" }}
                            disabled={
                                selectedUser?.friendship_status?.status !==
                                "accepted"
                            }
                        />
                        <label
                            htmlFor="attachmentInput"
                            className="attach-button"
                            style={{
                                cursor:
                                    selectedUser?.friendship_status?.status ===
                                    "accepted"
                                        ? "pointer"
                                        : "not-allowed",
                                opacity:
                                    selectedUser?.friendship_status?.status ===
                                    "accepted"
                                        ? 1
                                        : 0.5,
                            }}
                        >
                            <i className="fas fa-paperclip"></i>
                        </label>
                        {attachment && (
                            <div className="attachment-preview-container">
                                <div className="attachment-preview">
                                    {attachment.type.startsWith("image/") ? (
                                        <img
                                            src={URL.createObjectURL(
                                                attachment,
                                            )}
                                            alt="Preview"
                                        />
                                    ) : (
                                        <video controls>
                                            <source
                                                src={URL.createObjectURL(
                                                    attachment,
                                                )}
                                                type={attachment.type}
                                            />
                                        </video>
                                    )}
                                </div>
                                <button
                                    type="button"
                                    className="remove-attachment"
                                    onClick={() => {
                                        setAttachment(null);
                                        document.getElementById(
                                            "attachmentInput",
                                        ).value = "";
                                    }}
                                >
                                    <i className="fas fa-times"></i>
                                </button>
                            </div>
                        )}
                        <button
                            type="submit"
                            className="send-button"
                            disabled={
                                !receiverId ||
                                (!newMessage.trim() && !attachment) ||
                                selectedUser?.friendship_status?.status !==
                                    "accepted"
                            }
                        >
                            <i className="fas fa-paper-plane"></i>
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
