import secrets
from werkzeug.security import generate_password_hash

password = input("Password:\n")
secret_key = secrets.token_hex(32)

with open(".env", "w", encoding="utf-8") as f:
    f.write(f"""
SECRET_KEY={secret_key}
PASSWORD={generate_password_hash(password)}
""")
