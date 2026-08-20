FROM python:3.13-alpine
COPY check.py /check.py
CMD ["python", "-u", "/check.py"]
