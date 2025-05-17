import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import BlockButton from "./BlockButton";
import ReportUserModal from "./ReportUserModal";
import "../assets/styles/Profile.css";
import "../assets/styles/BlockReport.css";

export default function UserProfilePage() {
    const [profileData, setProfileData] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [showReportModal, setShowReportModal] = useState(false);
    const [isBlocked, setIsBlocked] = useState(false);
    const { user } = useAuth();
    const { username } = useParams();
    const navigate = useNavigate();

    // Fetch user profile data
    useEffect(() => {
        // If trying to view your own profile, redirect to the profile edit page
        if (user && user.username === username) {
            navigate("/profile");
            return;
        }

        const fetchUserProfile = async () => {
            if (!user) return;

            try {
                setLoading(true);
                const response = await axios.get(
                    `/api/users/${username}/profile/`,
                    {
                        withCredentials: true,
                    },
                );

                setProfileData({
                    ...response.data,
                    profile_picture_url: response.data.profile_picture_url,
                });
            } catch (error) {
                console.error("Error fetching profile:", error);
                if (error.response && error.response.status === 404) {
                    setError("User not found.");
                } else {
                    setError("Failed to load user profile data.");
                }
            } finally {
                setLoading(false);
            }
        };

        fetchUserProfile();
    }, [user, username, navigate]);

    // Check if the user is blocked
    const checkIfBlocked = useCallback(async () => {
        if (!profileData.user_id) return;

        try {
            const response = await axios.get("/api/blocks/");
            const blocked = response.data.some(
                (block) =>
                    block.blocked === profileData.user_id ||
                    block.blocked_username === profileData.username,
            );
            setIsBlocked(blocked);
        } catch (err) {
            console.error("Error checking block status:", err);
        }
    }, [profileData.user_id, profileData.username]);

    // Call checkIfBlocked when profile data changes
    useEffect(() => {
        if (profileData.user_id) {
            checkIfBlocked();
        }
    }, [profileData.user_id, checkIfBlocked]);

    // Handle block status changes
    const handleBlockChange = (blocked) => {
        setIsBlocked(blocked);
    };

    if (loading) {
        return <div className="loading-container">Loading...</div>;
    }

    if (error) {
        return <div className="error-container">{error}</div>;
    }

    return (
        <div className="profile-container fade-in">
            <div className="profile-header glass-card slide-up">
                <div className="profile-cover"></div>
                <div className="profile-info">
                    <div className="profile-avatar-wrapper">
                        <img
                            src={
                                profileData.profile_picture_url ||
                                "https://api.dicebear.com/7.x/avataaars/svg?seed=User"
                            }
                            alt="Profile"
                            className="profile-avatar"
                        />
                    </div>
                    <div className="profile-details">
                        <h1>{profileData.full_name}</h1>
                        <p className="username">@{profileData.username}</p>
                        {/* <p className="email">{profileData.email}</p> */}
                        <p className="bio">{profileData.bio}</p>
                        {profileData.is_verified && (
                            <p className="verified-badge">
                                <i className="fas fa-check-circle"></i> Verified
                                Account
                            </p>
                        )}

                        {isBlocked && (
                            <div className="blocked-status">
                                <i className="fas fa-ban"></i> User Blocked
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className="user-actions">
                <button
                    className="action-button message-button"
                    onClick={() =>
                        navigate("/messages", {
                            state: { username: profileData.username },
                        })
                    }
                    disabled={isBlocked}
                >
                    <i className="fas fa-envelope"></i> Send Message
                </button>

                <button
                    className="action-button report-button"
                    onClick={() => setShowReportModal(true)}
                >
                    <i className="fas fa-flag"></i> Report
                </button>

                <BlockButton
                    userId={profileData.user_id}
                    username={profileData.username}
                    onBlockChange={handleBlockChange}
                />
            </div>

            {showReportModal && (
                <ReportUserModal
                    userId={profileData.user_id}
                    username={profileData.username}
                    onClose={() => setShowReportModal(false)}
                />
            )}
        </div>
    );
}
