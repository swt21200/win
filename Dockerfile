FROM python:3.9-slim

# Linux ရဲ့ လိုအပ်တဲ့ library တွေ အကုန်သွင်းပေးခြင်း
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# Bot က သုံးထားတဲ့ port ကို ဖွင့်ပေးခြင်း
EXPOSE 8099
ENV BOT_PORT=8099

CMD ["python", "main.py"]
