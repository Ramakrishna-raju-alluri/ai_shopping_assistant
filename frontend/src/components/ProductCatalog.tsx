import React, { useState, useEffect } from 'react';
import Button from './common/Button';
import './ProductCatalog.css';

interface Product {
  item_id: string;
  name: string;
  price: number;
  tags: string[];
  in_stock: boolean;
  promo: boolean;
  category?: string;
  description?: string;
}

interface ProductCatalogProps {
  isOpen: boolean;
  onClose: () => void;
  onAddToCart: (product: Product) => void;
  onCartUpdate?: () => void;
}

const ProductCatalog: React.FC<ProductCatalogProps> = ({ isOpen, onClose, onAddToCart, onCartUpdate }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadProducts();
      loadCategories();
    }
  }, [isOpen]);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      let url = 'http://localhost:8000/api/v1/products?limit=100';
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
      
      const response = await fetch('http://localhost:8000/api/v1/products/categories', { headers });
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

  const getProductImage = (product: Product) => {
    // Generate placeholder images based on product category/tags
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

  if (!isOpen) return null;

  return (
    <div className="product-catalog-overlay">
      <div className="product-catalog-modal">
        <div className="catalog-header">
          <div>
            <h2>🛍️ Product Catalog</h2>
            <div className="product-counter">
              {loading ? 'Loading...' : `${products.length} products available`}
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="catalog-filters">
          <div className="search-bar">
            <input
              type="text"
              placeholder="Search products..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch} variant="primary" size="sm">
               Search
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

        <div className="catalog-content">
          {loading ? (
            <div className="loading">Loading products...</div>
          ) : (
            <div className="products-grid">
              {products.map((product) => (
                <div key={product.item_id} className="product-card">
                  <div className="product-image">
                    <span className="product-emoji">{getProductImage(product)}</span>
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
                         onClick={() => {
                           onAddToCart(product);
                           if (onCartUpdate) {
                             onCartUpdate();
                           }
                         }}
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
      </div>
    </div>
  );
};

export default ProductCatalog; 