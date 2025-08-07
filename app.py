import os
from werkzeug.security import check_password_hash
from audio import MediaCapture
from quart import Quart, request, jsonify, render_template, session, redirect, url_for
from auth import is_logged_in
from dotenv import load_dotenv


load_dotenv()

ROOT = os.path.dirname(__file__)
app = Quart(__name__)
app.secret_key = os.getenv('SECRET_KEY')
media = MediaCapture('/dev/video0', 'usb audio device', 'usb')


@app.route("/")
@is_logged_in
async def index():
    return await render_template("index.html")


@app.post("/offer")
@is_logged_in
async def offer():
    params = await request.get_json()
    sdp, typ = await media.handle_offer(params)

    return jsonify({"sdp": sdp, "type": typ})


@app.post("/stop")
@is_logged_in
async def stop():
    await media.shutdown()
    return '', 200


@app.route('/login', methods=['GET', 'POST'])
async def login():
    if session.get('logged_in') is not None:
        return redirect(url_for('index'))

    if request.method == 'POST':
        form = await request.form
        pwd = form.get('pwd')
        if check_password_hash(os.getenv('PASSWORD'), pwd):
            session['logged_in'] = True
            session.permanent = True
            return redirect(url_for('index'))

    return await render_template('login.html')


@app.post("/logout")
async def logout():
    session.clear()
    return redirect(url_for("login"))


@app.after_serving
async def after_serving():
    await media.shutdown()
    print("Server shutdown complete")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
