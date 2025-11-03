import os
from werkzeug.security import check_password_hash
from audio import MediaCapture
from quart import Quart, request, jsonify, render_template, session, redirect, url_for, Response
from auth import is_logged_in
from dotenv import load_dotenv


load_dotenv()

app = Quart(__name__)
app.secret_key = os.getenv('SECRET_KEY')
media = MediaCapture(os.getenv("CAM_URL"), os.getenv("MIC_NAME"), os.getenv("PLAYBACK_NAME"))


@app.route("/")
@is_logged_in
async def index():
    return await render_template("index.html", is_running=media.is_running)


@app.route("/js/client.js")
async def client_js():
    js_content = await render_template(
        "client.js",
        turn_url=os.getenv("TURN_URL"),
        turn_user=os.getenv("TURN_USER"),
        turn_password=os.getenv("TURN_PASSWORD"),
    )
    return Response(js_content, mimetype="application/javascript")


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
