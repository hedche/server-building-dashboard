# Multi-stage build for security and optimization
# Stage 1: Build the application
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY package*.json ./

# Install dependencies with clean install for reproducible builds
# --omit=dev excludes devDependencies in production
RUN npm ci --ignore-scripts && \
    npm cache clean --force

# Copy application source
COPY . .

# Build arguments for environment variables
# These should be passed at build time, NOT runtime for Vite
ARG VITE_BACKEND_URL
ARG VITE_DEV_MODE=false
ARG VITE_LOGIN_LOGO_PATH
ARG VITE_LOGIN_LOGO_BG_COLOR
ARG VITE_APP_NAME="Server Dashboard"

# Set environment variables for build
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL
ENV VITE_DEV_MODE=$VITE_DEV_MODE
ENV VITE_LOGIN_LOGO_PATH=$VITE_LOGIN_LOGO_PATH
ENV VITE_LOGIN_LOGO_BG_COLOR=$VITE_LOGIN_LOGO_BG_COLOR
ENV VITE_APP_NAME=$VITE_APP_NAME
ENV NODE_ENV=production

# Build the application
RUN npm run build

# Stage 2: Production server with simple HTTP server
FROM node:18-alpine AS production

# Security: Install security updates and dumb-init
RUN apk upgrade --no-cache && \
    apk add --no-cache dumb-init && \
    npm install -g serve@14.2.1

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Set working directory
WORKDIR /app

# Copy built application from builder stage
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist

# Switch to non-root user
USER appuser

# Expose port 8080 (non-privileged port)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

# Use dumb-init as entrypoint for proper signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Start serve with SPA support and security headers
CMD ["serve", "-s", "dist", "-l", "8080", "--no-request-logging", "--no-clipboard"]
