#!/usr/bin/env node

/**
 * API Test Script
 * 
 * Tests the API endpoints with environment-aware configuration.
 * Usage:
 *   node test_api.js                    # Uses default/development API
 *   REACT_APP_API_BASE_URL=<url> node test_api.js  # Uses custom API URL
 */

const axios = require('axios');
require('dotenv').config(); // Load .env files

// Get API URL from environment with fallback
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8100/api/v1';

console.log('🧪 API Test Script');
console.log('📡 Testing API:', API_BASE_URL);
console.log('');

async function testHealthCheck() {
  console.log('🔍 Testing health check...');
  try {
    const response = await axios.get(`${API_BASE_URL.replace('/api/v1', '')}/health`);
    console.log('✅ Health check passed:', response.data);
    return true;
  } catch (error) {
    console.log('❌ Health check failed:', error.message);
    return false;
  }
}

async function testSignup() {
  console.log('🔍 Testing signup...');
  try {
    const response = await axios.post(`${API_BASE_URL}/auth/signup`, {
      username: `testuser_${Date.now()}`, // Unique username
      password: '123456',
      name: 'Test User',
      email: `test_${Date.now()}@example.com`
    });
    console.log('✅ Signup test passed:', response.data);
    return response.data;
  } catch (error) {
    console.log('❌ Signup test failed:');
    console.log('   Status:', error.response?.status);
    console.log('   Data:', JSON.stringify(error.response?.data, null, 2));
    return null;
  }
}

async function testLogin() {
  console.log('🔍 Testing login...');
  try {
    const response = await axios.post(`${API_BASE_URL}/auth/login`, {
      username: 'testuser',
      password: '123456'
    });
    console.log('✅ Login test passed:', response.data);
    return response.data;
  } catch (error) {
    console.log('❌ Login test failed:');
    console.log('   Status:', error.response?.status);
    console.log('   Data:', JSON.stringify(error.response?.data, null, 2));
    return null;
  }
}

async function testProducts(token = null) {
  console.log('🔍 Testing products endpoint...');
  try {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const response = await axios.get(`${API_BASE_URL}/products?limit=5`, { headers });
    console.log('✅ Products test passed:', {
      count: response.data.products?.length || 0,
      success: response.data.success
    });
    return true;
  } catch (error) {
    console.log('❌ Products test failed:');
    console.log('   Status:', error.response?.status);
    console.log('   Data:', JSON.stringify(error.response?.data, null, 2));
    return false;
  }
}

async function runAllTests() {
  console.log('🚀 Starting API tests...\n');
  
  const results = {
    health: await testHealthCheck(),
    signup: await testSignup(),
    login: await testLogin(),
    products: await testProducts()
  };
  
  console.log('\n📊 Test Results:');
  Object.entries(results).forEach(([test, passed]) => {
    console.log(`   ${passed ? '✅' : '❌'} ${test}`);
  });
  
  const passedCount = Object.values(results).filter(Boolean).length;
  const totalCount = Object.keys(results).length;
  
  console.log(`\n🎯 Summary: ${passedCount}/${totalCount} tests passed`);
  
  if (passedCount === totalCount) {
    console.log('🎉 All tests passed! API is working correctly.');
    process.exit(0);
  } else {
    console.log('💥 Some tests failed. Check your API configuration.');
    process.exit(1);
  }
}

// Handle command line arguments
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log('Usage:');
  console.log('  node test_api.js                           # Test with default API');
  console.log('  REACT_APP_API_BASE_URL=<url> node test_api.js  # Test with custom API');
  console.log('');
  console.log('Examples:');
  console.log('  node test_api.js');
  console.log('  REACT_APP_API_BASE_URL=http://localhost:8100/api/v1 node test_api.js');
  console.log('  REACT_APP_API_BASE_URL=http://your-api.com/api/v1 node test_api.js');
  process.exit(0);
}

// Run tests
runAllTests().catch(error => {
  console.error('💥 Unexpected error:', error.message);
  process.exit(1);
});