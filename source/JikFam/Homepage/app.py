from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # flash 메시지 사용 시 필요

# Handle static file requests from HTML
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('static', filename)

@app.route('/static/assets/<path:filename>')
def serve_static_assets(filename):
    return send_from_directory('static', filename)

# Page routes
@app.route('/')
@app.route('/index.html')
def home():
    return render_template('index.html')

@app.route('/about')
@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/services')
@app.route('/services.html')
def services():
    return render_template('services.html')

@app.route('/blog')
@app.route('/blog.html')
def blog():
    return render_template('blog.html')

@app.route('/testimonials')
@app.route('/testimonials.html')
def testimonials():
    return render_template('testimonials.html')


if __name__ == '__main__':
    app.run(debug=True)