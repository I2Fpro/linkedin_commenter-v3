FROM nginx:alpine

# Installer curl pour le healthcheck
RUN apk add --no-cache curl

# Copier les fichiers HTML du site
COPY *.html /usr/share/nginx/html/
COPY account/ /usr/share/nginx/html/account/
COPY admin/ /usr/share/nginx/html/admin/

# Copier la configuration Nginx personnalisée
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Exposer le port 80
EXPOSE 80

# Démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]
