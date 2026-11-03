FROM node:24-alpine AS build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# The deployed source is downloadable from the footer, without secrets or data.
FROM alpine:3.22 AS source
COPY . /source
RUN tar -czf /source.tar.gz -C /source .

FROM nginx:1.28-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html
COPY --from=source /source.tar.gz /usr/share/nginx/html/source.tar.gz
EXPOSE 80
