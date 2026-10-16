FROM nginx:1.28.0-alpine@sha256:30f1c0d78e0ad60901648be663a710bdadf19e4c10ac6782c235200619158284
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/index.html frontend/app.js frontend/styles.css /usr/share/nginx/html/
