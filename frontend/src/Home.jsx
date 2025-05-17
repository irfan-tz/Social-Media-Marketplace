import React, { useState } from 'react';
import '@fortawesome/fontawesome-free/css/all.min.css';
import './Home.css';

function Home() {
    const [posts, setPosts] = useState([
      { 
        id: 1, 
        user: { 
          name: 'Buck Vernon', 
          avatar: 'https://yt3.googleusercontent.com/eztDhvc-evvEQVMeHp5NggBviGu--Fy30pv76ftDnSwuc4ARJGbQC7_0iWKGPEX28gf_ess=s160-c-k-c0x00ffffff-no-rj' 
        }, 
        content: `Now that I've left that place, 
      I feel like someone for the first time in my life.`, 
        image: 'https://www.lordhuron.com/wp-content/uploads/sites/1892/2025/01/artwork-440x440-1-compressed.jpg', 
        likes: 1313, 
        comments: 8, 
        timestamp: '2 hours ago' 
      },
      {
        id: 2,
        user: {
          name: 'SonicSpectacle',
          avatar: 'https://api.dicebear.com/9.x/lorelei/svg?seed=Vivian'
        },
        content: 'No more.',
        image: 'https://i1.sndcdn.com/artworks-ddyN2IQ4E3lmQUzd-zl0jkA-t500x500.jpg',
        likes: 156,
        comments: 12,
        timestamp: '5 hours ago'
      }
    ]);
  
    const [newPost, setNewPost] = useState('');
  
    const handlePostSubmit = (e) => {
      e.preventDefault();
      if (!newPost.trim()) return;
  
      const post = {
        id: posts.length + 1,
        user: {
          name: 'Current User',
          avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=User'
        },
        content: newPost,
        likes: 0,
        comments: 0,
        timestamp: 'Just now'
      };
  
      setPosts([post, ...posts]);
      setNewPost('');
    };
  
    return (
      <div className="home-container fade-in">
        <div className="post-form-container slide-up">
          <form onSubmit={handlePostSubmit}>
            <div className="post-input-wrapper">
              <img 
                src="https://api.dicebear.com/7.x/avataaars/svg?seed=User" 
                alt="User Avatar" 
                className="user-avatar"
              />
              <textarea
                value={newPost}
                onChange={(e) => setNewPost(e.target.value)}
                placeholder="What's on your mind?"
                className="post-input"
              />
            </div>
            <div className="post-actions">
              <button type="button" className="btn-secondary">
                <i className="fas fa-image"></i> Add Image
              </button>
              <button type="submit" className="btn-primary">Post</button>
            </div>
          </form>
        </div>
  
        <div className="posts-container">
          {posts.map((post) => (
            <div key={post.id} className="post-card slide-up">
              <div className="post-header">
                <img src={post.user.avatar} alt={post.user.name} className="user-avatar" />
                <div className="post-meta">
                  <h3>{post.user.name}</h3>
                  <span className="timestamp">{post.timestamp}</span>
                </div>
              </div>
              
              <p className="post-content">{post.content}</p>
              {post.image && (
                <img src={post.image} alt="Post" className="post-image" />
              )}
              
              <div className="post-actions">
                <button className="action-button">
                  <i className="fas fa-heart"></i> {post.likes}
                </button>
                <button className="action-button">
                  <i className="fas fa-comment"></i> {post.comments}
                </button>
                <button className="action-button">
                  <i className="fas fa-share"></i>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  
  export default Home;
  