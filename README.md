# 🎙️ Intercom — WebRTC Audio & Video Intercom System

**Intercom** lets you turn any computer with a **microphone**, **speakers**, and **webcam** into a remote intercom.  
You can **talk**, **listen**, and **watch** what’s happening — all through your browser using **WebRTC**.

---

## 🚀 Features

- 🔊 Two-way **audio communication**
- 🎥 Live **video streaming** via WebRTC
- 🔐 **Password-protected** single-user login
- ⚙️ Built with **Python**, **Quart**, and **aiortc**
- 🧩 Uses **Coturn** for TURN/STUN relay support
- 🖥️ Designed for simple deployment on Linux (Ubuntu/Debian)

> 🧑‍💻 Currently supports **1 user login** and **1 viewer** at a time.

---

## 🧠 Requirements

- Linux system (Ubuntu/Debian recommended)
- Microphone, speakers, and webcam connected
- Python 3.11+
- ALSA sound drivers
- OpenSSL
- Coturn (TURN server)

---

## ⚙️ Installation

Follow these steps to install and run **Intercom** on your Linux system.

### 1. Update your system
```bash
sudo apt update
```

### 2. Install Python
```bash
sudo apt install python3 python3-pip python3-venv
```

### 3. Install Coturn (TURN server)
```bash
sudo apt install coturn
```

### 4. Install dependencies
Make sure ALSA sound drivers, git, PortAudio, and OpenSSL are installed:
```bash
sudo apt install -y alsa-utils alsa-tools alsa-plugins git openssl libportaudio2 libportaudiocpp0 portaudio19-dev
```

### 5. Clone the repository
```bash
git clone https://github.com/zemendaniel/intercom.git
cd intercom
```

### 6. Set up the Python environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 7. Identify your audio and video devices
Find your playback (speaker) and recording (microphone) devices:
```bash
aplay -l     # list playback devices
arecord -l   # list recording devices
```

You’ll see something like:
```
card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]
```

List connected webcams:
```bash
ls /dev/video*
```

Usually `/dev/video0` is your main camera.

### 8. Create a self-signed certificate
You’ll need HTTPS for WebRTC to work. Run:
```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 36500
```
> Just press **Enter** for all questions. This creates `cert.pem` and `key.pem`.

### 9. Configure Coturn
Open the TURN server config:
```bash
sudo nano /etc/turnserver.conf
```

Paste this, replacing `<your lan ip>` with your actual LAN IP address:
```ini
# TURN server listening IP (your LAN IP)
listening-ip=<your lan ip>

# Relay IP usually same as listening IP
relay-ip=<your lan ip>

# Listening port (default 3478)
listening-port=3478

# Enable verbose logging to syslog
verbose

# Enable fingerprint attribute
fingerprint

# User authentication: username and password
# Replace with your own secure credentials
user=turnuser:turnpassword

# Enable long-term credentials mechanism (recommended)
lt-cred-mech
```

Restart Coturn and check that it’s running:
```bash
sudo systemctl restart coturn
sudo systemctl status coturn
```

### 10. Configure the Intercom app
Run the setup script to generate your `.env` file:
```bash
python3 setup-env.py
```

Follow the prompts and fill in your camera, mic, playback device, and TURN credentials.

You can adjust sound levels using:
```bash
alsamixer
```

### 11. Run the app as a system service
Create a new service file:
```bash
sudo nano /etc/systemd/system/intercom.service
```

Paste this configuration (adjust paths if needed):
```ini
[Unit]
Description=Intercom Webapp Service
After=network.target

[Service]
User=root
WorkingDirectory=/root/intercom
ExecStart=/root/intercom/venv/bin/python -m hypercorn app:app --bind 0.0.0.0:8080 --certfile cert.pem --keyfile key.pem --workers 1
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Reload systemd, start the service, and enable it on boot:
```bash
sudo systemctl daemon-reload
sudo systemctl start intercom
sudo systemctl enable intercom
sudo systemctl status intercom
```

### 12. Access the app
Open your browser and navigate to:
```
https://<your-ip>:8080
```

Log in with your configured password.  
Then:
- Click **Start** to begin the video/audio stream.
- Click **Stop** to end it.
- Ensure your browser has permission to use the **microphone**.

That’s it — your **Intercom** is now live!

---

## 🐞 Bugs / Feedback

If you find a bug or want to suggest improvements:
- 🪲 [Open an issue](https://github.com/zemendaniel/intercom/issues)
- ⭐ **Star the repo** to support the project!

---

## 📜 License


This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.  