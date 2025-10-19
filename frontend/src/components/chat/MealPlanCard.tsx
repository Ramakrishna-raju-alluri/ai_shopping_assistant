import React, { useState } from 'react';
import { MealPlan } from '../../types/structuredResponses';
import './StructuredResponseCards.css';

interface MealPlanCardProps {
  data: MealPlan;
}

const MealPlanCard: React.FC<MealPlanCardProps> = ({ data }) => {
  const [expandedRecipe, setExpandedRecipe] = useState<number | null>(null);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy': return 'success';
      case 'medium': return 'warning';
      case 'hard': return 'danger';
      default: return 'neutral';
    }
  };

  const getMealTypeIcon = (mealType: string) => {
    switch (mealType.toLowerCase()) {
      case 'breakfast': return '🌅';
      case 'lunch': return '🌞';
      case 'dinner': return '🌙';
      case 'snack': return '🍎';
      default: return '🍽️';
    }
  };

  const toggleRecipe = (index: number) => {
    setExpandedRecipe(expandedRecipe === index ? null : index);
  };

  return (
    <div className="structured-card meal-plan-card">
      <div className="card-header">
        <h3>🍽️ Meal Plan</h3>
        <span className="date-badge">{data.date}</span>
      </div>

      <div className="card-content">
        {/* Overview */}
        <div className="meal-overview">
          <div className="overview-grid">
            <div className="overview-item">
              <span className="overview-label">Total Calories</span>
              <span className="overview-value">{data.total_calories}</span>
            </div>
            <div className="overview-item">
              <span className="overview-label">Prep Time</span>
              <span className="overview-value">{data.total_prep_time} min</span>
            </div>
            <div className="overview-item">
              <span className="overview-label">Cook Time</span>
              <span className="overview-value">{data.total_cook_time} min</span>
            </div>
            {data.estimated_cost && (
              <div className="overview-item">
                <span className="overview-label">Est. Cost</span>
                <span className="overview-value">${data.estimated_cost.toFixed(2)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Meal Balance Score */}
        <div className="balance-score-section">
          <div className="score-container">
            <span className="score-label">Meal Balance Score</span>
            <div className="score-display">
              <span className={`score-value ${data.meal_balance_score >= 8 ? 'excellent' : data.meal_balance_score >= 6 ? 'good' : 'needs-improvement'}`}>
                {data.meal_balance_score}
              </span>
              <span className="score-max">/10</span>
            </div>
          </div>
          <div className="score-bar">
            <div 
              className="score-fill" 
              style={{ width: `${(data.meal_balance_score / 10) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Recipes */}
        <div className="recipes-section">
          <h4>Recipes ({data.recipes.length})</h4>
          <div className="recipes-list">
            {data.recipes.map((recipe, index) => (
              <div key={index} className="recipe-card">
                <div className="recipe-header" onClick={() => toggleRecipe(index)}>
                  <div className="recipe-title">
                    <span className="meal-icon">{getMealTypeIcon(recipe.meal_type)}</span>
                    <span className="recipe-name">{recipe.name}</span>
                    <span className="meal-type-badge">{recipe.meal_type}</span>
                  </div>
                  <div className="recipe-meta">
                    <span className="servings">Serves {recipe.servings}</span>
                    <span className="calories">{recipe.calories_per_serving} cal/serving</span>
                    <span className={`difficulty ${getDifficultyColor(recipe.difficulty_level)}`}>
                      {recipe.difficulty_level}
                    </span>
                    <span className="expand-icon">
                      {expandedRecipe === index ? '▼' : '▶'}
                    </span>
                  </div>
                </div>

                {expandedRecipe === index && (
                  <div className="recipe-details">
                    <div className="recipe-times">
                      <span>⏱️ Prep: {recipe.prep_time} min</span>
                      <span>🔥 Cook: {recipe.cook_time} min</span>
                    </div>

                    {recipe.dietary_tags && recipe.dietary_tags.length > 0 && (
                      <div className="dietary-tags">
                        {recipe.dietary_tags.map((tag, tagIndex) => (
                          <span key={tagIndex} className="dietary-tag">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="ingredients-section">
                      <h5>Ingredients:</h5>
                      <ul className="ingredients-list">
                        {recipe.ingredients.map((ingredient, ingIndex) => (
                          <li key={ingIndex}>{ingredient}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="instructions-section">
                      <h5>Instructions:</h5>
                      <ol className="instructions-list">
                        {recipe.instructions.map((instruction, instIndex) => (
                          <li key={instIndex}>{instruction}</li>
                        ))}
                      </ol>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Shopping List */}
        {data.shopping_list && data.shopping_list.length > 0 && (
          <div className="shopping-list-section">
            <h4>🛒 Shopping List</h4>
            <div className="shopping-grid">
              {data.shopping_list.map((item, index) => (
                <div key={index} className="shopping-item">
                  {item}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Nutritional Summary */}
        {data.nutritional_summary && Object.keys(data.nutritional_summary).length > 0 && (
          <div className="nutrition-section">
            <h4>📊 Nutritional Summary</h4>
            <div className="nutrition-grid">
              {Object.entries(data.nutritional_summary).map(([nutrient, value]) => (
                <div key={nutrient} className="nutrition-item">
                  <span className="nutrient-name">{nutrient}</span>
                  <span className="nutrient-value">{value}g</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Dietary Notes */}
        {data.dietary_notes && data.dietary_notes.length > 0 && (
          <div className="dietary-notes-section">
            <h4>📝 Dietary Notes</h4>
            <ul className="dietary-notes-list">
              {data.dietary_notes.map((note, index) => (
                <li key={index} className="dietary-note">
                  {note}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Ingredient Substitutions */}
        {data.ingredient_substitutions && data.ingredient_substitutions.length > 0 && (
          <div className="substitutions-section">
            <h4>🔄 Ingredient Substitutions</h4>
            <ul className="substitutions-list">
              {data.ingredient_substitutions.map((sub, index) => (
                <li key={index} className="substitution-item">
                  {sub}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default MealPlanCard;