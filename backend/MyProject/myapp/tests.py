# import React, { useState, useEffect, useRef } from "react";
# import axios from "axios";
# import { useAuth } from "../context/AuthContext";
# import { useNavigate, useLocation } from "react-router-dom";
# import "@fortawesome/fontawesome-free/css/all.min.css";
# import "../assets/styles/Messaging.css";

# export default function Messaging() {
#     const [messages, setMessages] = useState([]);
#     const [newMessage, setNewMessage] = useState("");
#     const [attachment, setAttachment] = useState(null);
#     const [receiverId, setReceiverId] = useState("");
#     const [users, setUsers] = useState([]);
#     const [loading, setLoading] = useState(false);
#     const [error, setError] = useState(null);
#     const { token, user } = useAuth();
#     const messageListRef = useRef(null);
#     const navigate = useNavigate();
#     const location = useLocation();

#     // Helper function to render attachments
#     const renderAttachment = (msg) => {
#         if (!msg.attachment_url) return null;

#         // Use the provided content type from the serializer, if available
#         const contentType = msg.attachment_content_type;

#         if (contentType) {
#             if (contentType.startsWith("video/")) {
#                 return (
#                     <div className="video-wrapper">
#                         <video controls>
#                             <source
#                                 src={msg.attachment_url}
#                                 type={contentType}
#                             />
#                             Your browser does not support the video tag.
#                         </video>
#                     </div>
#                 );
#             } else if (contentType.startsWith("image/")) {
#                 return (
#                     <img
#                         src={msg.attachment_url}
#                         alt="attachment"
#                         style={{ maxWidth: "100%", maxHeight: "400px" }}
#                     />
#                 );
#             }
#         }
#         // Fallback: if content type is missing, use URL extension
#         const lowerUrl = msg.attachment_url.toLowerCase();
#         if (
#             lowerUrl.endsWith(".mp4") ||
#             lowerUrl.endsWith(".webm") ||
#             lowerUrl.endsWith(".ogg")
#         ) {
#             return (
#                 <div className="video-wrapper">
#                     <video controls>
#                         <source src={msg.attachment_url} type="video/mp4" />
#                         Your browser does not support the video tag.
#                     </video>
#                 </div>
#             );
#         } else if (
#             lowerUrl.endsWith(".jpg") ||
#             lowerUrl.endsWith(".jpeg") ||
#             lowerUrl.endsWith(".png") ||
#             lowerUrl.endsWith(".gif")
#         ) {
#             return (
#                 <img
#                     src={msg.attachment_url}
#                     alt="attachment"
#                     style={{ maxWidth: "100%", maxHeight: "400px" }}
#                 />
#             );
#         }
#         return <p>Unsupported attachment type.</p>;
#     };

#     useEffect(() => {
#         const fetchData = async () => {
#             try {
#                 setLoading(true);
#                 const usersResponse = await axios.get("/api/users/", {
#                     headers: { Authorization: `Bearer ${token}` },
#                 });
#                 const sortedUsers = [...usersResponse.data].sort((a, b) => {
#                     if (
#                         a.last_interaction === null &&
#                         b.last_interaction === null
#                     )
#                         return 0;
#                     if (a.last_interaction === null) return 1;
#                     if (b.last_interaction === null) return -1;
#                     return (
#                         new Date(b.last_interaction) -
#                         new Date(a.last_interaction)
#                     );
#                 });
#                 setUsers(sortedUsers);

#                 const messagesResponse = await axios.get("/api/messages/", {
#                     headers: { Authorization: `Bearer ${token}` },
#                 });
#                 setMessages(messagesResponse.data);

#                 // Check if we were directed here to message a specific user
#                 if (location.state && location.state.username) {
#                     const targetUser = sortedUsers.find(
#                         (u) => u.username === location.state.username,
#                     );
#                     if (targetUser) {
#                         setReceiverId(targetUser.id);
#                     }
#                 }
#             } catch (err) {
#                 setError(err.response?.data?.detail || "Failed to load data");
#             } finally {
#                 setLoading(false);
#             }
#         };
#         fetchData();
#     }, [token, location.state]);

#     useEffect(() => {
#         const intervalId = setInterval(async () => {
#             try {
#                 const messagesResponse = await axios.get("/api/messages/", {
#                     headers: { Authorization: `Bearer ${token}` },
#                 });
#                 setMessages(messagesResponse.data);
#                 const usersResponse = await axios.get("/api/users/", {
#                     headers: { Authorization: `Bearer ${token}` },
#                 });
#                 const sortedUsers = [...usersResponse.data].sort((a, b) => {
#                     if (
#                         a.last_interaction === null &&
#                         b.last_interaction === null
#                     )
#                         return 0;
#                     if (a.last_interaction === null) return 1;
#                     if (b.last_interaction === null) return -1;
#                     return (
#                         new Date(b.last_interaction) -
#                         new Date(a.last_interaction)
#                     );
#                 });
#                 setUsers(sortedUsers);
#             } catch (err) {
#                 console.error("Polling error:", err);
#             }
#         }, 1000);
#         return () => clearInterval(intervalId);
#     }, [token]);

#     useEffect(() => {
#         if (messageListRef.current) {
#             const { scrollTop, scrollHeight, clientHeight } =
#                 messageListRef.current;
#             if (scrollHeight - scrollTop - clientHeight < 100) {
#                 messageListRef.current.scrollTop = scrollHeight;
#             }
#         }
#     }, [messages, receiverId]);

#     const handleAttachmentChange = (e) => {
#         const file = e.target.files[0];
#         if (!file) return;
#         const allowedTypes = [
#             "image/jpeg",
#             "image/png",
#             "image/gif",
#             "video/mp4",
#             "video/webm",
#             "video/ogg",
#         ];
#         const maxSize = 10 * 1024 * 1024;
#         if (!allowedTypes.includes(file.type)) {
#             setError("Only images and videos are allowed.");
#             e.target.value = null;
#             return;
#         }
#         if (file.size > maxSize) {
#             setError("File size must be less than 10MB.");
#             e.target.value = null;
#             return;
#         }
#         setAttachment(file);
#         setError(null);
#     };

#     const sendMessage = async (e) => {
#         e.preventDefault();
#         setError(null);
#         if (!receiverId || (!newMessage.trim() && !attachment)) {
#             setError("Select a receiver and add a message or attachment.");
#             return;
#         }
#         try {
#             setLoading(true);
#             const friendshipCheck = await axios.get(`/api/friendships/?receiver=${receiverId}`, {
#                 headers: { Authorization: `Bearer ${token}` }
#             });
    
#             const isFriend = friendshipCheck.data.some(f => 
#                 f.status === 'accepted' && 
#                 (f.sender.id === user.id || f.receiver.id === user.id)
#             );
    
#             if (!isFriend) {
#                 setError("You must be friends to message this user");
#                 return;
#             }
#             const formData = new FormData();
#             formData.append("receiver", parseInt(receiverId));
#             if (newMessage.trim()) {
#                 formData.append("content", newMessage.trim());
#             }
#             if (attachment) {
#                 formData.append("attachment", attachment);
#             }
#             await axios.post("/api/messages/", formData, {
#                 headers: {
#                     Authorization: `Bearer ${token}`,
#                     "Content-Type": "multipart/form-data",
#                 },
#             });
#             const updatedMessages = await axios.get("/api/messages/", {
#                 headers: { Authorization: `Bearer ${token}` },
#             });
#             setMessages(updatedMessages.data);
#             setNewMessage("");
#             setAttachment(null);
#             const fileInput = document.getElementById("attachmentInput");
#             if (fileInput) fileInput.value = "";
#     } catch (err) {
#         if (err.response?.status === 403) {
#             setError("You must be friends to message this user");
#         } else {
#             setError(err.response?.data?.detail || "Failed to send message");
#         }
#     } finally {
#         setLoading(false);
#     }
# };

#     const isCurrentUserSender = (message) =>
#         message.sender === user?.id ||
#         message.sender_username === user?.username;

#     const selectedUser = users.find(
#         (u) => u.id.toString() === receiverId.toString(),
#     );

#     const filteredMessages = messages
#         .filter(
#             (msg) =>
#                 msg.sender.toString() === receiverId.toString() ||
#                 msg.receiver.toString() === receiverId.toString(),
#         )
#         .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

#     const filteredUsers = users.filter(
#         (contact) => contact.id.toString() !== user?.id?.toString(),
#     );

#     return (
#         <div
#             className="page-container full-width-page"
#             style={{ width: "100vw", maxWidth: "100vw", padding: 0, margin: 0 }}
#         >
#             <div
#                 className="messaging-wrapper"
#                 style={{ width: "100%", maxWidth: "100%" }}
#             >
#                 {error && <div className="error-message">{error}</div>}
#                 {loading && <div className="loading-overlay">Loading...</div>}

#                 <div className="chat-sidebar">
#                     <h2>Contacts</h2>
#                     <div className="chat-list">
#                         {filteredUsers.map((contact) => (
#                             <div
#                                 key={contact.id}
#                                 className={`chat-item ${
#                                     receiverId === contact.id ? "active" : ""
#                                 }`}
#                             >
#                                 <div
#                                     className="chat-avatar-wrapper"
#                                     onClick={() => setReceiverId(contact.id)}
#                                 >
#                                     <img
#                                         src={
#                                             contact.profile_picture_url
#                                                 ? contact.profile_picture_url
#                                                 : `https://api.dicebear.com/7.x/avataaars/svg?seed=${contact.username}`
#                                         }
#                                         alt={contact.username}
#                                         className="chat-avatar"
#                                     />
#                                 </div>
#                                 <div className="chat-info">
#                                     <h3
#                                         onClick={() =>
#                                             navigate(
#                                                 `/users/${contact.username}`,
#                                             )
#                                         }
#                                         style={{ cursor: "pointer" }}
#                                     >
#                                         {contact.username}
#                                         <i
#                                             className="fas fa-external-link-alt"
#                                             style={{
#                                                 fontSize: "0.7em",
#                                                 marginLeft: "5px",
#                                             }}
#                                         ></i>
#                                     </h3>
#                                     <div
#                                         onClick={() =>
#                                             setReceiverId(contact.id)
#                                         }
#                                         style={{ cursor: "pointer" }}
#                                     >
#                                         {contact.last_interaction && (
#                                             <small className="last-interaction">
#                                                 Last message:{" "}
#                                                 {new Date(
#                                                     contact.last_interaction,
#                                                 ).toLocaleString()}
#                                             </small>
#                                         )}
#                                     </div>
#                                 </div>
#                             </div>
#                         ))}
#                     </div>
#                 </div>

#                 <div className="chat-main">
#                     <div className="chat-header">
#                         <h2>
#                             {selectedUser ? (
#                                 <>
#                                     <img
#                                         src={
#                                             selectedUser.profile_picture_url ||
#                                             `https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedUser.username}`
#                                         }
#                                         alt={selectedUser.username}
#                                         className="chat-avatar"
#                                         style={{
#                                             width: "32px",
#                                             height: "32px",
#                                             marginRight: "8px",
#                                         }}
#                                     />
#                                     Chat with
#                                     <span
#                                         onClick={() =>
#                                             navigate(
#                                                 `/users/${selectedUser.username}`,
#                                             )
#                                         }
#                                         style={{
#                                             cursor: "pointer",
#                                             textDecoration: "underline",
#                                             marginLeft: "5px",
#                                         }}
#                                     >
#                                         {selectedUser.username}
#                                         <i
#                                             className="fas fa-external-link-alt"
#                                             style={{
#                                                 fontSize: "0.7em",
#                                                 marginLeft: "5px",
#                                             }}
#                                         ></i>
#                                     </span>
#                                 </>
#                             ) : (
#                                 "Select a contact"
#                             )}
#                         </h2>
#                     </div>

#                     <div className="message-list" ref={messageListRef}>
#                         {filteredMessages.length > 0
#                             ? filteredMessages.map((msg) => (
#                                   <div
#                                       key={msg.id}
#                                       className={`message ${
#                                           isCurrentUserSender(msg)
#                                               ? "sent"
#                                               : "received"
#                                       }`}
#                                   >
#                                       <div className="message-content">
#                                           {msg.attachment_url && (
#                                               <div className="attachment-preview">
#                                                   {renderAttachment(msg)}
#                                               </div>
#                                           )}
#                                           {(!msg.attachment_url ||
#                                               (msg.content &&
#                                                   msg.content.toLowerCase() !==
#                                                       "attachment")) && (
#                                               <p>
#                                                   {msg.decrypted_content ||
#                                                       msg.content}
#                                               </p>
#                                           )}
#                                       </div>
#                                       <span className="message-time">
#                                           {new Date(
#                                               msg.timestamp,
#                                           ).toLocaleString([], {
#                                               year: "numeric",
#                                               month: "2-digit",
#                                               day: "2-digit",
#                                               hour: "2-digit",
#                                               minute: "2-digit",
#                                           })}
#                                       </span>
#                                   </div>
#                               ))
#                             : !loading && (
#                                   <p className="no-messages">
#                                       No messages yet. Start a conversation!
#                                   </p>
#                               )}
#                     </div>

#                     <form className="message-input" onSubmit={sendMessage}>
#                         {error && <div className="form-error">{error}</div>}
#                         <input
#                             type="text"
#                             value={newMessage}
#                             onChange={(e) => {
#                                 setNewMessage(e.target.value);
#                                 setError(null); // Clear error when user types
#                             }}
#                             placeholder={
#                                 receiverId
#                                     ? "Type a message..."
#                                     : "Select a contact first"
#                             }
#                             disabled={loading || !receiverId}
#                         />
#                         <input
#                             type="file"
#                             accept="image/*,video/*"
#                             onChange={handleAttachmentChange}
#                             style={{ display: "none" }}
#                             id="attachmentInput"
#                         />
#                         <label
#                             htmlFor="attachmentInput"
#                             className="attach-button"
#                         >
#                             <i className="fas fa-paperclip"></i>
#                             {attachment && (
#                                 <span className="attachment-indicator"></span>
#                             )}
#                         </label>
#                         {attachment && (
#                             <div className="attachment-preview-container">
#                                 <div className="attachment-preview">
#                                     {attachment.type.startsWith("image/") ? (
#                                         <img
#                                             src={URL.createObjectURL(
#                                                 attachment,
#                                             )}
#                                             alt="Attachment preview"
#                                         />
#                                     ) : attachment.type.startsWith("video/") ? (
#                                         <video controls>
#                                             <source
#                                                 src={URL.createObjectURL(
#                                                     attachment,
#                                                 )}
#                                                 type={attachment.type}
#                                             />
#                                         </video>
#                                     ) : (
#                                         <div className="file-icon">
#                                             <i className="fas fa-file"></i>
#                                             <span>{attachment.name}</span>
#                                         </div>
#                                     )}
#                                 </div>
#                                 <button
#                                     className="remove-attachment"
#                                     onClick={() => {
#                                         setAttachment(null);
#                                         document.getElementById(
#                                             "attachmentInput",
#                                         ).value = "";
#                                     }}
#                                 >
#                                     <i className="fas fa-times"></i>
#                                 </button>
#                             </div>
#                         )}
#                         <button
#                             type="submit"
#                             className="send-button"
#                             disabled={
#                                 loading ||
#                                 !receiverId ||
#                                 (!newMessage.trim() && !attachment)
#                             }
#                         >
#                             <i className="fas fa-paper-plane"></i>
#                         </button>
#                     </form>
#                 </div>
#             </div>
#         </div>
#     );
# }

