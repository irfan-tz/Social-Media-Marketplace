import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { useNavigate, useLocation } from "react-router-dom";
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
    const { token, user } = useAuth();
    const messageListRef = useRef(null);
    const navigate = useNavigate();
    const location = useLocation();
    const [friendRequests, setFriendRequests] = useState([]);

    // Safe user data access
    const currentUserId = user?.id;

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [usersResponse, messagesResponse, requestsResponse] = await Promise.all([
                    axios.get("/api/users/", { headers: { Authorization: `Bearer ${token}` } }),
                    axios.get("/api/messages/", { headers: { Authorization: `Bearer ${token}` } }),
                    axios.get("/api/friendships/", { headers: { Authorization: `Bearer ${token}` } })
                ]);

                setUsers(usersResponse.data);
                setMessages(messagesResponse.data);
                setFriendRequests(requestsResponse.data);

                if (location.state?.username) {
                    const targetUser = usersResponse.data.find(
                        u => u.username === location.state.username
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
    }, [token, location.state]);

    useEffect(() => {
        const intervalId = setInterval(async () => {
            try {
                const [messagesResponse, usersResponse] = await Promise.all([
                    axios.get("/api/messages/", { headers: { Authorization: `Bearer ${token}` } }),
                    axios.get("/api/users/", { headers: { Authorization: `Bearer ${token}` } })
                ]);
                setMessages(messagesResponse.data);
                setUsers(usersResponse.data);
            } catch (err) {
                // Polling error occurred
            }
        }, 1000);
        return () => clearInterval(intervalId);
    }, [token]);

    // Friendship handlers
    const sendFriendRequest = async (receiverId) => {
        try {
            await axios.post("/api/friendships/", { receiver: receiverId }, 
                { headers: { Authorization: `Bearer ${token}` } });
            const updatedUsers = users.map(u => 
                u.id === receiverId ? { ...u, friendship_status: { status: 'pending', is_sender: true } } : u
            );
            setUsers(updatedUsers);
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to send friend request");
        }
    };

    // const handleAcceptRequest = async (friendId) => {
    //     try {
    //         const request = friendRequests.find(fr => 
    //             fr.sender.id === friendId && fr.status === 'pending'
    //         );
    //         if (!request) throw new Error("Request not found");
            
    //         await axios.post(`/api/friendships/${request.id}/accept/`, {}, 
    //             { headers: { Authorization: `Bearer ${token}` } });
            
    //         const updatedUsers = users.map(u => 
    //             u.id === friendId ? { ...u, friendship_status: { status: 'accepted' } } : u
    //         );
    //         setUsers(updatedUsers);
    //     } catch (err) {
    //         setError(err.response?.data?.detail || "Failed to accept request");
    //     }
    // };

    const handleAcceptRequest = async (friendId) => {
        try {
            // Find the pending request
            const response = await axios.get(`/api/friendships/?receiver=${user.id}&sender=${friendId}&status=pending`);
            const request = response.data[0]; // Get first matching request
            
            if (!request) {
                setError("No pending request found");
                return;
            }
    
            // Send accept request
            await axios.post(`/api/friendships/${request.id}/accept/`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
    
            // Update UI
            setUsers(users.map(u => 
                u.id === friendId 
                    ? { ...u, friendship_status: { status: 'accepted' } } 
                    : u
            ));
        } catch (err) {
            setError(err.response?.data?.error || "Failed to accept request");
        }
    };
    
    const handleRejectRequest = async (friendId) => {
        try {
            // Find the pending request
            const response = await axios.get(`/api/friendships/?receiver=${user.id}&sender=${friendId}&status=pending`);
            const request = response.data[0];
            
            if (!request) {
                setError("No pending request found");
                return;
            }
    
            // Send reject request
            await axios.post(`/api/friendships/${request.id}/reject/`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
    
            // Update UI
            setUsers(users.map(u => 
                u.id === friendId 
                    ? { ...u, friendship_status: null } 
                    : u
            ));
        } catch (err) {
            setError(err.response?.data?.error || "Failed to reject request");
        }
    };

    const renderAttachment = (msg) => {
        if (!msg.attachment_url) return null;
        const contentType = msg.attachment_content_type;

        if (contentType?.startsWith("video/")) {
            return (
                <div className="video-wrapper">
                    <video controls>
                        <source src={msg.attachment_url} type={contentType} />
                        Your browser does not support the video tag.
                    </video>
                </div>
            );
        }
        if (contentType?.startsWith("image/")) {
            return <img src={msg.attachment_url} alt="attachment" className="message-attachment" />;
        }
        return <p>Unsupported attachment type.</p>;
    };

    const handleAttachmentChange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        z
        const allowedTypes = ["image/jpeg", "image/png", "image/gif", "video/mp4"];
        const maxSize = 10 * 1024 * 1024;

        if (!allowedTypes.includes(file.type)) {
            setError("Only images and videos are allowed");
            return;
        }
        if (file.size > maxSize) {
            setError("File size must be under 10MB");
            return;
        }
        setAttachment(file);
        setError(null);
    };

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!receiverId || (!newMessage.trim() && !attachment)) {
            setError("Select a receiver and add content");
            return;
        }

        try {
            const selectedUser = users?.find(u => u.id === receiverId);
            if (selectedUser?.friendship_status?.status !== 'accepted') {
                setError("You must be friends to message");
                return;
            }

            setLoading(true);
            const formData = new FormData();
            formData.append("receiver", receiverId);
            if (newMessage.trim()) formData.append("content", newMessage.trim());
            if (attachment) formData.append("attachment", attachment);

            await axios.post("/api/messages/", formData, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "multipart/form-data",
                },
            });

            setNewMessage("");
            setAttachment(null);
            document.getElementById("attachmentInput").value = "";
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to send message");
        } finally {
            setLoading(false);
        }
    };

    const isCurrentUserSender = (message) => 
        message.sender === currentUserId || message.sender_username === user?.username;

    // Safe data initialization
    const selectedUser = users?.find(u => u.id === receiverId) || null;
    const filteredMessages = messages
        ?.filter(msg => [msg.sender, msg.receiver].includes(receiverId))
        ?.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)) || [];
    const filteredUsers = users?.filter(u => u.id !== currentUserId) || [];

    return (
        <div className="page-container full-width-page">
            <div className="messaging-wrapper">
                {error && <div className="error-message">{error}</div>}
                {loading && <div className="loading-overlay">Loading...</div>}

                <div className="chat-sidebar">
                    <h2>Contacts</h2>
                    <div className="chat-list">
                        {filteredUsers.map(contact => (
                            <div key={contact.id} className={`chat-item ${receiverId === contact.id ? "active" : ""}`}>
                                <div className="chat-avatar-wrapper" onClick={() => setReceiverId(contact.id)}>
                                    <img
                                        src={contact.profile_picture_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${contact.username}`}
                                        alt={contact.username}
                                        className="chat-avatar"
                                    />
                                </div>
                                <div className="chat-info">
                                    <div className="contact-header">
                                        <h3 onClick={() => navigate(`/users/${contact.username}`)}>
                                            {contact.username}
                                            <i className="fas fa-external-link-alt"></i>
                                        </h3>
                                        <div className="friend-status">
                                            {contact.friendship_status?.status === 'accepted' ? (
                                                <span className="friend-badge">Friend</span>
                                            ) : contact.friendship_status?.status === 'pending' ? (
                                                contact.friendship_status.is_sender ? (
                                                    <span className="pending-badge">Request Sent</span>
                                                ) : (
                                                    <div className="request-actions">
                                                        <button className="accept-btn" onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleAcceptRequest(contact.id);
                                                        }}>
                                                            Accept
                                                        </button>
                                                        <button className="reject-btn" onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleRejectRequest(contact.id);
                                                        }}>
                                                            Reject
                                                        </button>
                                                    </div>
                                                )
                                            ) : (
                                                <button 
                                                    className="add-friend-btn"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        sendFriendRequest(contact.id);
                                                    }}
                                                >
                                                    Add Friend
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                    <div onClick={() => setReceiverId(contact.id)}>
                                        {contact.last_interaction && (
                                            <small className="last-interaction">
                                                Last message: {new Date(contact.last_interaction).toLocaleString()}
                                            </small>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="chat-main">
                    <div className="chat-header">
                        <h2>
                            {selectedUser ? (
                                <>
                                    <img
                                        src={selectedUser.profile_picture_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedUser.username}`}
                                        alt={selectedUser.username}
                                        className="chat-avatar"
                                    />
                                    Chat with
                                    <span onClick={() => navigate(`/users/${selectedUser.username}`)}>
                                        {selectedUser.username}
                                        <i className="fas fa-external-link-alt"></i>
                                    </span>
                                    {selectedUser.friendship_status?.status !== 'accepted' && (
                                        <span className="not-friend-warning">
                                            (Must be friends to message)
                                        </span>
                                    )}
                                </>
                            ) : "Select a contact"}
                        </h2>
                    </div>

                    <div className="message-list" ref={messageListRef}>
                        {filteredMessages.length > 0 ? (
                            filteredMessages.map(msg => (
                                <div key={msg.id} className={`message ${isCurrentUserSender(msg) ? "sent" : "received"}`}>
                                    <div className="message-content">
                                        {msg.attachment_url && renderAttachment(msg)}
                                        {msg.decrypted_content && <p>{msg.decrypted_content}</p>}
                                    </div>
                                    <span className="message-time">
                                        {new Date(msg.timestamp).toLocaleTimeString([], {
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}
                                    </span>
                                </div>
                            ))
                        ) : (
                            <div className="no-messages">
                                <p>
                                    {selectedUser?.friendship_status?.status === 'accepted'
                                        ? "No messages yet. Start a conversation!"
                                        : "You must be friends to message this user"}
                                </p>
                                {selectedUser && selectedUser.friendship_status?.status !== 'accepted' && (
                                    <button 
                                        className="friend-request-btn"
                                        onClick={() => {
                                            if (selectedUser.friendship_status?.status === 'pending') {
                                                if (selectedUser.friendship_status.is_sender) {
                                                    alert('Request already sent');
                                                } else {
                                                    handleAcceptRequest(selectedUser.id);
                                                }
                                            } else {
                                                sendFriendRequest(selectedUser.id);
                                            }
                                        }}
                                    >
                                        {selectedUser.friendship_status?.status === 'pending'
                                            ? (selectedUser.friendship_status.is_sender 
                                                ? "Request Pending" 
                                                : "Accept Request")
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
                                !receiverId ? "Select a contact first" :
                                selectedUser?.friendship_status?.status === 'accepted' 
                                    ? "Type a message..." 
                                    : "Must be friends to message"
                            }
                            disabled={!receiverId || selectedUser?.friendship_status?.status !== 'accepted'}
                        />
                        <input
                            type="file"
                            id="attachmentInput"
                            accept="image/*,video/*"
                            onChange={handleAttachmentChange}
                            style={{ display: 'none' }}
                            disabled={selectedUser?.friendship_status?.status !== 'accepted'}
                        />
                        <label 
                            htmlFor="attachmentInput" 
                            className="attach-button"
                            style={{ 
                                cursor: selectedUser?.friendship_status?.status === 'accepted' ? 'pointer' : 'not-allowed',
                                opacity: selectedUser?.friendship_status?.status === 'accepted' ? 1 : 0.5
                            }}
                        >
                            <i className="fas fa-paperclip"></i>
                        </label>
                        {attachment && (
                            <div className="attachment-preview-container">
                                <div className="attachment-preview">
                                    {attachment.type.startsWith('image/') ? (
                                        <img src={URL.createObjectURL(attachment)} alt="Preview" />
                                    ) : (
                                        <video controls>
                                            <source src={URL.createObjectURL(attachment)} type={attachment.type} />
                                        </video>
                                    )}
                                </div>
                                <button
                                    type="button"
                                    className="remove-attachment"
                                    onClick={() => {
                                        setAttachment(null);
                                        document.getElementById('attachmentInput').value = '';
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
                                selectedUser?.friendship_status?.status !== 'accepted'
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