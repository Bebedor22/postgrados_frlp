# Imagen del frontend — Sistema de Posgrado (Expo web)
#
# Etapa 1: se compila la app web con `expo export` (archivos estáticos en /app/dist).
# Etapa 2: nginx sirve esos archivos. La imagen final no tiene Node ni node_modules.
#
# La URL del backend queda fija al compilar (las variables EXPO_PUBLIC_* se
# reemplazan en el código). Es la URL que usa el NAVEGADOR, por eso es localhost.

FROM node:22-alpine AS compilacion
WORKDIR /app

# Primero solo las dependencias, así Docker reutiliza esta capa si no cambian
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
ARG EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV EXPO_PUBLIC_API_URL=$EXPO_PUBLIC_API_URL
RUN npx expo export --platform web

FROM nginx:1.27-alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=compilacion /app/dist /usr/share/nginx/html
EXPOSE 80