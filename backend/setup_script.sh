#!/bin/bash
# Setup script for Server Building Dashboard Backend
# Follows DevSecOps best practices

set -e

echo "========================================"
echo "Server Building Dashboard Backend Setup"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.11 or higher is required"
    echo "   Current version: $python_version"
    exit 1
fi
echo "✓ Python version: $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create SAML metadata directory
echo "Setting up SAML metadata directory..."
mkdir -p saml_metadata
chmod 700 saml_metadata
echo "✓ SAML metadata directory created"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    
    # Generate a secure secret key
    secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env with generated secret
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" .env
    else
        # Linux
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" .env
    fi
    
    echo "✓ .env file created with generated SECRET_KEY"
    echo ""
    echo "⚠️  IMPORTANT: Review and update .env file with your configuration:"
    echo "   - SAML_ACS_URL (Entity ID is auto-derived from this)"
    echo "   - CORS_ORIGINS"
    echo "   - FRONTEND_URL"
else
    echo "✓ .env file already exists"
fi
echo ""

# Check for SAML metadata
if [ ! -f "saml_metadata/idp_metadata.xml" ]; then
    echo "⚠️  WARNING: SAML IDP metadata not found"
    echo "   Please place your IDP metadata XML file at:"
    echo "   saml_metadata/idp_metadata.xml"
    echo ""
    echo "   You can obtain this from your Identity Provider:"
    echo "   - Azure AD: https://login.microsoftonline.com/{tenant}/federationmetadata/2007-06/federationmetadata.xml"
    echo "   - ADFS: https://{adfs-server}/FederationMetadata/2007-06/FederationMetadata.xml"
else
    echo "✓ SAML IDP metadata found"
fi
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Place your IDP metadata at: saml_metadata/idp_metadata.xml"
echo "2. Update .env with your configuration"
echo "3. Run the development server:"
echo "   source venv/bin/activate"
echo "   uvicorn main:app --reload"
echo ""
echo "For production deployment, see README.md"
echo ""