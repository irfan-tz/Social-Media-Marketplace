import React, { useState, useEffect } from "react";
import axios from "axios";
import "../assets/styles/BlockReport.css";

function ReportUserModal({ userId, username, onClose }) {
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState("");
    const [description, setDescription] = useState("");
    const [evidence, setEvidence] = useState(null);
    const [loading, setLoading] = useState(false);
    const [fetchingCategories, setFetchingCategories] = useState(true);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        const fetchCategories = async () => {
            try {
                const response = await axios.get("/api/report-categories/");
                setCategories(response.data);
            } catch (err) {
                setError("Failed to load report categories");
            } finally {
                setFetchingCategories(false);
            }
        };

        fetchCategories();
    }, []);

    const handleEvidenceChange = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            setError("File size must be less than 5MB");
            e.target.value = null;
            return;
        }

        setEvidence(file);
        setError("");
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedCategory) {
            setError("Please select a reason for reporting");
            return;
        }

        if (!description.trim()) {
            setError("Please provide details about the report");
            return;
        }

        try {
            setLoading(true);
            setError("");

            const formData = new FormData();
            formData.append("reported_user", userId);
            formData.append("category", selectedCategory);
            formData.append("description", description.trim());

            if (evidence) {
                formData.append("evidence", evidence);
            }

            await axios.post("/api/reports/", formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });

            setSuccess(true);
            setTimeout(() => {
                onClose();
            }, 2000);
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to submit report");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="report-modal-overlay" onClick={onClose}>
            <div
                className="report-modal-content"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="report-modal-header">
                    <h2>Report User: {username}</h2>
                    <button className="close-button" onClick={onClose}>
                        <i className="fas fa-times"></i>
                    </button>
                </div>

                {success ? (
                    <div className="success-message">
                        <i className="fas fa-check-circle"></i>
                        <p>
                            Report submitted successfully. Our moderators will
                            review it.
                        </p>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="report-form">
                        {error && <div className="error-message">{error}</div>}

                        <div className="form-group">
                            <label>Reason for reporting:</label>
                            {fetchingCategories ? (
                                <p>Loading categories...</p>
                            ) : (
                                <select
                                    value={selectedCategory}
                                    onChange={(e) =>
                                        setSelectedCategory(e.target.value)
                                    }
                                    required
                                >
                                    <option value="">Select a reason</option>
                                    {categories.map((category) => (
                                        <option
                                            key={category.id}
                                            value={category.id}
                                        >
                                            {category.name}
                                        </option>
                                    ))}
                                </select>
                            )}
                        </div>

                        <div className="form-group">
                            <label>Details:</label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Please provide specific details about the issue..."
                                rows={4}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Evidence (optional):</label>
                            <input
                                type="file"
                                onChange={handleEvidenceChange}
                                accept="image/*,application/pdf"
                            />
                            <small>
                                Upload screenshots or relevant files (Max 5MB,
                                JPG/PNG/PDF)
                            </small>
                        </div>

                        <div className="form-actions">
                            <button
                                type="button"
                                onClick={onClose}
                                className="cancel-button"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={loading || fetchingCategories}
                                className="submit-button"
                            >
                                {loading ? "Submitting..." : "Submit Report"}
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}

export default ReportUserModal;
