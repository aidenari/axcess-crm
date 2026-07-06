# Stage 1: Build the React application
FROM node:20-alpine as build

WORKDIR /app

# Install dependencies (use clean install for reproducibility)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code
COPY . .

# Build the application
# We need to inject the VITE_API_URL here or at runtime.
# Since this is a client-side app, environment variables are baked in at build time
# unless we use a runtime config solution.
# For simplicity in this Docker setup, we assume localhost usage or use a relative path proxy.
# However, the user request implies a simple deployment.
# We will set the API URL to http://localhost:8000 by default for the browser to access.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
