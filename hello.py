#!/usr/bin/env python3
from flask import Flask, request, g, render_template, render_template_string, Response
from flask_mail import Mail, Message

import sqlite3
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'una-cualquiera-fruta-fruta'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'faradaysec2@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ['GMAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
DATABASE = './database.db'

acc_tmpl = '''
Se reporto un evento en SERVIDOR:
{{ mensaje }}
'''

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.isolation_level = None
        #db.row_factory = sqlite3.Row
        #db.text_factory = lambda x: str(x).replace('"', '&quot;').replace("'", '&#x27;').replace('<', '&lt;').replace('>', '&gt;')
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
           db.cursor().executescript(f.read())
        db.commit()

if not os.path.exists(DATABASE):
    init_db()

def query_db(query, args=(), one=False):
    with app.app_context():
        cur = get_db().execute(query, args)
        rv = [dict((cur.description[idx][0], str(value)) \
                for idx, value in enumerate(row)) for row in cur.fetchall()]
        return (rv[0] if rv else None) if one else rv

@app.route('/sendMessage', methods=['POST'])
def sendMessage():
    if request.method == 'POST':
        msg = Message(request.form['subject'], sender = 'faradaysec@gmail.com', recipients = [request.form['dest']])
        msg.body = render_template_string(acc_tmpl.replace('SERVIDOR', query_db('SELECT nombre FROM usuarios ORDER BY usuario_id DESC', one=True)['nombre']), mensaje=request.form['body'])
        mail.send(msg)

        return render_template('enviado.html', dest=request.form['dest'])

@app.route('/profile')
def profile():
    name = request.args.get('name', '')
    if name:
        query_db('INSERT INTO usuarios (nombre) VALUES ("%s")' % name)

        return render_template('sender.html')
    return render_template('error.html')

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/dump')
def dump():
    return Response(open(__file__).read(), mimetype='text/plain')

@app.route('/error')
def error_route():
    1/0


if __name__ == "__main__":
    port = int(os.getenv('PORT') or 5000)
    app.run(host='0.0.0.0', port=port, debug=True)
