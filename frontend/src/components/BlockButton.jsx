import React, { useState, useEffect } from "react";
import axios from "axios";
import "../assets/styles/BlockReport.css";

function BlockButton({ userId, username, onBlockChange }) {
    const [isBlocking, setIsBlocking] = useState(false);
    const [isBlocked, setIsBlocked] = useState(false);
    const [blockId, setBlockId] = useState(null);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);

    // Check if the user is already blocked when the component loads
    useEffect(() => {
        const checkIfBlocked = async () => {
            if (!userId) return;

            try {
                const response = await axios.get("/api/blocks/");
                const blockedUser = response.data.find(
                    (block) =>
                        block.blocked === userId ||
                        block.blocked_username === username,
                );

                if (blockedUser) {
                    setIsBlocked(true);
                    setBlockId(blockedUser.id);
                }
            } catch (err) {
                console.error("Error checking block status:", err);
            } finally {
                setLoading(false);
            }
        };

        checkIfBlocked();
    }, [userId, username]);

    const handleBlock = async () => {
        if (
            !window.confirm(
                `Are you sure you want to block ${username}? You won't see their messages.`,
            )
        ) {
            return;
        }

        try {
            setIsBlocking(true);
            setError("");

            const response = await axios.post(
                "/api/blocks/",
                { blocked: userId },
                {
                    headers: {
                        "Content-Type": "application/json",
                    },
                },
            );

            setIsBlocked(true);
            setBlockId(response.data.id);

            if (onBlockChange) onBlockChange(true);
        } catch (err) {
            console.error("Block error:", err.response?.data || err.message);
            setError(
                err.response?.data?.detail ||
                    JSON.stringify(err.response?.data) ||
                    "Failed to block user",
            );
        } finally {
            setIsBlocking(false);
        }
    };

    const handleUnblock = async () => {
        if (!window.confirm(`Are you sure you want to unblock ${username}?`)) {
            return;
        }

        try {
            setIsBlocking(true);
            setError("");

            await axios.delete(`/api/blocks/${blockId}/`);

            setIsBlocked(false);
            setBlockId(null);

            if (onBlockChange) onBlockChange(false);
        } catch (err) {
            console.error("Unblock error:", err.response?.data || err.message);
            setError(
                err.response?.data?.detail ||
                    JSON.stringify(err.response?.data) ||
                    "Failed to unblock user",
            );
        } finally {
            setIsBlocking(false);
        }
    };

    if (loading) {
        return (
            <button className="action-button block-button" disabled>
                Loading...
            </button>
        );
    }

    return (
        <>
            {isBlocked ? (
                <button
                    onClick={handleUnblock}
                    disabled={isBlocking}
                    className="action-button unblock-button"
                >
                    <i className="fas fa-user-check"></i>
                    {isBlocking ? "Processing..." : "Unblock"}
                </button>
            ) : (
                <button
                    onClick={handleBlock}
                    disabled={isBlocking}
                    className="action-button block-button"
                >
                    <i className="fas fa-ban"></i>
                    {isBlocking ? "Blocking..." : "Block"}
                </button>
            )}
            {error && <div className="error-message">{error}</div>}
        </>
    );
}

export default BlockButton;
