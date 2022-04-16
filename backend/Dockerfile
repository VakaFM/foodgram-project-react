FROM python:3.8.6-slim
WORKDIR /app
COPY ./requirements.txt .
RUN pip install -r requirements.txt
COPY . ./
RUN chmod +x init.sh
CMD /app/init.sh