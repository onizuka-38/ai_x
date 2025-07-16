from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # flash 메시지 사용 시 필요

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/blog-details')
def blog_details():
    return render_template('blog-details.html')

@app.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not name or not email or not subject or not message:
            flash('모든 필드를 입력해주세요.', 'error')
        else:
            # 여기서 실제 이메일 전송 또는 DB 저장 로직 가능
            flash('문의가 성공적으로 전송되었습니다. 감사합니다!', 'success')
            return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/newsletter', methods=['POST'])
def newsletter():
    email = request.form.get('email')
    if not email:
        flash('이메일을 입력해주세요.', 'error')
    else:
        # 여기에 이메일 처리 로직 (예: DB 저장 또는 알림 전송)
        flash('구독 신청이 완료되었습니다!', 'success')
    return redirect(url_for('home'))
