#!/bin/bash

# Docker Compose Management Script
# Manages dev and prod environments for the Server Building Dashboard backend

set -e

# Detect if terminal supports colors
if [ -t 1 ] && command -v tput &> /dev/null && tput setaf 1 &> /dev/null; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    BOLD=$(tput bold)
    NC=$(tput sgr0)
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    BOLD=''
    NC=''
fi

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default environment
ENV="prod"
COMPOSE_FILE="docker-compose.yml"

# Function to print colored messages
print_info() {
    printf "%bℹ%b %s\n" "${BLUE}" "${NC}" "$1"
}

print_success() {
    printf "%b✓%b %s\n" "${GREEN}" "${NC}" "$1"
}

print_error() {
    printf "%b✗%b %s\n" "${RED}" "${NC}" "$1"
}

print_warning() {
    printf "%b⚠%b %s\n" "${YELLOW}" "${NC}" "$1"
}

# Function to display help
show_help() {
    cat << EOF
${GREEN}${BOLD}Server Building Dashboard - Docker Compose Manager${NC}

${BLUE}Usage:${NC}
  ./docker.sh [ENVIRONMENT] [COMMAND]

${BLUE}Environments:${NC}
  dev       Use development configuration (docker-compose.dev.yml)
  prod      Use production configuration (docker-compose.yml) [default]

${BLUE}Commands:${NC}
  start     Start containers (creates and starts if not exists)
  stop      Stop running containers
  restart   Restart containers
  rebuild   Rebuild images and restart containers
  help      Show this help message

${BLUE}Examples:${NC}
  ./docker.sh dev start       # Start development environment
  ./docker.sh prod rebuild    # Rebuild and start production
  ./docker.sh stop            # Stop production (default env)
  ./docker.sh dev restart     # Restart development environment

${BLUE}Environment Files Required:${NC}
  Production: ${YELLOW}.env${NC}
  Development: ${YELLOW}.env.dev${NC}

EOF
}

# Function to check if required files exist
check_requirements() {
    local env_file=""

    if [ "$ENV" = "dev" ]; then
        env_file=".env.dev"
    else
        env_file=".env"
    fi

    if [ ! -f "$SCRIPT_DIR/$env_file" ]; then
        print_error "Environment file $env_file not found!"
        print_info "Create it by running: ./setup_script.sh"
        exit 1
    fi

    if [ ! -f "$SCRIPT_DIR/$COMPOSE_FILE" ]; then
        print_error "Docker Compose file $COMPOSE_FILE not found!"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
}

# Function to get docker compose command (handles both docker-compose and docker compose)
get_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        echo "docker compose"
    fi
}

# Function to start containers
do_start() {
    print_info "Starting $ENV environment..."
    local compose_cmd=$(get_compose_cmd)

    cd "$SCRIPT_DIR"
    $compose_cmd -f "$COMPOSE_FILE" up -d

    print_success "$ENV environment started successfully"
    print_info "View logs with: $compose_cmd -f $COMPOSE_FILE logs -f"
}

# Function to stop containers
do_stop() {
    print_info "Stopping $ENV environment..."
    local compose_cmd=$(get_compose_cmd)

    cd "$SCRIPT_DIR"
    $compose_cmd -f "$COMPOSE_FILE" down

    print_success "$ENV environment stopped successfully"
}

# Function to restart containers
do_restart() {
    print_info "Restarting $ENV environment..."
    local compose_cmd=$(get_compose_cmd)

    cd "$SCRIPT_DIR"
    $compose_cmd -f "$COMPOSE_FILE" restart

    print_success "$ENV environment restarted successfully"
}

# Function to rebuild containers
do_rebuild() {
    print_info "Rebuilding $ENV environment..."
    local compose_cmd=$(get_compose_cmd)

    cd "$SCRIPT_DIR"

    print_info "Stopping containers..."
    $compose_cmd -f "$COMPOSE_FILE" down

    print_info "Building images..."
    $compose_cmd -f "$COMPOSE_FILE" build --no-cache

    print_info "Starting containers..."
    $compose_cmd -f "$COMPOSE_FILE" up -d

    print_success "$ENV environment rebuilt and started successfully"
    print_info "View logs with: $compose_cmd -f $COMPOSE_FILE logs -f"
}

# Parse arguments
if [ $# -eq 0 ]; then
    print_error "No command specified"
    echo ""
    show_help
    exit 1
fi

# Check if first argument is environment
if [ "$1" = "dev" ] || [ "$1" = "prod" ]; then
    ENV="$1"
    if [ "$ENV" = "dev" ]; then
        COMPOSE_FILE="docker-compose.dev.yml"
    fi
    shift
fi

# Check if command is provided
if [ $# -eq 0 ]; then
    print_error "No command specified"
    echo ""
    show_help
    exit 1
fi

COMMAND="$1"

# Handle commands
case "$COMMAND" in
    start)
        check_requirements
        do_start
        ;;
    stop)
        check_requirements
        do_stop
        ;;
    restart)
        check_requirements
        do_restart
        ;;
    rebuild)
        check_requirements
        do_rebuild
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac
