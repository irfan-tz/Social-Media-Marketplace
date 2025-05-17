import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import '../assets/styles/Auth.css';

export default function Registration() {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState({});
  const [generalError, setGeneralError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [otp, setOtp] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const navigate = useNavigate();

  // Validate password strength
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

  // Validate password match only when both fields have values
  const validatePasswordMatch = () => {
    // Only validate if both password fields have values
    if (!formData.password || !formData.confirmPassword) {
      return true; // Skip validation if either field is empty
    }

    if (formData.password !== formData.confirmPassword) {
      setErrors(prev => ({ ...prev, confirmPassword: "Passwords do not match!" }));
      return false;
    }
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors.confirmPassword;
      return newErrors;
    });
    return true;
  };

  const getCSRFToken = () => {
    return document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1] || "";
  };

  const handleSendOTP = async () => {
    if (!formData.email || !formData.email.includes('@')) {
      setErrors(prev => ({ ...prev, email: "Please enter a valid email address" }));
      return;
    }

    try {
      setIsSubmitting(true);
      await axios.post("/api/send-otp/", { email: formData.email }, {
        withCredentials: true,
        headers: { 'X-CSRFToken': getCSRFToken() }
      });
      setOtpSent(true);
      setErrors(prev => ({ ...prev, email: undefined }));
    } catch (error) {
      const errorData = error.response?.data || {};
      const newErrors = {};

      for (const [field, messages] of Object.entries(errorData)) {
        newErrors[field] = Array.isArray(messages) ? messages.join(' ') : messages;
      }

      if (errorData.email?.some(msg => msg.includes('Email provider is not trusted'))) {
        newErrors.email = "Please use a valid and trusted email provider (e.g., Gmail, Outlook).";
      }

      setErrors(newErrors);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!otp || otp.length < 6) {
      setErrors(prev => ({ ...prev, otp: "Please enter the complete 6-digit OTP" }));
      return;
    }

    try {
      setIsSubmitting(true);
      await axios.post("/api/verify-otp/", { email: formData.email, otp });
      setOtpVerified(true);
      setErrors(prev => ({ ...prev, otp: undefined }));
    } catch (error) {
      const errorMessage = error.response?.data?.error || "Invalid OTP. Please try again.";
      setErrors(prev => ({ ...prev, otp: errorMessage }));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!otpVerified) return;

    setErrors({});
    setGeneralError("");
    setIsSubmitting(true);

    // Client-side validation
    const newErrors = {};
    if (!formData.username.trim()) {
      newErrors.username = "Username is required";
    }
    if (!formData.password) {
      newErrors.password = "Password is required";
    } else {
      // Validate password strength
      const passwordError = validatePasswordStrength(formData.password);
      if (passwordError) {
        newErrors.password = passwordError;
      }
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setIsSubmitting(false);
      return;
    }

    if (!validatePasswordMatch()) {
      setIsSubmitting(false);
      return;
    }

    const formPayload = new URLSearchParams();
    formPayload.append('username', formData.username);
    formPayload.append('email', formData.email);
    formPayload.append('password', formData.password);

    try {
      const response = await axios.post("/api/register/", formPayload, {
        withCredentials: true,
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      if (response.status === 201) {
        navigate("/login", { state: { registrationSuccess: true } });
      }
    } catch (error) {
      if (error.response?.data?.user) {
        navigate("/login", {
          state: { registrationSuccess: true, message: "Account created successfully!" }
        });
      } else {
        const errorData = error.response?.data || {};
        const serverErrors = {};

        for (const [field, messages] of Object.entries(errorData)) {
          serverErrors[field] = Array.isArray(messages) ? messages.join(' ') : messages;
        }

        setErrors(serverErrors);
        setGeneralError(error.response?.data?.detail || "Registration failed. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e) => {
    const { id, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [id]: value
    }));

    // Clear existing errors for this field
    if (errors[id]) {
      setErrors(prev => ({ ...prev, [id]: undefined }));
    }

    // Validate password strength
    if (id === 'password') {
      if (value) {
        const passwordError = validatePasswordStrength(value);
        if (passwordError) {
          setErrors(prev => ({ ...prev, password: passwordError }));
        }
      }

      // If confirm password has a value, check matching
      if (formData.confirmPassword) {
        if (value !== formData.confirmPassword) {
          setErrors(prev => ({ ...prev, confirmPassword: "Passwords do not match!" }));
        } else {
          setErrors(prev => {
            const newErrors = { ...prev };
            delete newErrors.confirmPassword;
            return newErrors;
          });
        }
      }
    }

    // Check password match when changing confirm password
    if (id === 'confirmPassword' && formData.password && value) {
      if (formData.password !== value) {
        setErrors(prev => ({ ...prev, confirmPassword: "Passwords do not match!" }));
      } else {
        setErrors(prev => {
          const newErrors = { ...prev };
          delete newErrors.confirmPassword;
          return newErrors;
        });
      }
    }
  };

  const handleEmailKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSendOTP();
    }
  };

  const handleOtpKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleVerifyOTP();
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Create Account</h2>
        <p className="auth-description">
          Complete the following steps to create your account:
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="step-indicator">
            <div className={`step ${!otpSent ? 'active' : 'completed'}`}>1. Email</div>
            <div className={`step ${otpSent && !otpVerified ? 'active' : (otpVerified ? 'completed' : '')}`}>2. Verify OTP</div>
            <div className={`step ${otpVerified ? 'active' : ''}`}>3. Complete Registration</div>
          </div>

          {generalError && (
            <div className="auth-error-container">
              <div className="auth-field-error">{generalError}</div>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address:</label>
            <div className="input-with-button">
              <input
                type="email"
                id="email"
                placeholder="Enter your email address"
                value={formData.email}
                onChange={handleChange}
                onKeyDown={handleEmailKeyPress}
                className={errors.email ? "error" : ""}
                required
                disabled={otpSent}
              />
              <button
                type="button"
                onClick={handleSendOTP}
                disabled={otpSent || isSubmitting}
                className={otpSent ? "success" : ""}
              >
                {isSubmitting ? "Sending..." : (otpSent ? "✓ Sent" : "Send OTP")}
              </button>
            </div>
            {errors.email && <div className="field-error" aria-live="polite">{errors.email}</div>}
            {!otpSent && !errors.email && (
              <div className="info-message">Enter your email and click "Send OTP" to receive a verification code.</div>
            )}
            {otpSent && !errors.email && (
              <div className="success-message">✓ OTP sent to {formData.email}</div>
            )}
          </div>

          {otpSent && (
            <div className="form-group">
              <label htmlFor="otp-input">Verification Code (OTP):</label>
              <div className="input-with-button">
                <input
                  type="text"
                  id="otp-input"
                  placeholder="Enter 6-digit code"
                  value={otp}
                  onChange={(e) => {
                    setOtp(e.target.value);
                    if (errors.otp) setErrors(prev => ({ ...prev, otp: undefined }));
                  }}
                  onKeyDown={handleOtpKeyPress}
                  className={errors.otp ? "error" : ""}
                  required
                  disabled={otpVerified}
                  maxLength="6"
                />
                <button
                  type="button"
                  onClick={handleVerifyOTP}
                  disabled={otpVerified || isSubmitting}
                  className={otpVerified ? "success" : ""}
                >
                  {isSubmitting ? "Verifying..." : (otpVerified ? "✓ Verified" : "Verify OTP")}
                </button>
              </div>
              {errors.otp ? (
                <div className="field-error" aria-live="polite">{errors.otp}</div>
              ) : (
                <div className="info-message">
                  Check your email (including spam folder) for the 6-digit code
                </div>
              )}
              {otpVerified && (
                <div className="success-message">✓ Email verified successfully!</div>
              )}
            </div>
          )}

          {otpVerified && (
            <>
              <div className="form-group">
                <input
                  type="text"
                  id="username"
                  placeholder="Username"
                  value={formData.username}
                  onChange={handleChange}
                  className={errors.username ? "error" : ""}
                  required
                />
                {errors.username && <div className="field-error" aria-live="polite">{errors.username}</div>}
              </div>

              <div className="form-group password-group">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleChange}
                  className={errors.password ? "error" : ""}
                  required
                />
                <i
                  onClick={() => setShowPassword(!showPassword)}
                  className={`fas fa-eye${showPassword ? '-slash' : ''} password-toggle-icon`}
                />
                {errors.password && <div className="field-error" aria-live="polite">{errors.password}</div>}
                {!errors.password && (
                  <div className="info-message">
                    Password must be at least 8 characters with at least one number and one special character.
                  </div>
                )}
              </div>

              <div className="form-group password-group">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  id="confirmPassword"
                  placeholder="Confirm Password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={errors.confirmPassword ? "error" : ""}
                  required
                />
                <i
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className={`fas fa-eye${showConfirmPassword ? '-slash' : ''} password-toggle-icon`}
                />
                {errors.confirmPassword && (
                  <div className="field-error" aria-live="polite">{errors.confirmPassword}</div>
                )}
              </div>

              <div className="form-group">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={isSubmitting ? "submitting" : ""}
                >
                  {isSubmitting ? "Creating Account..." : "Create Account"}
                </button>
              </div>
            </>
          )}

          <div className="form-footer">
            <p className="auth-link">
              Already have an account? <Link to="/login">Login here</Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}