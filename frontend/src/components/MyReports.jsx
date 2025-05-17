import React, { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import "../assets/styles/MyReports.css";

function MyReports() {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchReports = async () => {
            try {
                setLoading(true);
                const response = await axios.get("/api/my-reports/");
                setReports(response.data);
            } catch (err) {
                setError("Failed to load your reports");
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchReports();
    }, []);

    const getStatusClass = (status) => {
        switch (status) {
            case "pending":
                return "status-pending";
            case "reviewing":
                return "status-reviewing";
            case "resolved":
                return "status-resolved";
            case "action_taken":
                return "status-action";
            default:
                return "";
        }
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return (
            date.toLocaleDateString() +
            " " +
            date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        );
    };

    return (
        <div className="my-reports-container">
            <h1>My Reports</h1>

            {error && <div className="error-message">{error}</div>}

            {loading ? (
                <div className="loading-indicator">Loading reports...</div>
            ) : reports.length === 0 ? (
                <div className="no-reports-message">
                    <p>You haven't submitted any reports yet.</p>
                </div>
            ) : (
                <div className="reports-list">
                    {reports.map((report) => (
                        <div key={report.id} className="report-card">
                            <div className="report-header">
                                <div className="report-info">
                                    <h3>
                                        Report against:{" "}
                                        {report.reported_username}
                                    </h3>
                                    <span className="report-date">
                                        Submitted on:{" "}
                                        {formatDate(report.created_at)}
                                    </span>
                                </div>
                                <span
                                    className={`report-status ${getStatusClass(report.status)}`}
                                >
                                    {report.status
                                        .replace("_", " ")
                                        .replace(/\b\w/g, (l) =>
                                            l.toUpperCase(),
                                        )}
                                </span>
                            </div>

                            <div className="report-details">
                                <p>
                                    <strong>Reason:</strong>{" "}
                                    {report.category_name}
                                </p>
                                <p>
                                    <strong>Details:</strong>{" "}
                                    {report.description}
                                </p>
                                {report.evidence && (
                                    <p className="evidence-info">
                                        <strong>Evidence:</strong> Provided
                                    </p>
                                )}
                            </div>

                            <div className="report-footer">
                                <div className="help-text">
                                    {report.status === "pending" &&
                                        "Your report is waiting to be reviewed by our moderation team."}
                                    {report.status === "reviewing" &&
                                        "Our moderation team is currently reviewing your report."}
                                    {report.status === "resolved" &&
                                        "We've reviewed your report and determined no further action is required."}
                                    {report.status === "action_taken" &&
                                        "We've taken action based on your report. Thank you for helping keep our community safe."}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default MyReports;
