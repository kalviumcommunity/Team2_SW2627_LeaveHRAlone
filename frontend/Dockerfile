FROM node:20-alpine AS base

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy application source
COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_TELEMETRY_DISABLED=1

# Build application
RUN npm run build

# Production stage
EXPOSE 3000
ENV PORT=3000
ENV NODE_ENV=production

CMD ["npm", "start"]
