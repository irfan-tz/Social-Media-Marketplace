import "../assets/styles/Auth.css";
import "../assets/styles/Profile.css";
import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import DashboardLayout from "./DashboardLayout";
import "@fortawesome/fontawesome-free/css/all.min.css";
import { Link } from "react-router-dom";
import ChangePassword from "./ChangePassword";

export default function Profile() {
    const [profileData, setProfileData] = useState({
        full_name: "",
        username: "",
        email: "",
        bio: "",
        profile_picture: null,
        profile_picture_url: null,
        verification_document: null, // added new state for verification document
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const { user } = useAuth();
    const fileInputRef = useRef(null);

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                setLoading(true);
                const response = await axios.get("/api/profile/", {
                    withCredentials: true,
                });

                setProfileData({
                    ...response.data,
                    profile_picture: null,
                    verification_document: null, // ensure document is null on load
                    profile_picture_url: response.data.profile_picture_url,
                });
            } catch (error) {
                setError("Failed to load profile data.");
            } finally {
                setLoading(false);
            }
        };

        user && fetchProfile();
    }, [user]);

    const handleUpdateProfile = async (e) => {
        e.preventDefault();
        const formData = new FormData();

        formData.append("user_id", user.user_id);

        formData.append("bio", profileData.bio);
        formData.append("full_name", profileData.full_name);
        formData.append("username", profileData.username);
        // Keep sending the original email even though it's not editable
        formData.append("email", profileData.email);

        // Handle profile picture upload
        if (profileData.profile_picture) {
            if (profileData.profile_picture.size > 5 * 1024 * 1024) {
                return setError("Profile picture must be less than 5MB");
            }
            const allowedPicTypes = ["image/jpeg", "image/png", "image/gif"];
            if (!allowedPicTypes.includes(profileData.profile_picture.type)) {
                return setError(
                    "Only JPEG, PNG, and GIF allowed for profile picture",
                );
            }
            formData.append("profile_picture", profileData.profile_picture);
        }

        // Handle verification document upload
        if (profileData.verification_document) {
            const allowedDocTypes = [
                "application/pdf",
                "image/jpeg",
                "image/png",
            ];
            if (
                !allowedDocTypes.includes(
                    profileData.verification_document.type,
                )
            ) {
                return setError(
                    "Only PDF, JPG, and PNG files allowed for verification document",
                );
            }
            if (profileData.verification_document.size > 5 * 1024 * 1024) {
                return setError("Verification document must be less than 5MB");
            }
            formData.append(
                "verification_document",
                profileData.verification_document,
            );
        }

        try {
            setLoading(true);
            setError("");

            const { data } = await axios.put("/api/profile/update/", formData, {
                headers: { "Content-Type": "multipart/form-data" },
                withCredentials: true,
            });

            setProfileData((prev) => ({
                ...prev,
                ...data,
                profile_picture: null,
                verification_document: null,
                profile_picture_url: data.profile_picture_url,
            }));
            alert("Profile updated successfully!");
        } catch (error) {
            const message =
                error.response?.data?.detail || error.request
                    ? "No server response"
                    : "Update failed. Please try again.";
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        // Prevent changes to the email field
        if (e.target.name !== "email") {
            setProfileData({ ...profileData, [e.target.name]: e.target.value });
        }
    };

    // Trigger the hidden file input when clicking the camera button for profile picture
    const handleProfilePictureClick = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    // Handle file selection for profile picture
    const handleFileChange = (e) => {
        setProfileData({
            ...profileData,
            profile_picture: e.target.files[0],
        });
    };

    // Handle file selection for verification document
    const handleVerificationChange = (e) => {
        setProfileData({
            ...profileData,
            verification_document: e.target.files[0],
        });
    };

    return (
        <div className="profile-container fade-in">
            <div className="profile-header glass-card slide-up">
                <div className="profile-cover">
                    <button className="edit-cover">
                        <i className="fas fa-camera"></i> Change Cover
                    </button>
                </div>
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
                        <button
                            type="button"
                            className="edit-avatar"
                            onClick={handleProfilePictureClick}
                        >
                            <i className="fas fa-camera"></i>
                        </button>
                        {/* Hidden file input triggered by the camera button */}
                        <input
                            type="file"
                            accept="image/*"
                            ref={fileInputRef}
                            style={{ display: "none" }}
                            onChange={handleFileChange}
                        />
                    </div>
                    <div className="profile-details">
                        <h1>{profileData.full_name}</h1>
                        <p className="username">@{profileData.username}</p>
                        <p className="email">{profileData.email}</p>
                        <p className="bio">{profileData.bio}</p>
                    </div>
                </div>
            </div>

            <form onSubmit={handleUpdateProfile} className="auth-form">
                {error && <div className="error-message">{error}</div>}
                {loading && <div className="loading-message">Loading...</div>}
                <div className="form-group">
                    <label>Full Name</label>
                    <input
                        name="full_name"
                        value={profileData.full_name}
                        onChange={handleChange}
                        required
                    />
                </div>
                <div className="form-group">
                    <label>Username</label>
                    <input
                        name="username"
                        value={profileData.username}
                        onChange={handleChange}
                        required
                    />
                </div>
                <div className="form-group">
                    <label>Email</label>
                    <input
                        type="email"
                        name="email"
                        value={profileData.email}
                        onChange={handleChange}
                        readOnly
                        disabled
                        className="readonly-input"
                    />
                </div>
                <div className="form-group verification-status">
                    <label>Account Status</label>
                    <div className="status-indicator">
                        <i
                            className={`fas fa-${profileData.is_verified ? "check-circle verified" : "times-circle unverified"}`}
                        ></i>
                        <span
                            style={{
                                color: profileData.is_verified
                                    ? "green"
                                    : "red",
                            }}
                        >
                            {profileData.is_verified
                                ? "  Verified Account"
                                : "  Unverified Account"}
                        </span>
                    </div>
                </div>
                <div className="form-group">
                    <label>Bio</label>
                    <textarea
                        name="bio"
                        value={profileData.bio}
                        onChange={handleChange}
                        rows="4"
                    />
                </div>
                {/* Verification Document Upload */}
                <div className="form-group">
                    <label htmlFor="verification_document">
                        Upload Verification Document (PDF/Image):
                    </label>
                    <input
                        type="file"
                        id="verification_document"
                        accept=".pdf,.jpg,.jpeg,.png"
                        onChange={handleVerificationChange}
                    />
                </div>
                <button type="submit" disabled={loading}>
                    {loading ? "Updating..." : "Update Profile"}
                </button>
            </form>
            <div className="profile-section">
                <Link to="/blocked-users" className="secondary-link">
                    <i className="fas fa-ban"></i> Manage Blocked Users
                </Link>
            </div>
            <div className="profile-section">
                <ChangePassword />
            </div>
            <Link to="/delete-account" className="delete-account-link">
                Delete Account
            </Link>
        </div>
    );
}