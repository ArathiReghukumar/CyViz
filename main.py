from typing import *
from concurrent.futures import ProcessPoolExecutor, Future

from utils import *
from pymongo import MongoClient
from flask import Flask, jsonify, url_for, redirect, request

import view1
import view2


app = Flask(__name__, static_folder='static', static_url_path='/')
app.register_blueprint(view1.page)
app.register_blueprint(view2.page)


@app.route('/')
def home():
    return redirect(url_for('static', filename='home.html'))





if __name__ == '__main__':
    app.run(debug=True)
