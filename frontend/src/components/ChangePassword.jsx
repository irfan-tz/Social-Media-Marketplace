import React, { useState } from "react";
import axios from "axios";
import "../assets/styles/Auth.css";
import { useAuth } from "../context/AuthContext";
import "@fortawesome/fontawesome-free/css/all.min.css";

const validatePasswordStrength = (password) => {
    const minLength = 8;
    const hasNumber = /[0-9]/.test(password);
    const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

    if (password.length < minLength) {
        return "Password must be at least 8 characters long";
    }
    if (!hasNumber) {
        return "Password must contain at least one number";
    }
    if (!hasSpecialChar) {
        return "Password must contain at least one special character";
    }
    return null; // Password is valid
};

export default function ChangePassword() {
    const [showForm, setShowForm] = useState(false);
    const [step, setStep] = useState(1);
    const [otp, setOtp] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmNewPassword, setConfirmNewPassword] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [loading, setLoading] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const { user } = useAuth();

    const initiatePasswordChange = async () => {
        try {
            setLoading(true);
            setError("");
            await axios.post("/api/change-password/request-otp/", { 
                email: user.email 
            });
            setSuccess("OTP sent to your email");
            setShowForm(true);
            setStep(2);
        } catch (err) {
            setError(err.response?.data?.error || "Failed to send OTP");
        } finally {
            setLoading(false);
        }
    };

    const verifyOTP = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            await axios.post("/api/change-password/verify-otp/", { 
                email: user.email, 
                otp 
            });
            setStep(3);
            setSuccess("OTP verified. Please enter your new password.");
        } catch (err) {
            setError(err.response?.data?.error || "Invalid OTP");
        } finally {
            setLoading(false);
        }
    };

    const changePassword = async (e) => {
        e.preventDefault();
        setError("");
        
        // Password validation
        const passwordError = validatePasswordStrength(newPassword);
        if (passwordError) {
            setError(passwordError);
            return;
        }
        
        if (newPassword !== confirmNewPassword) {
            setError("Passwords do not match");
            return;
        }
        
        setLoading(true);
        try {
            await axios.post("/api/change-password/reset/", {
                email: user.email,
                new_password: newPassword,
                otp: otp,
            });
            setSuccess("Password changed successfully!");
            // Reset form
            setOtp("");
            setNewPassword("");
            setConfirmNewPassword("");
            setShowForm(false);
            setStep(1);
        } catch (err) {
            setError(err.response?.data?.error || "Failed to change password");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-card">
            <h2>Change Password</h2>
            
            {!showForm ? (
                <div className="initiate-change">
                    <button 
                        onClick={initiatePasswordChange}
                        disabled={loading}
                        className="change-password-btn"
                    >
                        {loading ? "Sending OTP..." : "Change Password"}
                    </button>
                    {error && <div className="error-message">{error}</div>}
                    {success && <div className="success-message">{success}</div>}
                </div>
            ) : (
                <>
                    {error && <div className="error-message">{error}</div>}
                    {success && <div className="success-message">{success}</div>}

                    {step === 2 && (
                        <form onSubmit={verifyOTP} className="auth-form">
                            <div className="form-group">
                                <p>We've sent an OTP to your email ({user?.email})</p>
                                <input
                                    type="text"
                                    placeholder="Enter OTP"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                    required
                                />
                            </div>
                            <button type="submit" disabled={loading}>
                                {loading ? "Verifying..." : "Verify OTP"}
                            </button>
                            <button 
                                type="button" 
                                onClick={initiatePasswordChange}
                                disabled={loading}
                                className="resend-link"
                            >
                                Resend OTP
                            </button>
                        </form>
                    )}

                    {step === 3 && (
                        <form onSubmit={changePassword} className="auth-form">
                            <div className="form-group password-group">
                                <input
                                    type={showNewPassword ? "text" : "password"}
                                    placeholder="New Password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    required
                                />
                                <i
                                    onClick={() => setShowNewPassword(!showNewPassword)}
                                    className={`fas fa-eye${
                                        showNewPassword ? "-slash" : ""
                                    }`}
                                />
                            </div>
                            <div className="password-requirements">
                                <p>Password must:</p>
                                <ul>
                                    <li>Be at least 8 characters long</li>
                                    <li>Contain at least one number</li>
                                    <li>Contain at least one special character</li>
                                </ul>
                            </div>
                            <div className="form-group password-group">
                                <input
                                    type={showConfirmPassword ? "text" : "password"}
                                    placeholder="Confirm New Password"
                                    value={confirmNewPassword}
                                    onChange={(e) =>
                                        setConfirmNewPassword(e.target.value)
                                    }
                                    required
                                />
                                <i
                                    onClick={() =>
                                        setShowConfirmPassword(!showConfirmPassword)
                                    }
                                    className={`fas fa-eye${
                                        showConfirmPassword ? "-slash" : ""
                                    }`}
                                />
                            </div>
                            <button type="submit" disabled={loading}>
                                {loading ? "Changing Password..." : "Change Password"}
                            </button>
                        </form>
                    )}
                </>
            )}
        </div>
    );
}