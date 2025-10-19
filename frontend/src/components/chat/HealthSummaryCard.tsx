import React from 'react';
import { HealthSummary } from '../../types/structuredResponses';
import './StructuredResponseCards.css';

interface HealthSummaryCardProps {
  data: HealthSummary;
}

const HealthSummaryCard: React.FC<HealthSummaryCardProps> = ({ data }) => {
  const calorieProgress = (data.total_calories / data.target_calories) * 100;
  const remainingProgress = Math.max(0, (data.remaining_calories / data.target_calories) * 100);

  return (
    <div className="structured-card health-summary-card">
      <div className="card-header">
        <h3>📊 Nutrition Summary</h3>
        <span className="date-badge">{data.date}</span>
      </div>

      <div className="card-content">
        {/* Calorie Overview */}
        <div className="calorie-section">
          <div className="calorie-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${Math.min(calorieProgress, 100)}%` }}
              ></div>
            </div>
            <div className="calorie-numbers">
              <span className="consumed">{data.total_calories}</span>
              <span className="separator">/</span>
              <span className="target">{data.target_calories} calories</span>
            </div>
          </div>
          
          <div className="remaining-calories">
            <span className={`remaining-badge ${data.remaining_calories < 0 ? 'over-budget' : 'under-budget'}`}>
              {data.remaining_calories >= 0 ? `${data.remaining_calories} remaining` : `${Math.abs(data.remaining_calories)} over`}
            </span>
          </div>
        </div>

        {/* Macronutrients */}
        <div className="macros-section">
          <h4>Macronutrients</h4>
          <div className="macro-grid">
            <div className="macro-item protein">
              <span className="macro-label">Protein</span>
              <span className="macro-value">{data.protein}g</span>
            </div>
            <div className="macro-item carbs">
              <span className="macro-label">Carbs</span>
              <span className="macro-value">{data.carbs}g</span>
            </div>
            <div className="macro-item fat">
              <span className="macro-label">Fat</span>
              <span className="macro-value">{data.fat}g</span>
            </div>
          </div>
        </div>

        {/* Meals */}
        {data.meals && data.meals.length > 0 && (
          <div className="meals-section">
            <h4>Today's Meals</h4>
            <ul className="meals-list">
              {data.meals.map((meal, index) => (
                <li key={index} className="meal-item">
                  {meal}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {data.recommendations && data.recommendations.length > 0 && (
          <div className="recommendations-section">
            <h4>Recommendations</h4>
            <ul className="recommendations-list">
              {data.recommendations.map((rec, index) => (
                <li key={index} className="recommendation-item">
                  💡 {rec}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Health Score */}
        <div className="health-score-section">
          <div className="score-container">
            <span className="score-label">Health Score</span>
            <div className="score-display">
              <span className={`score-value ${data.health_score >= 8 ? 'excellent' : data.health_score >= 6 ? 'good' : 'needs-improvement'}`}>
                {data.health_score}
              </span>
              <span className="score-max">/10</span>
            </div>
          </div>
          <div className="score-bar">
            <div 
              className="score-fill" 
              style={{ width: `${(data.health_score / 10) * 100}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HealthSummaryCard;