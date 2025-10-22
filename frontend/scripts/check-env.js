#!/usr/bin/env node

/**
 * Environment Configuration Checker
 * 
 * This script helps verify that environment variables are set up correctly
 * for different build modes.
 */

const fs = require('fs');
const path = require('path');

const envFiles = [
  '.env',
  '.env.development', 
  '.env.production'
];

console.log('🔍 Checking environment configuration...\n');

envFiles.forEach(file => {
  const filePath = path.join(__dirname, '..', file);
  
  if (fs.existsSync(filePath)) {
    console.log(`✅ ${file} exists`);
    
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n').filter(line => line.trim() && !line.startsWith('#'));
      
      lines.forEach(line => {
        const [key, value] = line.split('=');
        if (key && value) {
          console.log(`   ${key.trim()}=${value.trim()}`);
        }
      });
    } catch (error) {
      console.log(`   ⚠️  Error reading file: ${error.message}`);
    }
  } else {
    console.log(`❌ ${file} missing`);
  }
  
  console.log('');
});

console.log('📋 Environment Usage:');
console.log('   npm start          → Uses .env.development');
console.log('   npm run build      → Uses .env.production');
console.log('   Fallback           → Uses .env');
console.log('');

console.log('🔧 To update API URLs:');
console.log('   Development: Edit .env.development');
console.log('   Production:  Edit .env.production');
console.log('');

// Check if the config file exists
const configPath = path.join(__dirname, '..', 'src', 'config', 'api.ts');
if (fs.existsSync(configPath)) {
  console.log('✅ API config file exists: src/config/api.ts');
} else {
  console.log('❌ API config file missing: src/config/api.ts');
}

console.log('\n🎉 Environment check complete!');