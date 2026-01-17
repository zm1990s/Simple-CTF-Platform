#!/bin/bash

# CTF Platform - Pre-deployment Checklist
# 部署前检查清单

echo "========================================"
echo "CTF Platform - Deployment Checklist"
echo "CTF平台 - 部署检查清单"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}!${NC} $1"
}

# 1. Check if .env file exists
echo "1. Checking environment configuration..."
if [ -f .env ]; then
    check_pass ".env file exists"
    
    # Check if SECRET_KEY has been changed
    if grep -q "your-secret-key-here" .env; then
        check_fail "SECRET_KEY still has default value! Please change it."
        ERRORS=$((ERRORS+1))
    else
        check_pass "SECRET_KEY has been customized"
    fi
else
    check_fail ".env file not found! Copy from .env.example"
    ERRORS=$((ERRORS+1))
fi
echo ""

# 2. Check Docker
echo "2. Checking Docker installation..."
if command -v docker &> /dev/null; then
    check_pass "Docker is installed"
    
    if docker ps &> /dev/null; then
        check_pass "Docker daemon is running"
    else
        check_fail "Docker daemon is not running"
        ERRORS=$((ERRORS+1))
    fi
else
    check_warn "Docker not found (OK if deploying locally)"
fi
echo ""

# 3. Check Docker Compose
echo "3. Checking Docker Compose..."
if command -v docker compose &> /dev/null; then
    check_pass "Docker Compose is installed"
else
    check_warn "Docker Compose not found (OK if deploying locally)"
fi
echo ""

# 4. Check Python
echo "4. Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    check_pass "Python is installed (version: $PYTHON_VERSION)"
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        check_pass "Virtual environment exists"
    else
        check_warn "Virtual environment not found (create with: python3 -m venv venv)"
    fi
else
    check_fail "Python3 not found"
    ERRORS=$((ERRORS+1))
fi
echo ""

# 5. Check required directories
echo "5. Checking required directories..."
REQUIRED_DIRS=("templates" "static" "routes" "uploads")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        check_pass "Directory $dir exists"
    else
        check_fail "Directory $dir not found"
        ERRORS=$((ERRORS+1))
    fi
done
echo ""

# 6. Check required files
echo "6. Checking required files..."
REQUIRED_FILES=("app.py" "wsgi.py" "config.py" "models.py" "forms.py" "requirements.txt")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "File $file exists"
    else
        check_fail "File $file not found"
        ERRORS=$((ERRORS+1))
    fi
done
echo ""

# 7. Check deployment files
echo "7. Checking deployment files..."
DEPLOY_FILES=("Dockerfile" "docker compose.yml" "k8s-deployment.yaml")
for file in "${DEPLOY_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "File $file exists"
    else
        check_warn "File $file not found"
    fi
done
echo ""

# Summary
echo "========================================"
echo "Summary / 总结"
echo "========================================"
if [ ${ERRORS:-0} -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo -e "${GREEN}✓ 所有关键检查都通过！${NC}"
    echo ""
    echo "You can now deploy the platform:"
    echo "您现在可以部署平台了："
    echo ""
    echo "  Option 1 - Docker Compose:"
    echo "    ./deploy.sh"
    echo ""
    echo "  Option 2 - Local Development:"
    echo "    python init_db.py"
    echo "    python app.py"
    echo ""
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s) found. Please fix them before deploying.${NC}"
    echo -e "${RED}✗ 发现 $ERRORS 个错误。请在部署前修复它们。${NC}"
    exit 1
fi
