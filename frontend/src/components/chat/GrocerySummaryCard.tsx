import React from 'react';
import { GrocerySummary } from '../../types/structuredResponses';
import './StructuredResponseCards.css';

interface GrocerySummaryCardProps {
  data: GrocerySummary;
}

const GrocerySummaryCard: React.FC<GrocerySummaryCardProps> = ({ data }) => {
  const getBudgetStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'within_budget': return 'success';
      case 'near_limit': return 'warning';
      case 'over_budget': return 'danger';
      default: return 'neutral';
    }
  };

  const getAvailabilityIcon = (availability: string) => {
    switch (availability.toLowerCase()) {
      case 'in stock': return '✅';
      case 'limited': return '⚠️';
      case 'out of stock': return '❌';
      default: return '❓';
    }
  };

  return (
    <div className="structured-card grocery-summary-card">
      <div className="card-header">
        <h3>🛒 Shopping Cart Summary</h3>
        <span className="item-count-badge">{data.item_count} items</span>
      </div>

      <div className="card-content">
        {/* Cart Items */}
        <div className="cart-items-section">
          <h4>Cart Items</h4>
          <div className="cart-items-list">
            {data.cart_items.map((item, index) => (
              <div key={index} className="cart-item">
                <div className="item-info">
                  <span className="item-name">{item.name}</span>
                  <span className="item-availability">
                    {getAvailabilityIcon(item.availability)} {item.availability}
                  </span>
                </div>
                <div className="item-pricing">
                  <span className="quantity">Qty: {item.quantity}</span>
                  <span className="unit-price">${item.price.toFixed(2)} each</span>
                  <span className="total-price">${item.total_price.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Total Cost */}
        <div className="total-section">
          <div className="total-cost">
            <span className="total-label">Total Cost</span>
            <span className="total-amount">${data.total_cost.toFixed(2)}</span>
          </div>
        </div>

        {/* Budget Information */}
        {data.budget_set && (
          <div className="budget-section">
            <h4>Budget Analysis</h4>
            <div className="budget-info">
              <div className="budget-row">
                <span>Budget Set:</span>
                <span>${data.budget_set.toFixed(2)}</span>
              </div>
              <div className="budget-row">
                <span>Remaining:</span>
                <span className={`budget-remaining ${getBudgetStatusColor(data.budget_status)}`}>
                  ${data.budget_remaining?.toFixed(2) || '0.00'}
                </span>
              </div>
              <div className="budget-status">
                <span className={`status-badge ${getBudgetStatusColor(data.budget_status)}`}>
                  {data.budget_status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>
            
            {data.budget_set > 0 && (
              <div className="budget-progress">
                <div className="progress-bar">
                  <div 
                    className={`progress-fill ${getBudgetStatusColor(data.budget_status)}`}
                    style={{ width: `${Math.min((data.total_cost / data.budget_set) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Savings Opportunities */}
        {data.savings_opportunities && data.savings_opportunities.length > 0 && (
          <div className="savings-section">
            <h4>💰 Savings Opportunities</h4>
            <ul className="savings-list">
              {data.savings_opportunities.map((saving, index) => (
                <li key={index} className="saving-item">
                  {saving}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {data.recommendations && data.recommendations.length > 0 && (
          <div className="recommendations-section">
            <h4>💡 Recommendations</h4>
            <ul className="recommendations-list">
              {data.recommendations.map((rec, index) => (
                <li key={index} className="recommendation-item">
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Substitutions */}
        {data.substitutions && data.substitutions.length > 0 && (
          <div className="substitutions-section">
            <h4>🔄 Available Substitutions</h4>
            <ul className="substitutions-list">
              {data.substitutions.map((sub, index) => (
                <li key={index} className="substitution-item">
                  {sub}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Availability Summary */}
        <div className="availability-section">
          <h4>📦 Availability Summary</h4>
          <p className="availability-text">{data.availability_summary}</p>
        </div>
      </div>
    </div>
  );
};

export default GrocerySummaryCard;