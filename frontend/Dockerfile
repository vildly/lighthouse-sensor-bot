FROM node:20.8.0-bullseye-slim

# Set the working directory within the container
WORKDIR /frontend

# Copy the package.json and package-lock.json files to the container
COPY package*.json ./

# Install the Node.js dependencies
RUN npm install 

# Copy the rest of the application code into the container
COPY . .

# Build the Next.js application
RUN npm run build

# Expose the application's port
EXPOSE 3000

# Start the application in production mode
CMD ["npm", "run", "start"]