FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN pip uninstall -y opencv-python opencv-python-headless && \
    pip install --no-cache-dir --force-reinstall "opencv-python-headless==4.10.0.84" "numpy<2.4.0"

COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]