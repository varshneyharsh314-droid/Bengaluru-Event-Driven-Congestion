FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install --silent

COPY . .

# Build React app static files
RUN npm run build

# Use simple local HTTP server to host production assets, or run in development server mode
# Here we expose port 5173 and execute Vite development server for ease of use
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
