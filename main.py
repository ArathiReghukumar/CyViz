from typing import *
from concurrent.futures import ProcessPoolExecutor, Future

from utils import *
from pymongo import MongoClient
from flask import Flask, jsonify, url_for, redirect, request

import view1
import view2
import view3
import view4
import view5
import view6
import view7
import view8
import view9
import view10
import view11

import socket

app = Flask(__name__, static_folder='static', static_url_path='/')
app.register_blueprint(view1.page)
app.register_blueprint(view2.page)
app.register_blueprint(view3.page)
app.register_blueprint(view4.page)
app.register_blueprint(view5.page)
app.register_blueprint(view6.page)
app.register_blueprint(view7.page)
app.register_blueprint(view8.page)
app.register_blueprint(view9.page)
app.register_blueprint(view10.page)
app.register_blueprint(view11.page)


@app.route('/')
def home():
    return redirect(url_for('static', filename='home.html'))



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
