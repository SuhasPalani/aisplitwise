import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

interface UserProfile {
  username: string;
  email: string;
  friends: string[];
  created_at: string;
}

const UserProfilePage: React.FC = () => {
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const response = await api.get<UserProfile>('/users/me'); // Calling user_service
        setUserProfile(response.data);
      } catch (err: any) {
        console.error("Error fetching user profile:", err);
        if (err.response?.status === 401) {
          logout();
          navigate('/login');
        }
        setError(err.response?.data?.detail || 'Failed to fetch user profile.');
      } finally {
        setLoading(false);
      }
    };
    fetchUserProfile();
  }, [logout, navigate]);

  if (loading) return <div className="text-center mt-8">Loading profile...</div>;
  if (error) return <div className="text-center mt-8 text-red-500">Error: {error}</div>;
  if (!userProfile) return <div className="text-center mt-8">No profile data available.</div>;

  return (
    <div className="container mx-auto p-4 bg-white shadow-md rounded-lg mt-8">
      <h1 className="text-3xl font-bold mb-6 text-center">User Profile</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <p className="text-lg font-semibold">Username:</p>
          <p className="text-gray-700">{userProfile.username}</p>
        </div>
        <div>
          <p className="text-lg font-semibold">Email:</p>
          <p className="text-gray-700">{userProfile.email}</p>
        </div>
        <div>
          <p className="text-lg font-semibold">Joined:</p>
          <p className="text-gray-700">{new Date(userProfile.created_at).toLocaleDateString()}</p>
        </div>
        <div>
          <p className="text-lg font-semibold">Friends:</p>
          {userProfile.friends.length > 0 ? (
            <ul className="list-disc list-inside text-gray-700">
              {userProfile.friends.map((friend, index) => (
                <li key={index}>{friend}</li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-700">No friends yet.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfilePage;