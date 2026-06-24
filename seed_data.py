import os
from datetime import datetime, timedelta, timezone
from app import db, Order, app


with app.app_context():
    print("🚀 Начинаю генерацию тестовых заказов...")


    test_orders = [
        {
            "name": "Анна Смирнова",
            "email": "anna@test.com",
            "phone": "+79991112233",
            "vk_profile": "vk.com/id10001",
            "description": "Нужно смонтировать ролик для ТикТока, 3 минуты.",
            "video_link": "https://drive.google.com/file/d/1A1A1A1A1A1"
        },
        {
            "name": "Дмитрий Петров",
            "email": "dmitry@test.com",
            "phone": "+79994445566",
            "vk_profile": "durov",
            "description": "Свадебный монтаж, 4 часа материала. Срочность высокая!",
            "video_link": "https://disk.yandex.ru/i/B2B2B2B2B2"
        },
        {
            "name": "Елена Козлова",
            "email": "elena@test.com",
            "phone": "",
            "vk_profile": "",
            "description": "Рекламный ролик для бизнеса, нужны титры.",
            "video_link": "https://cloud.mail.ru/public/C3C3C3C3"
        },
        {
            "name": "Игорь Волков",
            "email": "igor@test.com",
            "phone": "+79997778899",
            "vk_profile": "vk.com/club_studio",
            "description": "Репортаж с мероприятия, вырезать лишнее.",
            "video_link": "https://drive.google.com/file/d/4D4D4D4D4D"
        },
        {
            "name": "Ольга Федорова",
            "email": "olga@test.com",
            "phone": "+79001234567",
            "vk_profile": "id999888",
            "description": "Монтаж влогов за неделю, склейка дублей.",
            "video_link": "https://disk.yandex.ru/i/E5E5E5E5"
        }
    ]

    for i, data in enumerate(test_orders):
        status = 'new'
        if i == 1: status = 'in_progress'
        if i == 2: status = 'done'

        created_time = datetime.now(timezone.utc) - timedelta(hours=i * 2)

        order = Order(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            vk_profile=data['vk_profile'],
            description=data['description'],
            video_link=data['video_link'],
            status=status,
            created_at=created_time
        )
        db.session.add(order)
        print(f"✅ Добавлен заказ #{order.id} ({data['name']}) - Статус: {status}")

    try:
        db.session.commit()
        print("\n🎉 Готово! Все тестовые заказы сохранены в orders.db")
        print("👉 Теперь запускай админку: http://127.0.0.1:5000/admin?token=ТВОЙ_ТОКЕН")
    except Exception as e:
        db.session.rollback()
        print("❌ Ошибка при сохранении:", e)
