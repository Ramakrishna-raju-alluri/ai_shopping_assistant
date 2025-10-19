import React from 'react';
import { isJsonResponse, getResponseType, StructuredResponse } from '../../types/structuredResponses';
import HealthSummaryCard from './HealthSummaryCard';
import GrocerySummaryCard from './GrocerySummaryCard';
import MealPlanCard from './MealPlanCard';

interface StructuredResponseRendererProps {
  content: string;
}

const StructuredResponseRenderer: React.FC<StructuredResponseRendererProps> = ({ content }) => {
  // Check if the content is JSON
  if (!isJsonResponse(content)) {
    // Return plain text for non-JSON responses
    return (
      <div className="text-response">
        {content}
      </div>
    );
  }

  try {
    const data: StructuredResponse = JSON.parse(content);
    const responseType = getResponseType(data);

    switch (responseType) {
      case 'health':
        return <HealthSummaryCard data={data as any} />;
      case 'grocery':
        return <GrocerySummaryCard data={data as any} />;
      case 'meal':
        return <MealPlanCard data={data as any} />;
      default:
        // Fallback for unknown structured data - display as formatted JSON
        return (
          <div className="structured-card unknown-response-card">
            <div className="card-header">
              <h3>📊 Structured Response</h3>
            </div>
            <div className="card-content">
              <pre className="json-display">
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>
          </div>
        );
    }
  } catch (error) {
    console.error('Error parsing structured response:', error);
    // Fallback to plain text if JSON parsing fails
    return (
      <div className="text-response">
        {content}
      </div>
    );
  }
};

export default StructuredResponseRenderer;