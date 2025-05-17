import React, { useState } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import "../assets/styles/Auth.css";

function DeleteAccount() {
    const [step, setStep] = useState(1); // 1: initial, 2: OTP sent
    const [otp, setOtp] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const { logout } = useAuth();
    const navigate = useNavigate();

    const requestDeletion = async () => {
        try {
            setLoading(true);
            setError("");
            await axios.post("/api/delete-account/request/");
            setStep(2);
        } catch (err) {
            setError(err.response?.data?.error || "Failed to send OTP");
        } finally {
            setLoading(false);
        }
    };

    const confirmDeletion = async (e) => {
        e.preventDefault();
        if (!otp) {
            setError("Please enter the OTP");
            return;
        }

        try {
            setLoading(true);
            setError("");
            await axios.post("/api/delete-account/confirm/", { otp });
            await logout();
            navigate("/login", {
                state: { message: "Account successfully deleted" },
            });
        } catch (err) {
            setError(err.response?.data?.error || "Failed to delete account");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <h2>Delete Account</h2>
                {error && <div className="error-message">{error}</div>}

                {step === 1 ? (
                    <div>
                        <p className="warning-text">
                            Warning: This action cannot be undone. All your data
                            will be permanently deleted.
                        </p>
                        <button
                            onClick={requestDeletion}
                            disabled={loading}
                            className="delete-button"
                        >
                            {loading ? "Sending OTP..." : "Delete My Account"}
                        </button>
                    </div>
                ) : (
                    <form onSubmit={confirmDeletion}>
                        <div className="form-group">
                            <input
                                type="text"
                                placeholder="Enter OTP"
                                value={otp}
                                onChange={(e) => setOtp(e.target.value)}
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="confirm-delete-button"
                        >
                            {loading ? "Deleting..." : "Confirm Deletion"}
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}

export default DeleteAccount;
