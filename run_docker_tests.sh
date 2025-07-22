#!/bin/bash

# Docker Setup and Testing Script for Sales Agent Microservice
# This script starts all services and runs comprehensive end-to-end testing

echo "🚀 Sales Agent Microservice - Docker Setup & Testing"
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed and running
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker Desktop."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    
    print_success "Docker is installed and running"
}

# Check if docker-compose is available
check_docker_compose() {
    print_status "Checking Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose is not available"
        exit 1
    fi
    
    print_success "Docker Compose is available: $COMPOSE_CMD"
}

# Clean up existing containers
cleanup_containers() {
    print_status "Cleaning up existing containers..."
    
    $COMPOSE_CMD down --volumes --remove-orphans 2>/dev/null || true
    
    # Remove any dangling containers
    docker container prune -f 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Build and start all services
start_services() {
    print_status "Building and starting all services..."
    
    # Build the application image
    print_status "Building sales agent image..."
    $COMPOSE_CMD build
    
    if [ $? -ne 0 ]; then
        print_error "Failed to build application image"
        exit 1
    fi
    
    # Start all services
    print_status "Starting services in background..."
    $COMPOSE_CMD up -d
    
    if [ $? -ne 0 ]; then
        print_error "Failed to start services"
        exit 1
    fi
    
    print_success "All services started"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be healthy..."
    
    # Wait for PostgreSQL
    print_status "Waiting for PostgreSQL..."
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker exec sales_postgres pg_isready -U user -d sales_db &> /dev/null; then
            print_success "PostgreSQL is ready"
            break
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "PostgreSQL failed to start"
        show_logs
        exit 1
    fi
    
    # Wait for MongoDB
    print_status "Waiting for MongoDB..."
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker exec sales_mongodb mongo --eval "db.adminCommand('ping')" &> /dev/null; then
            print_success "MongoDB is ready"
            break
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "MongoDB failed to start"
        show_logs
        exit 1
    fi
    
    # Wait for Sales Agent API
    print_status "Waiting for Sales Agent API..."
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/health &> /dev/null; then
            print_success "Sales Agent API is ready"
            break
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 3
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Sales Agent API failed to start"
        show_logs
        exit 1
    fi
    
    print_success "All services are healthy and ready!"
}

# Show service logs
show_logs() {
    print_status "Showing service logs..."
    echo "==================== PostgreSQL Logs ===================="
    $COMPOSE_CMD logs postgres | tail -20
    echo ""
    echo "==================== MongoDB Logs ===================="
    $COMPOSE_CMD logs mongodb | tail -20
    echo ""
    echo "==================== Sales Agent Logs ===================="
    $COMPOSE_CMD logs sales-agent | tail -20
}

# Check service status
check_service_status() {
    print_status "Checking service status..."
    
    echo "==================== Container Status ===================="
    $COMPOSE_CMD ps
    echo ""
    
    echo "==================== API Health Check ===================="
    response=$(curl -s http://localhost:8000/health)
    if [ $? -eq 0 ]; then
        print_success "API Health: $response"
    else
        print_error "API Health check failed"
    fi
    echo ""
    
    echo "==================== Database Status ===================="
    # Check PostgreSQL
    if docker exec sales_postgres pg_isready -U user -d sales_db &> /dev/null; then
        print_success "PostgreSQL: Connected"
        product_count=$(docker exec sales_postgres psql -U user -d sales_db -t -c "SELECT COUNT(*) FROM products;" 2>/dev/null | xargs)
        print_status "Products in database: $product_count"
    else
        print_error "PostgreSQL: Connection failed"
    fi
    
    # Check MongoDB
    if docker exec sales_mongodb mongo --eval "db.adminCommand('ping')" &> /dev/null; then
        print_success "MongoDB: Connected"
    else
        print_error "MongoDB: Connection failed"
    fi
}

# Install Python dependencies for testing
install_test_dependencies() {
    print_status "Installing Python dependencies for testing..."
    
    # Check if pip is available
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        print_error "pip is not available. Please install Python and pip."
        exit 1
    fi
    
    # Use pip3 if available, otherwise pip
    PIP_CMD="pip3"
    if ! command -v pip3 &> /dev/null; then
        PIP_CMD="pip"
    fi
    
    # Install required packages
    $PIP_CMD install requests pymongo psycopg2-binary --quiet
    
    if [ $? -eq 0 ]; then
        print_success "Test dependencies installed"
    else
        print_warning "Some dependencies might not be installed. Tests may fail."
    fi
}

# Run the master end-to-end test
run_e2e_tests() {
    print_status "Running master end-to-end tests..."
    
    if [ -f "master_e2e_test.py" ]; then
        python3 master_e2e_test.py
    else
        print_error "master_e2e_test.py not found"
        exit 1
    fi
}

# Run quick connectivity tests
run_quick_tests() {
    print_status "Running quick connectivity tests..."
    
    echo "==================== Quick API Tests ===================="
    
    # Test health endpoint
    echo "Testing /health endpoint..."
    curl -s http://localhost:8000/health | python3 -m json.tool
    echo ""
    
    # Test webhook endpoint with a simple message
    echo "Testing webhook endpoint..."
    curl -s -X POST http://localhost:8000/api/webhook \
         -H "Content-Type: application/json" \
         -d '{"sender": "test_user", "recipient": "test_page", "text": "Hello, I want a perfume"}' | \
         python3 -m json.tool
    echo ""
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    $COMPOSE_CMD down --volumes
    print_success "Cleanup completed"
}

# Main script execution
main() {
    echo "Starting Sales Agent Docker Setup & Testing..."
    echo "Current directory: $(pwd)"
    echo ""
    
    # Trap cleanup on script exit
    trap cleanup EXIT
    
    # Check prerequisites
    check_docker
    check_docker_compose
    
    # Setup services
    cleanup_containers
    start_services
    wait_for_services
    
    # Check status
    check_service_status
    
    # Install test dependencies
    install_test_dependencies
    
    # Ask user what to run
    echo ""
    echo "What would you like to do?"
    echo "1) Run quick connectivity tests"
    echo "2) Run full end-to-end tests"
    echo "3) Show service logs"
    echo "4) Keep services running (no tests)"
    echo ""
    read -p "Enter your choice (1-4): " choice
    
    case $choice in
        1)
            run_quick_tests
            ;;
        2)
            run_e2e_tests
            ;;
        3)
            show_logs
            ;;
        4)
            print_success "Services are running. Use 'docker-compose logs -f' to follow logs."
            print_status "API URL: http://localhost:8000"
            print_status "PostgreSQL: localhost:5432"
            print_status "MongoDB: localhost:27017"
            print_status "Press Ctrl+C to stop services when done."
            
            # Remove trap so services keep running
            trap - EXIT
            
            # Wait for user interrupt
            while true; do
                sleep 1
            done
            ;;
        *)
            print_warning "Invalid choice. Running quick tests..."
            run_quick_tests
            ;;
    esac
    
    print_success "Script completed!"
}

# Run main function
main "$@"
