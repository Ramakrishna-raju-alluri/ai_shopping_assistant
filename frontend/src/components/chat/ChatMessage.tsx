import React from 'react';
import Button from '../common/Button';
import StructuredResponseRenderer from './StructuredResponseRenderer';

interface ChatMessageType {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sessionId?: string;
  step?: string;
  requiresConfirmation?: boolean;
  confirmationPrompt?: string;
  requiresInput?: boolean;
  input_prompt?: string;
  input_type?: string;
  input_options?: string[];
  data?: any;
}

interface ChatMessageProps {
  message: ChatMessageType;
  onConfirm: (confirmed: boolean) => void;
  onInputSubmit?: (input: string | number | boolean) => void;
  onCartAction?: (action: string) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, onConfirm, onInputSubmit, onCartAction }) => {
  // Ensure message type is properly handled as string
  const messageType = String(message.type || 'user').toLowerCase();
  const isUser = messageType === 'user';
  const isAssistant = messageType === 'assistant';
  
  // Debug logging
  console.log(`🎨 ChatMessage rendering - Type: "${messageType}", IsUser: ${isUser}, IsAssistant: ${isAssistant}`);
  console.log(`🎨 ChatMessage content: "${message.content.substring(0, 50)}..."`);
  
  const [inputValue, setInputValue] = React.useState<string>('');
  const [ratingValue, setRatingValue] = React.useState<number>(0);

  const handleInputSubmit = () => {
    if (onInputSubmit) {
      if (message.input_type === 'rating') {
        onInputSubmit(ratingValue);
      } else {
        onInputSubmit(inputValue);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleInputSubmit();
    }
  };

  const formatData = (data: any) => {
    if (!data) return null;

    if (data.recipe_summary) {
      return (
        <div className="data-card recipe">
          <h4 className="font-semibold text-green-700 mb-3 flex items-center">
            <span className="mr-2">🍽️</span>
            Recipes Found
          </h4>
          <div className="text-sm text-green-700 leading-relaxed" style={{ whiteSpace: 'pre-line' }}>
            {data.recipe_summary}
          </div>
        </div>
      );
    }

    if (data.product_summary) {
      return (
        <div className="data-card product">
          <h4 className="font-semibold text-blue-700 mb-3 flex items-center">
            <span className="mr-2">🛒</span>
            Products Found
          </h4>
          <div className="text-sm text-blue-700 leading-relaxed" style={{ whiteSpace: 'pre-line' }}>
            {data.product_summary}
          </div>
        </div>
      );
    }

    if (data.cart_summary) {
      return (
        <div className="data-card cart">
          <h4 className="font-semibold text-purple-700 mb-3 flex items-center">
            <span className="mr-2">🛍️</span>
            Shopping Cart
          </h4>
          <div className="text-sm text-purple-700 space-y-2 leading-relaxed">
            {data.cart_summary.split('\n').map((line: string, index: number) => (
              <div key={index} className="flex justify-between items-center p-2 bg-white bg-opacity-50 rounded-lg">
                <span>{line}</span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    if (data.final_summary) {
      return (
        <div className="data-card final">
          <h4 className="font-semibold text-orange-700 mb-3 flex items-center">
            <span className="mr-2">🎉</span>
            Final Cart with Promotions
          </h4>
          <div className="text-sm text-orange-700 leading-relaxed" style={{ whiteSpace: 'pre-line' }}>
            {data.final_summary}
          </div>
        </div>
      );
    }

    if (data.purchase_intent && data.purchase_summary) {
      return (
        <div className="data-card purchase-intent">
          <h4 className="font-semibold text-green-700 mb-3 flex items-center">
            <span className="mr-2">🛒</span>
            Purchase Intent
          </h4>
          <div className="text-sm text-green-700 leading-relaxed" style={{ whiteSpace: 'pre-line' }}>
            {data.purchase_summary}
          </div>
        </div>
      );
    }

    if (data.purchase_confirmation && data.purchase_summary) {
      return (
        <div className="data-card purchase-confirmation">
          <h4 className="font-semibold text-blue-700 mb-3 flex items-center">
            <span className="mr-2">✅</span>
            Purchase Confirmation
          </h4>
          <div className="text-sm text-blue-700 leading-relaxed" style={{ whiteSpace: 'pre-line' }}>
            {data.purchase_summary}
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className={`chat-message ${isUser ? 'user-message' : 'ai-message'}`}>
      <div className={`chat-bubble ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? (
          <div className="text-sm leading-relaxed">{message.content}</div>
        ) : (
          <StructuredResponseRenderer content={message.content} />
        )}
        
        {!isUser && formatData(message.data)}
        
        {!isUser && message.requiresConfirmation && (
          <div className="mt-4 space-y-3">
            <p className="text-sm font-semibold text-gray-800 bg-white bg-opacity-80 p-3 rounded-lg border border-gray-200">
              {message.confirmationPrompt || 'Should I proceed?'}
            </p>
            
            {/* Cart Action Buttons */}
            {message.data?.add_to_cart_enabled && message.data?.cart_options && (
              <div className="space-y-2">
                <div className="grid grid-cols-1 gap-2">
                  {message.data.cart_options.map((option: string, index: number) => (
                    <Button
                      key={index}
                      size="sm"
                      variant={option.includes('Add All') ? "success" : option.includes('View') ? "primary" : "secondary"}
                      onClick={() => onCartAction && onCartAction(option)}
                      className="text-xs hover-lift w-full justify-start"
                    >
                      {option.includes('Add All') && '🛒 '}
                      {option.includes('View') && '🛍️ '}
                      {option.includes('Continue') && '📝 '}
                      {option}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Regular Yes/No buttons for other confirmations */}
            {!message.data?.add_to_cart_enabled && (
              <div className="flex space-x-3">
                <Button
                  size="sm"
                  variant="success"
                  onClick={() => onConfirm(true)}
                  className="text-xs hover-lift"
                >
                  ✅ Yes
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => onConfirm(false)}
                  className="text-xs hover-lift"
                >
                  ❌ No
                </Button>
              </div>
            )}
          </div>
        )}

        {!isUser && message.requiresInput && (
          <div className="mt-4 space-y-3">
            <p className="text-sm font-semibold text-gray-800 bg-white bg-opacity-80 p-3 rounded-lg border border-gray-200">
              {message.input_prompt || 'Please provide your input:'}
            </p>
            
            {message.input_type === 'rating' && (
              <div className="space-y-2">
                <div className="flex space-x-2">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <Button
                      key={rating}
                      size="sm"
                      variant={ratingValue >= rating ? "success" : "secondary"}
                      onClick={() => setRatingValue(rating)}
                      className="text-xs hover-lift"
                    >
                      {rating}
                    </Button>
                  ))}
                </div>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={handleInputSubmit}
                  disabled={ratingValue === 0}
                  className="text-xs hover-lift"
                >
                  Submit Rating
                </Button>
              </div>
            )}

            {message.input_type === 'text' && (
              <div className="space-y-2">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Enter your response..."
                  className="w-full p-3 border border-gray-300 rounded-lg text-sm resize-none"
                  rows={3}
                />
                <Button
                  size="sm"
                  variant="primary"
                  onClick={handleInputSubmit}
                  disabled={!inputValue.trim()}
                  className="text-xs hover-lift"
                >
                  Submit
                </Button>
              </div>
            )}

            {message.input_type === 'options' && message.input_options && (
              <div className="space-y-2">
                <div className="space-y-2">
                  {message.input_options.map((option, index) => (
                    <Button
                      key={index}
                      size="sm"
                      variant="secondary"
                      onClick={() => setInputValue(option)}
                      className="text-xs hover-lift w-full justify-start"
                    >
                      {option}
                    </Button>
                  ))}
                </div>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={handleInputSubmit}
                  disabled={!inputValue}
                  className="text-xs hover-lift"
                >
                  Submit Selection
                </Button>
              </div>
            )}
          </div>
        )}
        
        <div className={`text-xs mt-3 opacity-70 ${
          isUser ? 'text-white' : 'text-gray-500'
        }`}>
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage; 