# Environment Configuration

This project uses environment variables to manage API endpoints for different environments.

## Environment Files

- `.env` - Default/fallback environment variables
- `.env.development` - Development environment (used with `npm start`)
- `.env.production` - Production environment (used with `npm run build`)

## Available Variables

### REACT_APP_API_BASE_URL
The base URL for all API calls.

**Development:** `http://localhost:8100/api/v1`
**Production:** `http://ai-shopping-assistant-backend.eba-kdhudhcc.us-west-2.elasticbeanstalk.com/api/v1`

## Usage

The environment variables are automatically loaded based on the build mode:

- **Development mode** (`npm start`): Uses `.env.development`
- **Production build** (`npm run build`): Uses `.env.production`
- **Fallback**: Uses `.env` if specific environment file is missing

## Configuration File

All API configuration is centralized in `src/config/api.ts`:

```typescript
import { API_CONFIG } from '../config/api';

// Use in components
const response = await fetch(`${API_CONFIG.BASE_URL}/endpoint`);
```

## Helper Functions

- `getApiUrl(endpoint)` - Get full API URL for an endpoint
- `getApiBaseUrl()` - Get base URL without /api/v1 suffix
- `isDevelopment` - Check if running in development mode
- `isProduction` - Check if running in production mode

## Updating API URLs

To change API endpoints:

1. **For development**: Update `frontend/.env.development`
2. **For production**: Update `frontend/.env.production`
3. **For both**: Update `frontend/.env` (fallback)

No code changes needed - the configuration is automatically picked up!

## Testing

### Test Scripts Available

```bash
# Check environment configuration
npm run check-env

# Test API with current environment
npm run test-api

# Test production API specifically
npm run test-api-prod

# Test with custom API URL
REACT_APP_API_BASE_URL=http://your-api.com/api/v1 npm run test-api
```

### Files Updated

All these files now use environment variables:

- ✅ `src/services/api.ts` - Main API service
- ✅ `src/services/chatHistoryAPI.ts` - Chat history service  
- ✅ `src/components/**/*.tsx` - All React components
- ✅ `index.html` - Static HTML demo (auto-detects environment)
- ✅ `test_api.js` - API testing script
- ✅ `test_signup_error.js` - Legacy test (updated)

## Example

```bash
# Development
REACT_APP_API_BASE_URL=http://localhost:8100/api/v1

# Production
REACT_APP_API_BASE_URL=http://ai-shopping-assistant-backend.eba-kdhudhcc.us-west-2.elasticbeanstalk.com/api/v1

# Custom environment
REACT_APP_API_BASE_URL=https://your-production-api.com/api/v1
```