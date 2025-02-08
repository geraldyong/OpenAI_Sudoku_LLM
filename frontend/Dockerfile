# Use the official Nginx image as a base.
FROM nginx:alpine

# Remove the default static content.
RUN rm -rf /usr/share/nginx/html/*

# Copy the frontend files into the Nginx html directory.
COPY . /usr/share/nginx/html/

# Expose port 80.
EXPOSE 80

# Start Nginx when the container launches.
CMD ["nginx", "-g", "daemon off;"]
