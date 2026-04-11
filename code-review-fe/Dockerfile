# ===== BUILD STAGE =====
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# disable telemetry + tăng memory
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_OPTIONS="--max-old-space-size=2048"

RUN npm run build

# ===== RUN STAGE =====
FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=production

# chỉ copy phần cần thiết (QUAN TRỌNG)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]