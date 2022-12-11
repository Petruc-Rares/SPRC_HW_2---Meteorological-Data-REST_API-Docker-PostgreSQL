FROM python:3.6
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
COPY . .
WORKDIR /src
ENV FLASK_ENV="docker"
ENV PYTHONDONTWRITEBYTECODE 1
EXPOSE 81
CMD ["flask", "run", "--host=0.0.0.0", "--port=81"]