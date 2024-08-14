
FROM python:3.11-slim

RUN apt update -y && apt upgrade -y && apt -y install python3-pip vim supervisor less \
	&& apt clean
RUN pip3 install flask gunicorn pydantic pydantic-settings
RUN pip3 install gspread oauth2client Pillow PyDrive2
RUN pip3 install boto3
#RUN pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

ENV APP_HOME /app 
WORKDIR $APP_HOME
COPY . ./

CMD exec gunicorn --bind :8080 --workers 1 app:app

# docker build -t vrchat-sync-frame .
# docker run --rm -it -p 8080:8080 -v c/obara/vrchat-photo-frame/server:/app vrchat-sync-frame /bin/bash
# docker run --rm -p 8080:8080 --env-file .env vrchat-sync-frame
# docker tag vrchat-sync-frame asia-northeast1-docker.pkg.dev/vrchat-photo-frame/server/sync-frame
# docker image push asia-northeast1-docker.pkg.dev/vrchat-photo-frame/server/sync-frame
