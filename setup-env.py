import secrets
from werkzeug.security import generate_password_hash

password = input("Password:\n")
secret_key = secrets.token_hex(32)
cam_url = input("Enter cam url (eg. /dev/video0):\n")
mic_name = input("Enter mic name (eg. usb audio device):\n")
playback_name = input("Enter playback device name (eg. usb):\n")
turn_url = input("Enter turn url (eg. 192.168.1.50:3478):\n")
turn_user = input("Enter turn username (eg. turnuser):\n")
turn_password = input("Enter turn password (eg. turnpassword):\n")

with open(".env", "w", encoding="utf-8") as f:
    f.write(f"""
SECRET_KEY={secret_key}
PASSWORD={generate_password_hash(password)}
CAM_URL={cam_url}
MIC_NAME={mic_name}
PLAYBACK_NAME={playback_name}
TURN_URL={turn_url}
TURN_USER={turn_user}
TURN_PASSWORD={turn_password}
""")
