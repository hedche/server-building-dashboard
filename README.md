# Server Building Dashboard

A React-based dashboard for monitoring server builds, managing preconfigurations, and assigning servers across multiple data center regions.

## Features

- **Build Overview**: Real-time visualization of server installation progress across racks
- **Preconfig Management**: Push preconfigurations to different regions (CBG, DUB, DAL)
- **Server Assignment**: Assign completed servers to customers
- **Build Logs**: View detailed build logs (coming soon)
- **SAML2 Authentication**: Secure login with enterprise SSO

## Development Setup

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd server-building-dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

### Environment Variables

Copy the example environment file and modify as needed:

```bash
cp .env.example .env
```

Then edit the `.env` file with your configuration:

```env
# Application Configuration
VITE_APP_NAME=Server Dashboard

# Backend API URL
VITE_BACKEND_URL=https://your-backend-api.com

# Development mode (bypasses SAML authentication)
VITE_DEV_MODE=true
```

#### Environment Variables Explained

- `VITE_APP_NAME`: The name displayed in the application header and login page (defaults to "SAML Portal")
- `VITE_BACKEND_URL`: The base URL for your backend API
- `VITE_DEV_MODE`: Set to `true` to bypass SAML authentication for local development

### Development Mode / Bypassing SAML Login

For local development and testing, you can bypass the SAML authentication system:

1. **Set Development Mode**: Add `VITE_DEV_MODE=true` to your `.env` file
2. **Mock User**: The app will automatically log you in as a test user (`dev@example.com`)
3. **Mock Data**: All API calls will return mock data instead of hitting the backend
4. **Dev Mode Button**: A yellow "Dev Mode" button appears in the bottom-right corner for easy identification

When `VITE_DEV_MODE=true`:
- No SAML authentication required
- All data is mocked locally
- API calls are simulated with realistic delays
- Perfect for frontend development without backend dependencies

### Building for Production

```bash
# Build the application
npm run build

# Preview the build
npm run preview
```

## Requirements for Backend API

The frontend expects the following API endpoints and JSON response formats:

### Authentication Endpoints

#### `GET /me`
Get current user information
```json
{
  "id": "user123",
  "email": "user@company.com",
  "name": "John Doe",
  "role": "admin"
}
```

#### `GET /saml/login`
Redirect endpoint for SAML authentication (no JSON response)

#### `POST /logout`
Logout endpoint (no JSON response expected)

### Build Status Endpoints

#### `GET /api/build-status`
Get current build status across all regions
```json
{
  "cbg": [
    {
      "rackID": "1-E",
      "hostname": "server-001",
      "dbid": "305589",
      "serial_number": "483446357",
      "percent_built": 55,
      "assigned_status": "not assigned",
      "machine_type": "Server",
      "status": "installing"
    }
  ],
  "dub": [...],
  "dal": [...]
}
```

#### `GET /api/build-history/{date}`
Get build history for a specific date (YYYY-MM-DD format)
```json
{
  "cbg": [
    {
      "rackID": "1-E",
      "hostname": "server-001",
      "dbid": "305589",
      "serial_number": "483446357",
      "percent_built": 100,
      "assigned_status": "not assigned",
      "machine_type": "Server",
      "status": "complete"
    }
  ],
  "dub": [...],
  "dal": [...]
}
```

### Server Details Endpoint

#### `GET /api/server-details?hostname={hostname}`
Get detailed information about a specific server
```json
{
  "hostname": "server-001",
  "dbid": "305589",
  "serial_number": "483446357",
  "rackID": "1-E",
  "percent_built": 55,
  "assigned_status": "not assigned",
  "machine_type": "Server",
  "status": "installing",
  "ip_address": "192.168.1.100",
  "mac_address": "00:1B:44:11:3A:B7",
  "cpu_model": "Intel Xeon E5-2680 v4",
  "ram_gb": 64,
  "storage_gb": 2000,
  "install_start_time": "2025-01-15T10:30:00Z",
  "estimated_completion": "2025-01-15T14:45:00Z",
  "last_heartbeat": "2025-01-15T12:15:30Z"
}
```

### Preconfig Endpoints

#### `GET /api/preconfigs`
Get all preconfigurations
```json
[
  {
    "id": "1",
    "depot": 1,
    "config": {
      "os": "ubuntu-20.04",
      "ram": "64GB",
      "storage": "2TB"
    },
    "created_at": "2025-01-15T10:00:00Z"
  }
]
```

#### `POST /api/push-preconfig`
Push preconfig to a specific depot
**Request Body:**
```json
{
  "depot": 1
}
```
**Response:**
```json
{
  "status": "success",
  "message": "Preconfig pushed successfully"
}
```

### Assignment Endpoint

#### `POST /api/assign`
Assign a server to a customer
**Request Body:**
```json
{
  "serial_number": "483446357",
  "hostname": "server-001",
  "dbid": "305589"
}
```
**Response:**
```json
{
  "status": "success",
  "message": "Server assigned successfully"
}
```

### Error Responses

All endpoints should return appropriate HTTP status codes and error messages:

```json
{
  "error": "Server not found",
  "code": 404
}
```

### Authentication

All API endpoints (except `/saml/login`) should:
- Accept cookies for session management
- Return 401 for unauthenticated requests
- Support CORS with credentials

### Region/Depot Mapping

- **CBG (Cambridge)**: depot = 1
- **DUB (Dublin)**: depot = 2  
- **DAL (Dallas)**: depot = 4

## Technology Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS
- **Routing**: React Router v7
- **Icons**: Lucide React
- **Build Tool**: Vite
- **Authentication**: SAML2 (production), Mock (development)

## Project Structure

```
src/
├── components/          # Reusable UI components
├── contexts/           # React contexts (Auth)
├── hooks/              # Custom React hooks
├── pages/              # Page components
├── types/              # TypeScript type definitions
└── main.tsx           # Application entry point
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test in development mode
5. Submit a pull request

## License

[Your License Here]