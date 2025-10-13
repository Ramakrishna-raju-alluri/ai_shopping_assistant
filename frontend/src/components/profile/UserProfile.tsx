import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../common/Button';

interface UserProfileProps {
  onClose: () => void;
}

const UserProfile: React.FC<UserProfileProps> = ({ onClose }) => {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    onClose();
  };

  return (
    <div className="card p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <span className="mr-3 text-2xl">👤</span>
          User Profile
        </h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors text-xl w-8 h-8 rounded-full hover-bg-gray-100 flex items-center justify-center"
          aria-label="Close profile"
        >
          ✕
        </button>
      </div>
      
      <div className="space-y-6">
        {/* User Avatar and Basic Info */}
        <div className="bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 p-6 rounded-2xl border border-blue-100">
          <div className="flex items-center">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-2xl mr-4 shadow-lg">
              {user?.name?.charAt(0) || user?.username?.charAt(0) || 'U'}
            </div>
            <div className="flex-1">
              <h4 className="font-bold text-gray-900 text-xl mb-1">{user?.name || 'User'}</h4>
              <p className="text-gray-600 text-sm font-medium">@{user?.username}</p>
              <div className="flex items-center mt-2">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                <span className="text-xs text-green-600 font-medium">Active</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* User Details */}
        <div className="space-y-4">
          <div className="bg-white bg-opacity-80 backdrop-blur-sm p-5 rounded-xl border border-gray-100 shadow-sm hover-shadow-md transition-shadow">
            <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">User ID</label>
            <p className="text-sm text-gray-900 font-mono bg-gray-50 px-3 py-2 rounded-lg border border-gray-200">{user?.user_id}</p>
          </div>
          
          <div className="bg-white bg-opacity-80 backdrop-blur-sm p-5 rounded-xl border border-gray-100 shadow-sm hover-shadow-md transition-shadow">
            <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">Username</label>
            <p className="text-sm text-gray-900 font-medium">{user?.username}</p>
          </div>
          
          {user?.name && (
            <div className="bg-white bg-opacity-80 backdrop-blur-sm p-5 rounded-xl border border-gray-100 shadow-sm hover-shadow-md transition-shadow">
              <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">Full Name</label>
              <p className="text-sm text-gray-900 font-medium">{user.name}</p>
            </div>
          )}
        </div>
        
        {/* Account Stats */}
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-5 rounded-xl border border-gray-200">
          <h5 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wider">Account Information</h5>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">1</div>
              <div className="text-xs text-gray-500 uppercase tracking-wider">Active Session</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">✓</div>
              <div className="text-xs text-gray-500 uppercase tracking-wider">Verified</div>
            </div>
          </div>
        </div>
        
        {/* Logout Section */}
        <div className="pt-6 border-t border-gray-200">
          <Button
            variant="danger"
            size="sm"
            onClick={handleLogout}
            className="w-full hover-lift bg-gradient-to-r from-red-500 to-red-600 hover-from-red-600 hover-to-red-700 text-white font-semibold py-3 rounded-xl shadow-lg hover-shadow-xl transition-all duration-200 transform hover-scale"
          >
            <span className="mr-2">🚪</span>
            Logout
          </Button>
        </div>
      </div>
    </div>
  );
};

export default UserProfile; 