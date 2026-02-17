# Development Dockerfile for Vite React App
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm install

COPY . .

EXPOSE 3000

# Use 'dev' script with --host ensuring it listens on 0.0.0.0
CMD ["npm", "run", "dev", "--", "--host"]
