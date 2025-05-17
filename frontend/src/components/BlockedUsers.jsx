import React, { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import "../assets/styles/BlockReport.css";

function BlockedUsers() {
    const [blockedUsers, setBlockedUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // Fetch blocked users
    useEffect(() => {
        const fetchBlockedUsers = async () => {
            try {
                setLoading(true);
                const response = await axios.get("/api/blocks/");
                setBlockedUsers(response.data);
            } catch (err) {
                setError("Failed to load blocked users");
            } finally {
                setLoading(false);
            }
        };

        fetchBlockedUsers();
    }, []);

    // Unblock a user
    const handleUnblock = async (blockId, username) => {
        if (!window.confirm(`Are you sure you want to unblock ${username}?`)) {
            return;
        }

        try {
            await axios.delete(`/api/blocks/${blockId}/`);
            // Remove from the list
            setBlockedUsers(
                blockedUsers.filter((block) => block.id !== blockId),
            );
        } catch (err) {
            setError("Failed to unblock user");
        }
    };

    return (
        <div className="blocked-users-container">
            <h2>Blocked Users</h2>

            {error && <div className="error-message">{error}</div>}

            {loading ? (
                <div className="loading-container">
                    Loading blocked users...
                </div>
            ) : blockedUsers.length === 0 ? (
                <div className="no-blocks-message">
                    <i className="fas fa-check-circle"></i>
                    <p>You haven't blocked any users yet.</p>
                </div>
            ) : (
                <ul className="blocked-users-list">
                    {blockedUsers.map((block) => (
                        <li key={block.id} className="blocked-user-item">
                            <div className="user-info">
                                <img
                                    src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${block.blocked_username}`}
                                    alt={block.blocked_username}
                                    className="user-avatar"
                                />
                                <Link to={`/users/${block.blocked_username}`}>
                                    <span className="username">
                                        {block.blocked_username}
                                    </span>
                                </Link>
                            </div>
                            <div className="actions">
                                <small className="blocked-date">
                                    Blocked on{" "}
                                    {new Date(
                                        block.created_at,
                                    ).toLocaleDateString()}
                                </small>
                                <button
                                    onClick={() =>
                                        handleUnblock(
                                            block.id,
                                            block.blocked_username,
                                        )
                                    }
                                    className="action-button unblock-button"
                                >
                                    <i className="fas fa-user-check"></i>{" "}
                                    Unblock
                                </button>
                            </div>
                        </li>
                    ))}
                </ul>
            )}

            <div className="back-link">
                <Link to="/profile" className="link-button">
                    <i className="fas fa-arrow-left"></i> Back to Profile
                </Link>
            </div>
        </div>
    );
}

export default BlockedUsers;
