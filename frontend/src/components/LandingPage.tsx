import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Button from './common/Button';
import CartWidget from './CartWidget';
import './LandingPage.css';

interface Product {
  item_id: string;
  name: string;
  price: number;
  tags: string[];
  in_stock: boolean;
  promo: boolean;
  category?: string;
  description?: string;
  image_url?: string;
}


const LandingPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCartWidget, setShowCartWidget] = useState(true);

  useEffect(() => {
    loadProducts();
    loadCategories();
  }, []);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      let url = 'http://localhost:8100/api/v1/products?limit=100';
      if (selectedCategory !== 'all') {
        url += `&category=${selectedCategory}`;
      }
      if (searchTerm) {
        url += `&search=${searchTerm}`;
      }

      const response = await fetch(url, { headers });
      const data = await response.json();

      if (data.success) {
        setProducts(data.products);
      }
    } catch (error) {
      console.error('Error loading products:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const response = await fetch('http://localhost:8100/api/v1/products/categories', { headers });
      const data = await response.json();

      if (data.success) {
        setCategories(data.categories.map((cat: any) => cat.name));
      }
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    loadProducts();
  };

  const handleSearch = () => {
    loadProducts();
  };

  const handleAddToCart = async (product: Product) => {
    try {
      console.log(`🛒 Adding product to cart: ${product.name}`);
      
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const response = await fetch('http://localhost:8100/api/v1/cart/add', {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          items: [{
            item_id: product.item_id,
            name: product.name,
            price: product.price,
            quantity: 1
          }]
        })
      });

      const data = await response.json();
      
      if (data.success) {
        console.log('✅ Product added to cart successfully');
        // Show success message
        alert(`✅ Added "${product.name}" to your cart!`);
      } else {
        console.error('❌ Failed to add product to cart:', data.message);
        alert(`❌ Failed to add "${product.name}" to cart: ${data.message}`);
      }
    } catch (error) {
      console.error('❌ Error adding product to cart:', error);
      alert('❌ Error adding product to cart. Please try again.');
    }
  };

  const getProductImage = (product: Product) => {
    // If product has an image URL, use it
    if (product.image_url) {
      return product.image_url;
    }
    
    // Fallback to emoji if no image URL
    const category = product.category?.toLowerCase() || '';
    const tags = product.tags.map(tag => tag.toLowerCase());
    
    if (category.includes('vegetable') || tags.includes('vegetable')) {
      return '🥬';
    } else if (category.includes('fruit') || tags.includes('fruit')) {
      return '🍎';
    } else if (category.includes('meat') || tags.includes('protein')) {
      return '🥩';
    } else if (category.includes('dairy') || tags.includes('dairy')) {
      return '🥛';
    } else if (category.includes('grain') || tags.includes('grain')) {
      return '🍚';
    } else if (tags.includes('organic')) {
      return '🌱';
    } else {
      return '🛒';
    }
  };

  const getCategoryIcon = (category: string) => {
    const categoryLower = category.toLowerCase();
    if (categoryLower.includes('vegetable')) return '🥬';
    if (categoryLower.includes('fruit')) return '🍎';
    if (categoryLower.includes('meat') || categoryLower.includes('protein')) return '🥩';
    if (categoryLower.includes('dairy')) return '🥛';
    if (categoryLower.includes('grain')) return '🍚';
    if (categoryLower.includes('organic')) return '🌱';
    return '🛒';
  };

  return (
    <div className="landing-page">
      {/* Header */}
      <div className="landing-header">
        <div className="header-left">
          <img src="/coles-logo.png" alt="Coles Logo" className="coles-logo" />
          <h1>Coles Shopping</h1>
        </div>
        <div className="header-right">
          <Button 
            variant="primary" 
            size="lg" 
            onClick={() => navigate('/dashboard')}
            className="chatbot-btn"
          >
            🤖 Personal Shopping Assistant
          </Button>
          <Button variant="danger" size="sm" onClick={logout}>
            Logout
          </Button>
        </div>
      </div>



      {/* Filters Section */}
      <div className="filters-section">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button onClick={handleSearch} variant="primary" size="sm">
            🔍 Search
          </Button>
        </div>

        <div className="category-filters">
          <button
            className={`category-btn ${selectedCategory === 'all' ? 'active' : ''}`}
            onClick={() => handleCategoryChange('all')}
          >
            🛒 All Products
          </button>
          {categories.map((category) => (
            <button
              key={category}
              className={`category-btn ${selectedCategory === category ? 'active' : ''}`}
              onClick={() => handleCategoryChange(category)}
            >
              {getCategoryIcon(category)} {category}
            </button>
          ))}
        </div>
      </div>

      {/* Products Grid */}
      <div className="products-section">
        <div className="section-header">
          <h3>Our Products</h3>
          <p>{loading ? 'Loading...' : `${products.length} products available`}</p>
        </div>

        {loading ? (
          <div className="loading">Loading products...</div>
        ) : (
          <div className="products-grid">
            {products.map((product) => (
              <div key={product.item_id} className="product-card">
                <div className="product-image">
                  {product.image_url ? (
                    <img 
                      src={product.image_url} 
                      alt={product.name}
                      className="product-image-img"
                      onError={(e) => {
                        const target = e.currentTarget as HTMLImageElement;
                        target.style.display = 'none';
                        const nextSibling = target.nextElementSibling as HTMLElement;
                        if (nextSibling) {
                          nextSibling.style.display = 'block';
                        }
                      }}
                    />
                  ) : null}
                  <span className="product-emoji" style={{ display: product.image_url ? 'none' : 'block' }}>
                    {getProductImage(product)}
                  </span>
                </div>
                <div className="product-info">
                  <h3 className="product-name">{product.name}</h3>
                  <div className="product-price">${product.price.toFixed(2)}</div>
                  <div className="product-tags">
                    {product.tags.slice(0, 3).map((tag, index) => (
                      <span key={index} className="tag">{tag}</span>
                    ))}
                  </div>
                  <div className="product-actions">
                    <Button
                      onClick={() => handleAddToCart(product)}
                      variant="success"
                      size="sm"
                      disabled={!product.in_stock}
                    >
                      {product.in_stock ? '🛒 Add to Cart' : '❌ Out of Stock'}
                    </Button>
                    {product.promo && <span className="promo-badge">🔥 Sale</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && products.length === 0 && (
          <div className="no-products">
            <h3>No products found</h3>
            <p>Try adjusting your search or category filters.</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="landing-footer">
        <div className="footer-content">
          <div className="footer-section">
            <h4>Need Help?</h4>
            <p>Our AI shopping assistant is here to help you find the perfect products!</p>
            <Button 
              variant="primary" 
              onClick={() => navigate('/dashboard')}
              className="footer-chatbot-btn"
            >
              🤖 Start Shopping Assistant
            </Button>
          </div>
          <div className="footer-section">
            <h4>Quick Links</h4>
            <ul>
              <li><a href="#" onClick={() => navigate('/profile')}>My Profile</a></li>
              <li><a href="#" onClick={() => navigate('/dashboard')}>Shopping Assistant</a></li>
              <li><a href="#" onClick={logout}>Logout</a></li>
            </ul>
          </div>
        </div>
      </div>

      {/* Floating Cart Widget */}
      <CartWidget
        isVisible={showCartWidget}
        onToggle={() => setShowCartWidget(!showCartWidget)}
      />
    </div>
  );
};

export default LandingPage; 