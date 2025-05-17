import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import "../assets/styles/GroupMessaging.css";
import CreateGroupModal from "../context/CreateGroupModal";
import { useNavigate } from "react-router-dom";

// A simple warning dialog component
function WarningDialog({ onClose }) {
  return (
    <div className="warning-dialog-overlay">
      <div className="warning-dialog">
        <h2>🛑 STOP! Access Restricted ✋ 🛑</h2>
        <p>
          Your account is <p1>not verified</p1>. <br/> Please verify your account to access group messaging.
        </p>
        <button onClick={onClose}>OK</button>
      </div>
    </div>
  );
}

export default function ChatGroupMessaging() {
  const [chatGroups, setChatGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showWarning, setShowWarning] = useState(false);
  const { token, user } = useAuth();
  const messageListRef = useRef(null);
  const navigate = useNavigate();

  // Check if user is verified on mount/update
  useEffect(() => {
    if (user && !user.is_verified) {
      setShowWarning(true);   // <- turn this to false
    } else {
      setShowWarning(false);
    }
  }, [user]);

  // Fetch chat groups
  const fetchChatGroups = async () => {
    try {
      setLoading(true);
      const res = await axios.get("/api/chat_groups/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setChatGroups(res.data);
    } catch (err) {
      setError("Failed to load chat groups");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChatGroups();
  }, [token]);

  // Fetch messages for selected group
  const fetchChatMessages = async () => {
    if (!selectedGroup) return;
    try {
      const res = await axios.get(
        `/api/chat_messages/?chat_group=${selectedGroup.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setChatMessages(res.data);
    } catch (err) {
      setError("Failed to load chat messages");
    }
  };

  useEffect(() => {
    if (selectedGroup) {
      fetchChatMessages();
      const interval = setInterval(fetchChatMessages, 1000);
      return () => clearInterval(interval);
    }
  }, [selectedGroup, token]);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    if (messageListRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = messageListRef.current;
      if (scrollHeight - scrollTop - clientHeight < 100) {
        messageListRef.current.scrollTop = scrollHeight;
      }
    }
  }, [chatMessages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!selectedGroup || !newMessage.trim()) {
      setError("Select a group and type a message");
      return;
    }
    try {
      setLoading(true);
      await axios.post(
        "/api/chat_messages/",
        {
          chat_group: selectedGroup.id,
          content: newMessage.trim(),
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setNewMessage("");
      await fetchChatMessages();
    } catch (err) {
      setError("Failed to send message");
    } finally {
      setLoading(false);
    }
  };

  const handleGroupCreated = () => {
    setShowCreateModal(false);
    fetchChatGroups();
  };

  return (
    <>
      {user && !user.is_verified && showWarning ? (
        <WarningDialog onClose={() => navigate("/profile")} />
      ) : (
        <div className="messaging-wrapper">
          {/* <div className="messaging-container"> */}
            {error && <div className="error-message">{error}</div>}
            {loading && <div className="loading-overlay">Loading...</div>}

            {/* Sidebar */}
            <div className="chat-sidebar">
              <h2>Chat Groups</h2>
              <button
                className="create-group-button"
                onClick={() => setShowCreateModal(true)}
              >
                + Create Group
              </button>
              <div className="chat-list">
                {chatGroups.map((group) => (
                  <div
                    key={group.id}
                    className={`chat-item ${
                      selectedGroup && selectedGroup.id === group.id ? "active" : ""
                    }`}
                    onClick={() => setSelectedGroup(group)}
                  >
                    <div className="chat-info">
                      <h3>{group.name}</h3>
                      <p>
                        {group.members_count ? `${group.members_count} members` : ""}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Main Chat Area */}
            <div className="chat-main">
              <div className="chat-header">
                <h2>
                  {selectedGroup
                    ? `Group: ${selectedGroup.name}`
                    : "Select a Chat Group"}
                </h2>
              </div>
              <div className="message-list" ref={messageListRef}>
                {chatMessages.length > 0 ? (
                  chatMessages.map((msg) => {
                    const isSelf = msg.sender === user.id;
                    return (
                      <div
                        key={msg.id}
                        className={`message ${isSelf ? "self" : "other"}`}
                      >
                        {!isSelf && (
                          <div className="message-sender">
                            <img
                              src={
                                msg.profile_picture_url
                                  ? msg.profile_picture_url
                                  : `https://api.dicebear.com/7.x/avataaars/svg?seed=${msg.sender_username}`
                              }
                              alt={msg.sender_username}
                              className="chat-avatar"
                            />
                            <span className="sender-name">{msg.sender_username}</span>
                          </div>
                        )}
                        <div className="message-content">
                          <p>{msg.decrypted_content || msg.content}</p>
                          <span className="message-time">
                            {new Date(msg.timestamp).toLocaleString([], {
                              year: "numeric",
                              month: "2-digit",
                              day: "2-digit",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  !loading && <p className="no-messages">No messages yet.</p>
                )}
              </div>
              <form className="message-input" onSubmit={sendMessage}>
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder={
                    selectedGroup ? "Type a message..." : "Select a group first"
                  }
                  disabled={loading || !selectedGroup}
                />
                <button
                  type="submit"
                  className="send-button"
                  disabled={loading || !selectedGroup || !newMessage.trim()}
                >
                  <i className="fas fa-paper-plane"></i>
                </button>
              </form>
            </div>
          {/* </div> */}
          {showCreateModal && (
            <CreateGroupModal
              token={token}
              onClose={() => setShowCreateModal(false)}
              onGroupCreated={handleGroupCreated}
              currentUser={user}
            />
          )}
        </div>
      )}
    </>
  );
}
