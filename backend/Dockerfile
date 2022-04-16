FROM python:3.8.6-slim
WORKDIR /app
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . ./
RUN chmod +x init.sh
CMD /app/init.sh