import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AuthForm from '../components/AuthForm';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

const SignupPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth(); // Log in immediately after successful signup
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSignup = async (data: any) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.post('/auth/signup', data);
      alert('Signup successful for user: ' + response.data.username);

      // Attempt to log in the user immediately after successful signup
      const loginFormData = new URLSearchParams();
      loginFormData.append('username', data.username);
      loginFormData.append('password', data.password);

      const loginResponse = await api.post('/auth/login', loginFormData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      login(loginResponse.data.access_token);
      navigate('/');
    } catch (err: any) {
      console.error("Signup error:", err);
      setError(err.response?.data?.detail || 'Signup failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="w-full max-w-md">
        <AuthForm type="signup" onSubmit={handleSignup} isLoading={isLoading} error={error} />
        <p className="mt-4 text-center text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-500 hover:underline">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
};

export default SignupPage;