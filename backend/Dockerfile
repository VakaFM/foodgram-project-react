FROM python:3.8.6-slim
WORKDIR /app
COPY requirements.txt .
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip3 install -r requirements.txt --no-cache-dir
RUN python manage.py makemigrations
RUN chmod +x init.sh
CMD /app/init.sh