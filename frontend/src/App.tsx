import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/auth/Login';
import Signup from './components/auth/Signup';
import Dashboard from './components/Dashboard';
import LandingPage from './components/LandingPage';
import ProfileSetupWrapper from './components/profile/ProfileSetupWrapper';
import LoadingSpinner from './components/common/LoadingSpinner';
import './App.css';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return user ? <>{children}</> : <Navigate to="/signup" />;
};

const AppContent: React.FC = () => {
  const { user, loading, isNewUser } = useAuth();
  const [showSignup, setShowSignup] = React.useState(true);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/signup"
          element={
            user ? (
              isNewUser ? (
                <Navigate to="/profile-setup" />
              ) : (
                <Navigate to="/" />
              )
            ) : (
              showSignup ? (
                <Signup onSwitchToLogin={() => setShowSignup(false)} />
              ) : (
                <Login onSwitchToSignup={() => setShowSignup(true)} />
              )
            )
          }
        />
        <Route
          path="/login"
          element={
            user ? (
              isNewUser ? (
                <Navigate to="/profile-setup" />
              ) : (
                <Navigate to="/" />
              )
            ) : (
              showSignup ? (
                <Signup onSwitchToLogin={() => setShowSignup(false)} />
              ) : (
                <Login onSwitchToSignup={() => setShowSignup(true)} />
              )
            )
          }
        />
        <Route
          path="/profile-setup"
          element={
            <PrivateRoute>
              <ProfileSetupWrapper />
            </PrivateRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          }
        />
        <Route
          path="/"
          element={
            user ? (
              isNewUser ? (
                <Navigate to="/profile-setup" />
              ) : (
                <LandingPage />
              )
            ) : (
              <Navigate to="/signup" />
            )
          }
        />
      </Routes>
    </Router>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;

