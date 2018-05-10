FROM python:3-alpine3.7

LABEL maintainer="sile16"

ENV VERSION "v2.2.10"
ENV FOLDER "swagger-ui-2.2.10"
ENV API_URL "http://petstore.swagger.io/v2/swagger.json"
ENV API_URLS ""
ENV API_KEY "**None**"
ENV OAUTH_CLIENT_ID "**None**"
ENV OAUTH_CLIENT_SECRET "**None**"
ENV OAUTH_REALM "**None**"
ENV OAUTH_APP_NAME "**None**"
ENV OAUTH_ADDITIONAL_PARAMS "**None**"
ENV SWAGGER_JSON "/app/swagger.json"
ENV PORT 80
ENV BASE_URL ""

RUN apk update --no-cache && apk upgrade --no-cache && apk add --update --no-cache \
    git \
    nginx

RUN mkdir -p /run/nginx


#Get latest swagger-ui
RUN mkdir -p /usr/share/nginx/html
RUN git clone https://github.com/swagger-api/swagger-ui.git /swagger-ui && \
     mv /swagger-ui/dist/* /usr/share/nginx/html/    && \
     mv /swagger-ui/docker-run.sh /usr/share/nginx && \
     rm -rf /swagger-ui



RUN apk add --no-cache --update build-base && \
    pip install --no-cache-dir pdfminer.six && \
    apk del build-base

ADD rest_extract/requirements.txt /usr/share/nginx/
RUN pip install --no-cache-dir -r /usr/share/nginx/requirements.txt
ADD rest_extract /usr/share/nginx/


#this should overwrite the index.html provided in the cloned swagger-ui from master.
COPY nginx.conf /etc/nginx/
COPY html/index.html /usr/share/nginx/html/
COPY docker-run.sh /usr/share/nginx/

EXPOSE 80

CMD ["sh", "/usr/share/nginx/docker-run.sh"]

