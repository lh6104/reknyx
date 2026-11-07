FROM node:22.23.2-bookworm-slim AS build
WORKDIR /app
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm ci --ignore-scripts
COPY frontend ./frontend
COPY contracts/generated ./contracts/generated
WORKDIR /app/frontend
ARG NEXT_PUBLIC_REKNYX_MODE=api
ARG REKNYX_BACKEND_ORIGIN=http://api:8000
ENV NEXT_PUBLIC_REKNYX_MODE=$NEXT_PUBLIC_REKNYX_MODE REKNYX_BACKEND_ORIGIN=$REKNYX_BACKEND_ORIGIN NEXT_TELEMETRY_DISABLED=1
RUN npm run build
FROM build AS runtime
ENV NODE_ENV=production
RUN chown -R node:node /app/frontend/.next
USER node
EXPOSE 3000
CMD ["node", "node_modules/next/dist/bin/next", "start", "--hostname", "0.0.0.0"]
