# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS build
WORKDIR /app
RUN apk add --no-cache bash
COPY package.json package-lock.json ./
RUN npm ci
RUN npm install -g pnpm@10.30.3
# 强制装 alpine 需要的 musl native 包（npm ci 装的是 gnu 版本）
RUN cd /app && npm install @rollup/rollup-linux-x64-musl --no-save --include=optional
COPY . .
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
