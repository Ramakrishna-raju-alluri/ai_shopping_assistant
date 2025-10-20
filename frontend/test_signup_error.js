const axios = require('axios');

// Get API URL from environment or use localhost as fallback
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8100/api/v1';

async function testSignup() {
  console.log('Testing signup with API:', API_BASE_URL);
  
  try {
    const response = await axios.post(`${API_BASE_URL}/auth/signup`, {
      username: 'testuser',
      password: '123',
      name: 'Test User',
      email: 'test@example.com'
    });
    console.log('Success:', response.data);
  } catch (error) {
    console.log('Error Status:', error.response?.status);
    console.log('Error Data:', JSON.stringify(error.response?.data, null, 2));
    console.log('Error Message:', error.message);
    console.log('Full Error:', error);
  }
}

testSignup(); 