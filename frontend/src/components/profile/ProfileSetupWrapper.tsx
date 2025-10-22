import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';
import ProfileSetup from './ProfileSetup';
import LoadingSpinner from '../common/LoadingSpinner';

interface ProfileStatus {
  is_setup_complete: boolean;
  missing_sections: string[];
  profile_data: any;
}

const API_BASE_URL = 'http://127.0.0.1:8100/api/v1';

const ProfileSetupWrapper: React.FC = () => {
  const { user, isNewUser } = useAuth();
  const [searchParams] = useSearchParams();
  const isUpdateMode = searchParams.get('mode') === 'update';
  const [profileStatus, setProfileStatus] = useState<ProfileStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      checkProfileStatus();
    }
  }, [user]);

  const checkProfileStatus = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const response = await axios.get(`${API_BASE_URL}/profile-setup/status`, { headers });
      setProfileStatus(response.data);
      
    } catch (err) {
      console.error('Error checking profile status:', err);
      setError('Failed to check profile status');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 mb-4">Error: {error}</div>
          <button 
            onClick={checkProfileStatus}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // If this is a new user, show profile setup regardless of profile status
  if (isNewUser) {
    return <ProfileSetup />;
  }

  // If this is an existing user in update mode, allow them to update their profile
  if (isUpdateMode) {
    return <ProfileSetup />;
  }

  // If this is an existing user who navigated here without update mode, redirect to dashboard
  // (existing users should go to dashboard even if profile is incomplete)
  window.location.href = '/dashboard';
  return null;
};

export default ProfileSetupWrapper; 