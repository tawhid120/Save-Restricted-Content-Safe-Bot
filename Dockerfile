FROM python:3.10-slim-bullseye


# ধাপ ২: সব সিস্টেম প্যাকেজ একটি RUN লেয়ারে ইনস্টল করুন
RUN apt-get update && apt-get install -y \
    git \
    curl \
    python3-pip \
    ffmpeg \
    wget \
    bash \
    neofetch \
    software-properties-common \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ধাপ ৩: পাইথন প্যাকেজ ইনস্টল করুন
RUN pip3 install wheel
COPY requirements.txt .
# ধাপ ৩: পাইথন প্যাকেজ ইনস্টল করুন (সঠিকভাবে)
RUN pip3 install wheel
COPY requirements.txt .

# প্রথমে pyrofork এবং pyromod ছাড়া বাকি সব ইনস্টল করুন
RUN pip3 install --no-cache-dir -U $(grep -vE '^(pyromod|pyrofork)$' requirements.txt)

# এখন pyrofork ইনস্টল করুন (যা pyrogram-কে রিপ্লেস করবে)
RUN pip3 install --no-cache-dir -U pyrofork

# সবশেষে, pyromod ইনস্টল করুন, কিন্তু তার dependency (পুরনো pyrogram) ইনস্টল করা থেকে বিরত রাখুন
RUN pip3 install --no-cache-dir -U --no-deps pyromod

# ধাপ ৪: আপনার অ্যাপ কোড কপি করুন
WORKDIR /app
COPY . .

# ধাপ ৫: Flask অ্যাপের প্রধান ফাইল সেট করুন (প্রয়োজনে পরিবর্তন করুন)
ENV FLASK_APP=app.py

# ধাপ ৬: আপনার দুটি কমান্ড একসাথে চালান (Render-এর জন্য)
CMD python3 -m safe_repo & flask run --host=0.0.0.0 --port=$PORT
