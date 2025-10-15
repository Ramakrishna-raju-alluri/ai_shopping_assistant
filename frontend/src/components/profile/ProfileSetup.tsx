import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './ProfileSetup.css';

interface ProfileSetupOptions {
  dietary_options: string[];
  cuisine_options: string[];
  cooking_skill_options: string[];
  cooking_time_options: string[];
  shopping_frequency_options: string[];
}

interface ProfileStatus {
  is_setup_complete: boolean;
  missing_sections: string[];
  profile_data: any;
}

interface DietaryPreferences {
  diet: string;
  allergies: string[];
  restrictions: string[];
}

interface CuisinePreferences {
  preferred_cuisines: string[];
  disliked_cuisines: string[];
}

interface CookingPreferences {
  skill_level: string;
  cooking_time_preference: string;
  kitchen_equipment: string[];
}

interface BudgetPreferences {
  budget_limit: number;
  meal_budget?: number;
  shopping_frequency: string;
}

interface CompleteProfileSetup {
  dietary: DietaryPreferences;
  cuisine: CuisinePreferences;
  cooking: CookingPreferences;
  budget: BudgetPreferences;
  meal_goal?: string;
}

const API_BASE_URL = 'http://localhost:8100/api/v1';

const ProfileSetup: React.FC = () => {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isUpdateMode = searchParams.get('mode') === 'update';
  const [currentStep, setCurrentStep] = useState(1);
  const [options, setOptions] = useState<ProfileSetupOptions | null>(null);
  const [profileStatus, setProfileStatus] = useState<ProfileStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Form data
  const [dietary, setDietary] = useState<DietaryPreferences>({
    diet: '',
    allergies: [],
    restrictions: []
  });
  
  const [cuisine, setCuisine] = useState<CuisinePreferences>({
    preferred_cuisines: [],
    disliked_cuisines: []
  });
  
  const [cooking, setCooking] = useState<CookingPreferences>({
    skill_level: '',
    cooking_time_preference: '',
    kitchen_equipment: []
  });
  
  const [budget, setBudget] = useState<BudgetPreferences>({
    budget_limit: 100,
    meal_budget: 15,
    shopping_frequency: 'weekly'
  });
  
  const [mealGoal, setMealGoal] = useState<string>('');

  useEffect(() => {
    if (user) {
      loadProfileData();
    }
  }, [user]);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      // Load options
      const optionsResponse = await axios.get(`${API_BASE_URL}/profile-setup/options`);
      setOptions(optionsResponse.data);
      
      // Load profile status
      const statusResponse = await axios.get(`${API_BASE_URL}/profile-setup/status`, { headers });
      setProfileStatus(statusResponse.data);
      
      // If this is update mode, always start from step 1 (fresh setup)
      if (isUpdateMode) {
        console.log('🔄 Update mode: Starting fresh profile setup for existing user');
        setCurrentStep(1);
        // Reset all form data for fresh start
        resetFormData();
      } else {
        // For new users, if profile is already complete, show completion step
        if (statusResponse.data.is_setup_complete) {
          setCurrentStep(6); // Show completion step
        }
      }
      
    } catch (err) {
      setError('Failed to load profile data');
      console.error('Error loading profile data:', err);
    } finally {
      setLoading(false);
    }
  };

  const resetFormData = () => {
    console.log('🔄 Resetting form data for fresh setup');
    setDietary({
      diet: '',
      allergies: [],
      restrictions: []
    });
    setCuisine({
      preferred_cuisines: [],
      disliked_cuisines: []
    });
    setCooking({
      skill_level: '',
      cooking_time_preference: '',
      kitchen_equipment: []
    });
    setBudget({
      budget_limit: 100,
      meal_budget: 15,
      shopping_frequency: 'weekly'
    });
    setMealGoal('');
  };

  const handleDietaryChange = (field: keyof DietaryPreferences, value: any) => {
    setDietary(prev => ({ ...prev, [field]: value }));
  };

  const handleCuisineChange = (field: keyof CuisinePreferences, value: any) => {
    setCuisine(prev => ({ ...prev, [field]: value }));
  };

  const handleCookingChange = (field: keyof CookingPreferences, value: any) => {
    setCooking(prev => ({ ...prev, [field]: value }));
  };

  const handleBudgetChange = (field: keyof BudgetPreferences, value: any) => {
    setBudget(prev => ({ ...prev, [field]: value }));
  };

  const handleNext = () => {
    if (currentStep < 5) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleCompleteSetup = async () => {
    try {
      setLoading(true);
      
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const completeProfile: CompleteProfileSetup = {
        dietary,
        cuisine,
        cooking,
        budget,
        meal_goal: mealGoal
      };
      
      await axios.post(`${API_BASE_URL}/profile-setup/complete`, completeProfile, { headers });
      
      // Move to completion step
      setCurrentStep(6);
      
    } catch (err) {
      setError('Failed to complete profile setup');
      console.error('Error completing profile setup:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="step-container">
      <h3>🥗 Dietary Preferences</h3>
      <p>Tell us about your dietary needs and restrictions</p>
      
      <div className="form-group">
        <label>Dietary Preference:</label>
        <select 
          value={dietary.diet} 
          onChange={(e) => handleDietaryChange('diet', e.target.value)}
          className="form-control"
        >
          <option value="">Select your diet</option>
          {options?.dietary_options.map(option => (
            <option key={option} value={option}>
              {option.charAt(0).toUpperCase() + option.slice(1).replace('-', ' ')}
            </option>
          ))}
        </select>
      </div>
      
      <div className="form-group">
        <label>Food Allergies (comma-separated):</label>
        <input
          type="text"
          value={dietary.allergies.join(', ')}
          onChange={(e) => handleDietaryChange('allergies', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
          placeholder="e.g., nuts, shellfish, dairy"
          className="form-control"
        />
      </div>
      
      <div className="form-group">
        <label>Other Restrictions (comma-separated):</label>
        <input
          type="text"
          value={dietary.restrictions.join(', ')}
          onChange={(e) => handleDietaryChange('restrictions', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
          placeholder="e.g., low-sodium, no processed foods"
          className="form-control"
        />
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="step-container">
      <h3>🍽️ Cuisine Preferences</h3>
      <p>What types of cuisine do you enjoy?</p>
      
      <div className="form-group">
        <label>Preferred Cuisines:</label>
        <div className="checkbox-group">
          {options?.cuisine_options.map(option => (
            <label key={option} className="checkbox-label">
              <input
                type="checkbox"
                checked={cuisine.preferred_cuisines.includes(option)}
                onChange={(e) => {
                  if (e.target.checked) {
                    handleCuisineChange('preferred_cuisines', [...cuisine.preferred_cuisines, option]);
                  } else {
                    handleCuisineChange('preferred_cuisines', cuisine.preferred_cuisines.filter(c => c !== option));
                  }
                }}
              />
              {option.charAt(0).toUpperCase() + option.slice(1).replace('_', ' ')}
            </label>
          ))}
        </div>
      </div>
      
      <div className="form-group">
        <label>Disliked Cuisines (optional):</label>
        <div className="checkbox-group">
          {options?.cuisine_options.map(option => (
            <label key={option} className="checkbox-label">
              <input
                type="checkbox"
                checked={cuisine.disliked_cuisines.includes(option)}
                onChange={(e) => {
                  if (e.target.checked) {
                    handleCuisineChange('disliked_cuisines', [...cuisine.disliked_cuisines, option]);
                  } else {
                    handleCuisineChange('disliked_cuisines', cuisine.disliked_cuisines.filter(c => c !== option));
                  }
                }}
              />
              {option.charAt(0).toUpperCase() + option.slice(1).replace('_', ' ')}
            </label>
          ))}
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="step-container">
      <h3>👨‍🍳 Cooking Preferences</h3>
      <p>Tell us about your cooking experience and preferences</p>
      
      <div className="form-group">
        <label>Cooking Skill Level:</label>
        <select 
          value={cooking.skill_level} 
          onChange={(e) => handleCookingChange('skill_level', e.target.value)}
          className="form-control"
        >
          <option value="">Select your skill level</option>
          {options?.cooking_skill_options.map(option => (
            <option key={option} value={option}>
              {option.charAt(0).toUpperCase() + option.slice(1)}
            </option>
          ))}
        </select>
      </div>
      
      <div className="form-group">
        <label>Cooking Time Preference:</label>
        <select 
          value={cooking.cooking_time_preference} 
          onChange={(e) => handleCookingChange('cooking_time_preference', e.target.value)}
          className="form-control"
        >
          <option value="">Select your preference</option>
          {options?.cooking_time_options.map(option => (
            <option key={option} value={option}>
              {option.charAt(0).toUpperCase() + option.slice(1)}
            </option>
          ))}
        </select>
      </div>
      
      <div className="form-group">
        <label>Available Kitchen Equipment (comma-separated):</label>
        <input
          type="text"
          value={cooking.kitchen_equipment.join(', ')}
          onChange={(e) => handleCookingChange('kitchen_equipment', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
          placeholder="e.g., stove, oven, blender, microwave"
          className="form-control"
        />
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="step-container">
      <h3>💰 Budget Preferences</h3>
      <p>Set your budget limits and shopping frequency</p>
      
      <div className="form-group">
        <label>Monthly Budget Limit ($):</label>
        <input
          type="number"
          value={budget.budget_limit}
          onChange={(e) => handleBudgetChange('budget_limit', parseFloat(e.target.value))}
          min="10"
          max="1000"
          step="5"
          className="form-control"
        />
      </div>
      
      <div className="form-group">
        <label>Per-Meal Budget ($):</label>
        <input
          type="number"
          value={budget.meal_budget || ''}
          onChange={(e) => handleBudgetChange('meal_budget', parseFloat(e.target.value))}
          min="5"
          max="50"
          step="1"
          className="form-control"
        />
      </div>
      
      <div className="form-group">
        <label>Shopping Frequency:</label>
        <select 
          value={budget.shopping_frequency} 
          onChange={(e) => handleBudgetChange('shopping_frequency', e.target.value)}
          className="form-control"
        >
          {options?.shopping_frequency_options.map(option => (
            <option key={option} value={option}>
              {option.charAt(0).toUpperCase() + option.slice(1).replace('-', ' ')}
            </option>
          ))}
        </select>
      </div>
    </div>
  );

  const renderStep5 = () => (
    <div className="step-container">
      <h3>🎯 Meal Planning Goal</h3>
      <p>What's your primary goal for meal planning?</p>
      
      <div className="form-group">
        <label>Meal Planning Goal:</label>
        <select 
          value={mealGoal} 
          onChange={(e) => setMealGoal(e.target.value)}
          className="form-control"
        >
          <option value="">Select your goal</option>
          <option value="healthy_balanced_meals">Healthy & Balanced Meals</option>
          <option value="budget_friendly">Budget-Friendly Meals</option>
          <option value="quick_easy_meals">Quick & Easy Meals</option>
          <option value="family_friendly">Family-Friendly Meals</option>
          <option value="weight_loss">Weight Loss</option>
          <option value="muscle_gain">Muscle Gain</option>
          <option value="special_diet">Special Diet Requirements</option>
        </select>
      </div>
      
      <div className="summary">
        <h4>📋 Profile Summary</h4>
        <div className="summary-grid">
          <div><strong>Diet:</strong> {dietary.diet || 'Not set'}</div>
          <div><strong>Allergies:</strong> {dietary.allergies.length > 0 ? dietary.allergies.join(', ') : 'None'}</div>
          <div><strong>Preferred Cuisines:</strong> {cuisine.preferred_cuisines.length > 0 ? cuisine.preferred_cuisines.join(', ') : 'Not set'}</div>
          <div><strong>Cooking Skill:</strong> {cooking.skill_level || 'Not set'}</div>
          <div><strong>Budget:</strong> ${budget.budget_limit}</div>
          <div><strong>Shopping Frequency:</strong> {budget.shopping_frequency}</div>
          <div><strong>Meal Goal:</strong> {mealGoal || 'Not set'}</div>
        </div>
      </div>
    </div>
  );

  const renderStep6 = () => (
    <div className="step-container">
      {isUpdateMode ? (
        <>
          <h3>✅ Profile Updated Successfully!</h3>
          <p>Your profile has been updated with your new preferences. All changes have been saved to your account.</p>
          
          <div className="completion-message">
            <div className="checkmark">Update Complete</div>
            <h4>Profile Update Complete!</h4>
            <ul>
              <li>Your dietary preferences have been updated</li>
              <li>Cuisine preferences refreshed</li>
              <li>Cooking preferences saved</li>
              <li>Budget settings updated</li>
              <li>All changes saved to DynamoDB</li>
            </ul>
          </div>
          
          <button 
            onClick={() => navigate('/dashboard')} 
            className="btn btn-primary"
          >
            Return to Dashboard
          </button>
        </>
      ) : (
        <>
          <h3>Profile Setup Complete!</h3>
          <p>Your profile has been set up successfully. You can now enjoy personalized meal planning and product recommendations.</p>
          
          <div className="completion-message">
            <div className="checkmark">Complete</div>
            <h4>What's Next?</h4>
            <ul>
              <li>Start planning meals with your preferences</li>
              <li>Get personalized product recommendations</li>
              <li>Update your preferences anytime</li>
              <li>Track your shopping history</li>
            </ul>
          </div>
          
          <button 
            onClick={() => navigate('/dashboard')} 
            className="btn btn-primary"
          >
            Go to Dashboard
          </button>
        </>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="profile-setup-container">
        <div className="loading">Loading profile setup...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-setup-container">
        <div className="error">Error: {error}</div>
        <button onClick={loadProfileData} className="btn btn-secondary">Retry</button>
      </div>
    );
  }

  // Only show completion step for non-update mode when setup is complete
  if (profileStatus?.is_setup_complete && !isUpdateMode) {
    return renderStep6();
  }

  return (
    <div className="profile-setup-container">
      <div className="back-to-dashboard">
        <button 
          onClick={() => navigate('/dashboard')} 
          className="btn btn-danger"
        >
          ← Back to Dashboard
        </button>
      </div>
      
      <div className="setup-header">
        {isUpdateMode ? (
          <>
            <h2>Update Profile</h2>
            <p>Let's update your preferences from the beginning</p>
            <div className="update-notice">
              <span className="update-badge">Update Mode</span>
              <span>All changes will be saved to your profile</span>
            </div>
          </>
        ) : (
          <>
            <h2>Profile Setup</h2>
            <p>Let's personalize your experience</p>
          </>
        )}
        
        <div className="progress-bar">
          {[1, 2, 3, 4, 5].map(step => (
            <div 
              key={step} 
              className={`progress-step ${step <= currentStep ? 'active' : ''}`}
            >
              {step}
            </div>
          ))}
        </div>
      </div>
      
      <div className="setup-content">
        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
        {currentStep === 3 && renderStep3()}
        {currentStep === 4 && renderStep4()}
        {currentStep === 5 && renderStep5()}
        {currentStep === 6 && renderStep6()}
      </div>
      
      <div className="setup-actions">
        {currentStep > 1 && currentStep < 6 && (
          <button onClick={handleBack} className="btn btn-secondary">
            Back
          </button>
        )}
        
        {currentStep < 5 && (
          <button onClick={handleNext} className="btn btn-primary">
            Next
          </button>
        )}
        
        {currentStep === 5 && (
          <button 
            onClick={handleCompleteSetup} 
            className="btn btn-success"
            disabled={loading}
          >
            {loading ? 'Setting up...' : 'Complete Setup'}
          </button>
        )}
      </div>
    </div>
  );
};

export default ProfileSetup; 