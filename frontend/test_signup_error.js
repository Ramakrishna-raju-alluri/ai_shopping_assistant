const axios = require('axios');

async function testSignup() {
  try {
    const response = await axios.post('http://localhost:8000/api/v1/auth/signup', {
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