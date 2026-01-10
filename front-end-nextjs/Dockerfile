FROM node:18-alpine as build
WORKDIR /app
ADD *json .
RUN npm ci
ADD . .
RUN npm run build

FROM node:18-alpine as runner
WORKDIR /app
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["npm", "start"]
