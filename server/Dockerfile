
FROM python:3.10

RUN apt update -y && apt upgrade -y && apt -y install python3-pip vim supervisor less \
	&& apt clean
RUN pip3 install flask gunicorn
RUN pip3 install gspread oauth2client Pillow PyDrive2


ENV APP_HOME /app 
WORKDIR $APP_HOME
COPY . ./

CMD exec gunicorn --bind :8080 --workers 1 app:app

# docker build -t gcr.io/vrchat-analyzer/photoframe .
# docker run --rm -it -p 8080:8080 -v c:/obara/vrchat_photoframe/server:/app gcr.io/vrchat-analyzer/photoframe /bin/bash
# docker image push gcr.io/vrchat-analyzer/photoframe
