FROM python:3.11.8-slim-bullseye

WORKDIR /opt/vaultbackup
COPY main.py .
COPY requirements.txt .
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "-u"]
CMD ["main.py"]