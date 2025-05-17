import React, { useState, useEffect } from "react";
import axios from "axios";

function CreateGroupModal({ token, onClose, onGroupCreated, currentUser }) {
  const [groupName, setGroupName] = useState("");
  const [allUsers, setAllUsers] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [error, setError] = useState(null);
  
  // Fetch users (excluding current user)
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await axios.get("/api/users/", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const otherUsers = res.data.filter((u) => u.id !== currentUser.id);
        setAllUsers(otherUsers);
      } catch (err) {
        setError("Failed to load users");
      }
    };
    fetchUsers();
  }, [token, currentUser]);
  
  const handleCheckboxChange = (id) => {
    if (selectedUsers.includes(id)) {
      setSelectedUsers(selectedUsers.filter((sid) => sid !== id));
    } else {
      setSelectedUsers([...selectedUsers, id]);
    }
  };
  
  const handleCreate = async () => {
    if (!groupName.trim() || selectedUsers.length === 0) {
      setError("Please provide a group name and select at least one user");
      return;
    }
    try {
      await axios.post(
        "/api/chat_groups/",
        { name: groupName.trim(), members: selectedUsers },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      onGroupCreated();
    } catch (err) {
      setError("Failed to create group");
    }
  };
  
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Create a New Group</h2>
        {error && <div className="error-alert">{error}</div>}
        <input
          type="text"
          placeholder="Group Name"
          value={groupName}
          onChange={(e) => setGroupName(e.target.value)}
          className="group-name-input"
        />
        <div className="users-list-container">
          <p>Select Users:</p>
          {allUsers.map((u) => (
            <label key={u.id} className="user-checkbox-label">
              <input
                type="checkbox"
                checked={selectedUsers.includes(u.id)}
                onChange={() => handleCheckboxChange(u.id)}
              />
              {u.username}
            </label>
          ))}
        </div>
        <div className="modal-actions">
          <button className="cancel-button" onClick={onClose}>
            Cancel
          </button>
          <button className="create-button" onClick={handleCreate}>
            Create Group
          </button>
        </div>
      </div>
    </div>
  );
}

export default CreateGroupModal;