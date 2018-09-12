# You should always specify a full version here to ensure all of your developers
# are running the same version of Node.
FROM node:8

#Copy file from directory to container
COPY . .

#where the next command where executed
WORKDIR /src/visualization

#install package
RUN npm i

# Build for production.
RUN npm run build --production

# Install `serve` to run the application.
RUN npm install -g serve

# Tell Docker about the port we'll run on.
EXPOSE 3000

# Set the command to start the node server.
CMD serve -l 3000 -s build