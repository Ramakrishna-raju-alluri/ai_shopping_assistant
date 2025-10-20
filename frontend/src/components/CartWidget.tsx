import React, { useState, useEffect } from 'react';
import Button from './common/Button';
import { API_CONFIG } from '../config/api';
import './CartWidget.css';

interface CartItem {
  item_id: string;
  name: string;
  price: number | string;
  quantity: number | string;
  added_at: string;
}

interface Cart {
  user_id: string;
  items: CartItem[];
  total_items: number;
  total_cost: number | string;
  last_updated: string;
}

interface CartWidgetProps {
  isVisible: boolean;
  onToggle: () => void;
}

const CartWidget: React.FC<CartWidgetProps> = ({ isVisible, onToggle }) => {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Helper function to safely format prices
  const formatPrice = (price: number | string): string => {
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    return numPrice.toFixed(2);
  };

  const loadCart = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/cart`, { headers });
      const data = await response.json();
      
      if (data.success) {
        setCart(data.cart);
      }
    } catch (error) {
      console.error('Error loading cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (itemId: string, quantity: number) => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
      
      // Ensure quantity is a valid integer
      const newQuantity = Math.max(1, Math.floor(Number(quantity)));
      
      console.log(`Updating quantity for item ${itemId}: ${quantity} -> ${newQuantity}`);
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/cart/update`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({
          item_id: itemId,
          quantity: newQuantity
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setCart(data.cart);
        console.log('Cart updated successfully:', data.cart);
      } else {
        console.error('Failed to update cart:', data.message);
      }
    } catch (error) {
      console.error('Error updating quantity:', error);
    }
  };

  const removeItem = async (itemId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/cart/remove/${itemId}`, {
        method: 'DELETE',
        headers
      });
      
      const data = await response.json();
      if (data.success) {
        setCart(data.cart);
      }
    } catch (error) {
      console.error('Error removing item:', error);
    }
  };

  const clearCart = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/cart/clear`, {
        method: 'DELETE',
        headers
      });
      
      const data = await response.json();
      if (data.success) {
        setCart(data.cart);
      }
    } catch (error) {
      console.error('Error clearing cart:', error);
    }
  };

  // Load cart when component mounts or when cart changes
  useEffect(() => {
    if (isVisible) {
      loadCart();
    }
  }, [isVisible]);

  // Auto-refresh cart every 30 seconds
  useEffect(() => {
    if (isVisible) {
      const interval = setInterval(loadCart, 30000);
      return () => clearInterval(interval);
    }
  }, [isVisible]);

  // Load cart when modal opens
  useEffect(() => {
    if (isModalOpen) {
      loadCart();
    }
  }, [isModalOpen]);

  if (!isVisible) return null;

    return (
    <>
      {/* Floating Cart Button */}
      <div className="cart-widget" onClick={() => setIsModalOpen(true)}>
        🛒
        {cart && cart.total_items > 0 && (
          <span className="cart-badge">{cart.total_items}</span>
        )}
      </div>

      {/* Cart Modal */}
      {isModalOpen && (
        <div className="cart-modal" onClick={() => setIsModalOpen(false)}>
          <div className="cart-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="cart-modal-header">
              <div>
                <h2>🛒 Shopping Cart</h2>
                {cart && (
                  <div className="cart-modal-total">
                    Total: ${formatPrice(cart.total_cost)}
                  </div>
                )}
              </div>
              <button className="close-modal-btn" onClick={() => setIsModalOpen(false)}>
                ×
              </button>
            </div>

            <div className="cart-content">
              {loading ? (
                <div className="cart-loading">Loading cart...</div>
              ) : cart && cart.items.length > 0 ? (
                <>
                  <div className="cart-items">
                    {cart.items.map((item) => (
                      <div key={item.item_id} className="cart-item">
                        <div className="item-info">
                          <div className="item-name">{item.name}</div>
                          <div className="item-price">${formatPrice(item.price)}</div>
                        </div>
                        <div className="item-controls">
                          <div className="quantity-controls">
                            <button
                              className="quantity-btn"
                              onClick={() => updateQuantity(item.item_id, Number(item.quantity) - 1)}
                              disabled={Number(item.quantity) <= 1}
                            >
                              -
                            </button>
                            <span className="quantity">{item.quantity}</span>
                            <button
                              className="quantity-btn"
                              onClick={() => updateQuantity(item.item_id, Number(item.quantity) + 1)}
                            >
                              +
                            </button>
                          </div>
                          <button
                            className="remove-btn"
                            onClick={() => removeItem(item.item_id)}
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="cart-actions">
                    <Button
                      onClick={clearCart}
                      variant="danger"
                      size="sm"
                    >
                      Clear Cart
                    </Button>
                    <Button
                      onClick={() => {
                        // You could add checkout functionality here
                        alert('Checkout functionality coming soon!');
                      }}
                      variant="success"
                      size="sm"
                    >
                      Checkout
                    </Button>
                  </div>
                </>
              ) : (
                <div className="empty-cart">
                  <div className="empty-cart-icon">🛒</div>
                  <div className="empty-cart-text">Your cart is empty</div>
                  <div className="empty-cart-subtext">Add some products to get started!</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default CartWidget; 