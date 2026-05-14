# Use a minimal nginx base image for reverse proxying.
FROM nginx:1.25-alpine

# Remove the default config if present.
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy the docker-specific nginx configuration.
COPY nginx-mywebapp.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port.
EXPOSE 80
