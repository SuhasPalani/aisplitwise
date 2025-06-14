import React from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

const HomePage: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleFetchMe = async () => {
    try {
      const response = await api.get('/auth/me'); // Or /users/me depending on which one you want to call
      alert(JSON.stringify(response.data, null, 2));
    } catch (error: any) {
      if (error.response && error.response.status === 401) {
        logout(); // Token expired or invalid
        navigate('/login');
      }
      alert('Error fetching user data: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md text-center">
        <h1 className="text-4xl font-bold mb-4">Welcome to AI Splitwise!</h1>
        {isAuthenticated ? (
          <>
            <p className="text-lg text-gray-700 mb-6">You are logged in. Explore the features!</p>
            <div className="space-x-4">
              <button 
                onClick={() => navigate('/expenses')} 
                className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
              >
                Go to Expenses
              </button>
              <button 
                onClick={handleFetchMe} 
                className="bg-indigo-500 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded"
              >
                Fetch My Info (Auth Service)
              </button>
            </div>
          </>
        ) : (
          <p className="text-lg text-gray-700">Please login or sign up to continue.</p>
        )}
      </div>
    </div>
  );
};

export default HomePage;