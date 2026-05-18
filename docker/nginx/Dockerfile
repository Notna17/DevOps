FROM nginx:1.25-alpine

RUN rm -f /etc/nginx/conf.d/default.conf

COPY nginx-mywebapp.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
