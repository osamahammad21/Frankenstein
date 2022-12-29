FROM python:3.7-slim

ENV PYTHONDONTWRITEBYTECODE=1

RUN pip3 install Kubernetes
COPY shuffler.py .


CMD ["python3", "-u", "./shuffler.py"]
