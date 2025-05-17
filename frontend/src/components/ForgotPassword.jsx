import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import '../assets/styles/Auth.css';
import '@fortawesome/fontawesome-free/css/all.min.css';

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

export default function ForgotPassword() {
    const [step, setStep] = useState(1);
    const [email, setEmail] = useState("");
    const [otp, setOtp] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [loading, setLoading] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const navigate = useNavigate();

    const handleSendOTP = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        
        try {
            await axios.post('/api/change-password/request-otp/', { email });
            setStep(2);
            setSuccess("OTP sent to your email");
        } catch (error) {
            setError(error.response?.data?.error || 'Failed to send OTP');
        } finally {
            setLoading(false);
        }
    };

    const handleVerifyOTP = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        
        try {
            await axios.post('/api/change-password/verify-otp/', { email, otp });
            setStep(3);
            setSuccess("OTP verified. Please enter your new password.");
        } catch (error) {
            setError(error.response?.data?.error || 'Invalid OTP');
        } finally {
            setLoading(false);
        }
    };

    const handleResetPassword = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        
        // Password validation
        const passwordError = validatePasswordStrength(newPassword);
        if (passwordError) {
            setError(passwordError);
            setLoading(false);
            return;
        }
        
        if (newPassword !== confirmPassword) {
            setError("Passwords don't match");
            setLoading(false);
            return;
        }

        try {
            await axios.post('/api/change-password/reset/', { 
                email, 
                new_password: newPassword,
                otp 
            });
            setSuccess("Password changed successfully!");
            setTimeout(() => navigate('/login'), 2000);
        } catch (error) {
            setError(error.response?.data?.error || 'Password reset failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <h2>Password Recovery</h2>
                {error && <div className="error-message">{error}</div>}
                {success && <div className="success-message">{success}</div>}
                
                {step === 1 && (
                    <form className="auth-form" onSubmit={handleSendOTP}>
                        <div className="form-group">
                            <input
                                type="email"
                                placeholder="Enter your email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                        <button type="submit" disabled={loading}>
                            {loading ? 'Sending...' : 'Send OTP'}
                        </button>
                        <p className="auth-link">
                            Remember password? <Link to="/login">Login here</Link>
                        </p>
                    </form>
                )}

                {step === 2 && (
                    <form className="auth-form" onSubmit={handleVerifyOTP}>
                        <div className="form-group">
                            <input
                                type="text"
                                placeholder="Enter OTP"
                                value={otp}
                                onChange={(e) => setOtp(e.target.value)}
                                required
                            />
                        </div>
                        <button type="submit" disabled={loading}>
                            {loading ? 'Verifying...' : 'Verify OTP'}
                        </button>
                        <p className="auth-link">
                            Didn't receive OTP? <button 
                                type="button" 
                                onClick={handleSendOTP}
                                className="resend-link"
                            >
                                Resend
                            </button>
                        </p>
                    </form>
                )}

                {step === 3 && (
                    <form className="auth-form" onSubmit={handleResetPassword}>
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
                                className={`fas fa-eye${showNewPassword ? "-slash" : ""}`}
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
                                placeholder="Confirm Password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                            />
                            <i
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                className={`fas fa-eye${showConfirmPassword ? "-slash" : ""}`}
                            />
                        </div>
                        <button type="submit" disabled={loading}>
                            {loading ? 'Resetting...' : 'Reset Password'}
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}