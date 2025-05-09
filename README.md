# FPIS-Backend
FPIS-Backend Django


📦 Установка зависимостей из requirements.txt

Чтобы установить все необходимые библиотеки, указанные в файле requirements.txt, выполните следующие шаги:

✅ 1. Клонируйте проект (если необходимо)

```bash
git clone https://github.com/Yermakhan05/FPIS-Backend.git
cd backend
```

✅ 2. Создайте и активируйте виртуальное окружение

🔹 На Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

🔹 На macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

✅ 3. Установите все зависимости

```bash
pip install -r requirements.txt
```

✅ 3. Run project:
```bash
daphne -b 0.0.0.0 -p 8000 backend.asgi:application
```