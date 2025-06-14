import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-gray-800 p-4 text-white">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">AI Splitwise</Link>
        <div>
          {isAuthenticated ? (
            <>
              <Link to="/profile" className="mr-4 hover:text-gray-300">Profile</Link>
              <Link to="/groups" className="mr-4 hover:text-gray-300">Groups</Link>
              <Link to="/expenses" className="mr-4 hover:text-gray-300">Expenses</Link>
              <Link to="/payments" className="mr-4 hover:text-gray-300">Payments</Link>
              <Link to="/reports" className="mr-4 hover:text-gray-300">Reports</Link>
              <button onClick={handleLogout} className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="mr-4 hover:text-gray-300">Login</Link>
              <Link to="/signup" className="hover:text-gray-300">Sign Up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;