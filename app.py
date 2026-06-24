import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'orders.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')

# --- КОНФИГУРАЦИЯ ПОЧТЫ ---
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.yandex.ru')
MAIL_PORT = int(os.getenv('MAIL_PORT', 465))


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    vk_profile = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=False)
    video_link = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(50), default='new')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Order {self.id}>'


with app.app_context():
    db.create_all()


def send_email_notification(to_email, name, new_status, order_id):
    """Функция отправки письма клиенту"""
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("❌ Ошибка: Не настроены переменные MAIL_USERNAME или MAIL_PASSWORD в .env")
        return False

    # Формируем тему письма в зависимости от статуса
    subject_map = {
        'new': 'Ваш заказ принят в работу!',
        'in_progress': 'Статус вашего заказа изменен: В работе',
        'done': 'Готово! Ваш заказ #{} выполнен! 🎉'.format(order_id)
    }
    subject = subject_map.get(new_status, f'Статус заказа #{order_id} изменен')

    # Тело письма (HTML для красоты)
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2>Студия видеомонтажа</h2>
            <p>Здравствуйте, <b>{name}</b>!</p>

            <p>Статус вашего заказа <b>#</b><b style="color: #764ba2;">{order_id}</b> был изменен.</p>

            <div style="background-color: #f0f4ff; padding: 15px; border-left: 5px solid #764ba2; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #4f46e5;">Новый статус: {new_status.replace('_', ' ').title()}</h3>
                <p>Мы уже работаем над вашим видео!</p>
            </div>

            <p>Если у вас возникнут вопросы, вы можете:</p>
            <ul>
                <li>Написать нам в <a href="https://vk.com/твоя_группа_vk">VK</a></li>
                <li>Позвонить по телефону: +7 (XXX) XXX-XX-XX</li>
            </ul>

            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            <small style="color: #888;">Это автоматическое сообщение. Пожалуйста, не отвечайте на него напрямую.</small>
        </body>
    </html>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = MAIL_USERNAME
    msg['To'] = to_email

    part = MIMEText(html_content, 'html')
    msg.attach(part)

    try:
        # Используем SSL соединение
        server = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT)
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(MAIL_USERNAME, to_email, msg.as_string())
        server.quit()
        print(f"✅ Письмо успешно отправлено на {to_email} (статус: {new_status})")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки письма: {e}")
        flash(f'Заказ обновлен, но письмо не удалось отправить: {str(e)}', 'warning')
        return False


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        vk_profile = request.form.get('vk_profile', '').strip()
        description = request.form.get('description', '').strip()
        video_link = request.form.get('video_link', '').strip()

        if not video_link:
            flash('Пожалуйста, вставьте ссылку на видео с диска.', 'error')
            return redirect(request.url)

        if 'http' not in video_link and 'www' not in video_link:
            flash('Ссылка выглядит некорректно.', 'error')
            return redirect(request.url)

        new_order = Order(
            name=name, email=email, phone=phone, vk_profile=vk_profile,
            description=description, video_link=video_link, status='new'
        )
        db.session.add(new_order)
        db.session.commit()

        # Отправляем приветственное письмо сразу после создания заказа
        send_email_notification(email, name, 'new', new_order.id)

        flash('Ваш заказ успешно отправлен! Мы свяжемся с вами.', 'success')
        return redirect(url_for('index'))

    return render_template('index.html')


def check_admin_token():
    if not ADMIN_TOKEN:
        return False
    token = request.args.get('token')
    return token == ADMIN_TOKEN


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not check_admin_token():
        if request.method == 'GET':
            return render_template_string('''
            <!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><title>Доступ запрещен</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>body{background:#f1f3f5;} .card{margin-top:50px;}</style></head>
            <body><div class="container"><div class="card p-5 text-center">
            <h1 class="display-1 text-danger">���<h2 class="fw-bold">Доступ запрещен</h2>
            <p class="lead">Для доступа к админ-панели добавьте секретный токен к ссылке.</p>
            <a href="/" class="btn btn-primary mt-3">Вернуться на сайт</a></div></div></body></html>
            ''')
        else:
            return redirect(url_for('admin'))

    if request.method == 'POST':
        order_id = request.form.get('order_id')
        new_status = request.form.get('status')

        if order_id and new_status:
            order = Order.query.get(order_id)
            if order:
                old_status = order.status
                order.status = new_status
                db.session.commit()

                # ГЛАВНОЕ: Отправляем уведомление ТОЛЬКО если статус реально изменился
                if old_status != new_status:
                    send_email_notification(order.email, order.name, new_status, order.id)
                    flash(f'Статус заказа #{order_id} изменен на "{new_status}" и клиенту отправлено письмо!',
                          'success')
                else:
                    flash(f'Статус заказа #{order_id} уже был "{new_status}".', 'info')
            else:
                flash('Заказ не найден', 'error')

        current_token = request.args.get('token', '')
        return redirect(url_for('admin', token=current_token))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin.html', orders=orders)


if __name__ == '__main__':
    app.run(debug=True)
