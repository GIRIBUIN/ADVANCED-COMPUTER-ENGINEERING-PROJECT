from flask import Flask, render_template, jsonify


def create_app():
    ''' Flask 애플리케이션을 생성하는 함수 '''
    app = Flask(__name__)

    @app.route('/')
    def index():
        # templates 폴더에 있는 hello.html
        return render_template('hello.html')

    return app