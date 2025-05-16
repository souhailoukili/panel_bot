from flask import Flask, render_template_string, request, redirect, session, url_for
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecretkey123')  # Use environment variable for security

# Firebase setup
cred = credentials.Certificate("bot-souhail-firebase-adminsdk-fbsvc-5634524741.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# HTML Templates
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GhostShield - لوحة التحكم</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 0; padding: 20px; }
        .navbar { background-color: #007bff; padding: 10px; border-radius: 5px; }
        .navbar a { color: white; margin: 0 15px; text-decoration: none; font-weight: bold; }
        .navbar a:hover { color: #ddd; }
        .container { max-width: 1000px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #007bff; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #007bff; color: white; }
        .btn { padding: 8px 15px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background-color: #0056b3; }
        .btn-danger { background-color: #dc3545; }
        .btn-danger:hover { background-color: #c82333; }
        form { margin-top: 20px; }
        input[type="text"] { padding: 8px; width: 200px; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/">🏠 الرئيسية</a>
        <a href="/blacklist">🚫 القائمة السوداء</a>
        <a href="/groups">👥 إدارة المجموعات</a>
        <a href="/settings">⚙️ الإعدادات</a>
        <a href="/logout">🔓 تسجيل الخروج</a>
    </div>
    <div class="container">
        <h1>🛡️ GhostShield - لوحة تحكم البوت</h1>
        <p>✅ تم التحقق من: {{ verified|length }} مستخدم</p>
        <p>🚫 عدد المخالفات: {{ violations }}</p>
        <form action="/clear" method="POST">
            <button type="submit" class="btn btn-danger">🗑️ حذف جميع سجلات التحقق</button>
        </form>
        <h2>📋 المستخدمون الذين تم التحقق منهم:</h2>
        <table>
            <tr>
                <th>🆔 ID</th>
                <th>👤 الاسم</th>
                <th>🔗 اسم المستخدم</th>
                <th>📅 وقت التحقق</th>
                <th>🗑️ حذف</th>
            </tr>
            {% for user in verified %}
            <tr>
                <td>{{ user.user_id }}</td>
                <td>{{ user.first_name }}</td>
                <td>{{ user.username }}</td>
                <td>{{ user.verified_at }}</td>
                <td>
                    <form action="/delete/{{ user.doc_id }}" method="POST">
                        <button type="submit" class="btn btn-danger">🗑️</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

HTML_BLACKLIST = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>القائمة السوداء</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 0; padding: 20px; }
        .navbar { background-color: #007bff; padding: 10px; border-radius: 5px; }
        .navbar a { color: white; margin: 0 15px; text-decoration: none; font-weight: bold; }
        .navbar a:hover { color: #ddd; }
        .container { max-width: 1000px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #007bff; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #007bff; color: white; }
        .btn { padding: 8px 15px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background-color: #0056b3; }
        .btn-danger { background-color: #dc3545; }
        .btn-danger:hover { background-color: #c82333; }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/">🏠 الرئيسية</a>
        <a href="/blacklist">🚫 القائمة السوداء</a>
        <a href="/groups">👥 إدارة المجموعات</a>
        <a href="/settings">⚙️ الإعدادات</a>
        <a href="/logout">🔓 تسجيل الخروج</a>
    </div>
    <div class="container">
        <h1>🚫 القائمة السوداء</h1>
        <table>
            <tr>
                <th>🆔 ID</th>
                <th>🕒 وقت الإضافة</th>
                <th>🗑️ حذف</th>
            </tr>
            {% for user in blacklist %}
            <tr>
                <td>{{ user.user_id }}</td>
                <td>{{ user.added_at }}</td>
                <td>
                    <form action="/blacklist/delete/{{ user.doc_id }}" method="POST">
                        <button type="submit" class="btn btn-danger">🗑️</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

HTML_GROUPS = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة المجموعات</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 0; padding: 20px; }
        .navbar { background-color: #007bff; padding: 10px; border-radius: 5px; }
        .navbar a { color: white; margin: 0 15px; text-decoration: none; font-weight: bold; }
        .navbar a:hover { color: #ddd; }
        .container { max-width: 1000px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #007bff; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #007bff; color: white; }
        .btn { padding: 8px 15px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background-color: #0056b3; }
        .btn-danger { background-color: #dc3545; }
        .btn-danger:hover { background-color: #c82333; }
        form { margin-top: 20px; }
        input[type="text"] { padding: 8px; width: 200px; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/">🏠 الرئيسية</a>
        <a href="/blacklist">🚫 القائمة السوداء</a>
        <a href="/groups">👥 إدارة المجموعات</a>
        <a href="/settings">⚙️ الإعدادات</a>
        <a href="/logout">🔓 تسجيل الخروج</a>
    </div>
    <div class="container">
        <h1>👥 إدارة المجموعات</h1>
        <form action="/groups/add" method="POST">
            <input type="text" name="chat_id" placeholder="أدخل معرف المجموعة (مثل -1001234567890)" required>
            <button type="submit" class="btn">➕ إضافة مجموعة</button>
        </form>
        <h2>📋 المجموعات المسموح بها:</h2>
        <table>
            <tr>
                <th>🆔 معرف المجموعة</th>
                <th>🗑️ حذف</th>
            </tr>
            {% for group in groups %}
            <tr>
                <td>{{ group.chat_id }}</td>
                <td>
                    <form action="/groups/delete/{{ group.chat_id }}" method="POST">
                        <button type="submit" class="btn btn-danger">🗑️</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

HTML_USER_DETAILS = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>معلومات المستخدم</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 0; padding: 20px; }
        .navbar { background-color: #007bff; padding: 10px; border-radius: 5px; }
        .navbar a { color: white; margin: 0 15px; text-decoration: none; font-weight: bold; }
        .navbar a:hover { color: #ddd; }
        .container { max-width: 1000px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #007bff; }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/">🏠 الرئيسية</a>
        <a href="/blacklist">🚫 القائمة السوداء</a>
        <a href="/groups">👥 إدارة المجموعات</a>
        <a href="/settings">⚙️ الإعدادات</a>
        <a href="/logout">🔓 تسجيل الخروج</a>
    </div>
    <div class="container">
        <h1>👤 معلومات المستخدم</h1>
        <p><strong>الاسم:</strong> {{ user.first_name or '-' }}</p>
        <p><strong>اسم المستخدم:</strong> {{ user.username or '-' }}</p>
        <p><strong>المعرف:</strong> {{ user.user_id }}</p>
        <p><strong>عدد المخالفات:</strong> {{ violations }}</p>
        <p><strong>في البلاك ليست؟</strong> {{ in_blacklist }}</p>
    </div>
</body>
</html>
"""

HTML_SETTINGS = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إعدادات النظام</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 0; padding: 20px; }
        .navbar { background-color: #007bff; padding: 10px; border-radius: 5px; }
        .navbar a { color: white; margin: 0 15px; text-decoration: none; font-weight: bold; }
        .navbar a:hover { color: #ddd; }
        .container { max-width: 1000px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #007bff; }
        form { margin-top: 20px; }
        label { display: block; margin: 10px 0; }
        input[type="checkbox"] { margin-right: 10px; }
        .btn { padding: 8px 15px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/">🏠 الرئيسية</a>
        <a href="/blacklist">🚫 القائمة السوداء</a>
        <a href="/groups">👥 إدارة المجموعات</a>
        <a href="/settings">⚙️ الإعدادات</a>
        <a href="/logout">🔓 تسجيل الخروج</a>
    </div>
    <div class="container">
        <h1>⚙️ إعدادات النظام</h1>
        <form action="/settings" method="POST">
            <label><input type="checkbox" name="night_mode" {% if settings.night_mode %}checked{% endif %}> الوضع الليلي</label>
            <label><input type="checkbox" name="block_media" {% if settings.block_media %}checked{% endif %}> منع الوسائط</label>
            <label><input type="checkbox" name="kick_links" {% if settings.kick_links %}checked{% endif %}> الطرد عند الروابط</label>
            <label><input type="checkbox" name="verify_new_users" {% if settings.verify_new_users %}checked{% endif %}> التحقق من الأعضاء الجدد</label>
            <button type="submit" class="btn">💾 حفظ</button>
        </form>
    </div>
</body>
</html>
"""

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 400px; margin: 50px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #007bff; text-align: center; }
        form { display: flex; flex-direction: column; }
        input[type="text"], input[type="password"] { padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        .btn { padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background-color: #0056b3; }
        .error { color: #dc3545; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 تسجيل الدخول</h1>
        <form action="/login" method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit" class="btn">دخول</button>
        </form>
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

# Routes
@app.route('/')
def home():
    if 'logged_in' not in session:
        return redirect('/login')
    verified_docs = db.collection("verified_users").order_by("verified_at", direction=firestore.Query.DESCENDING).limit(20).stream()
    verified_list = []
    for doc in verified_docs:
        data = doc.to_dict()
        verified_list.append({
            "doc_id": doc.id,
            "user_id": data.get("user_id"),
            "first_name": data.get("first_name", ""),
            "username": data.get("username", "") or "-",
            "verified_at": data.get("verified_at")
        })

    violations_count = len(list(db.collection("violations").stream()))
    return render_template_string(HTML_TEMPLATE, verified=verified_list, violations=violations_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'souhail_boss' and password == 'boss_souhail':
            session['logged_in'] = True
            return redirect('/')
        return render_template_string(HTML_LOGIN, error='❌ اسم المستخدم أو كلمة المرور خاطئة')
    return render_template_string(HTML_LOGIN)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

@app.route('/clear', methods=['POST'])
def clear_verified():
    try:
        docs = db.collection("verified_users").stream()
        for doc in docs:
            doc.reference.delete()
        return redirect('/')
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

@app.route('/delete/<doc_id>', methods=['POST'])
def delete_verified_user(doc_id):
    try:
        db.collection("verified_users").document(doc_id).delete()
        return redirect('/')
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

@app.route('/blacklist')
def show_blacklist():
    if 'logged_in' not in session:
        return redirect('/login')
    docs = db.collection("blacklist").order_by("added_at", direction=firestore.Query.DESCENDING).stream()
    blacklist = []
    for doc in docs:
        data = doc.to_dict()
        blacklist.append({
            "doc_id": doc.id,
            "user_id": data.get("user_id"),
            "added_at": data.get("added_at").strftime("%Y-%m-%d %H:%M:%S") if data.get("added_at") else "-"
        })
    return render_template_string(HTML_BLACKLIST, blacklist=blacklist)

@app.route('/blacklist/delete/<doc_id>', methods=['POST'])
def delete_blacklisted_user(doc_id):
    try:
        db.collection("blacklist").document(doc_id).delete()
        return redirect('/blacklist')
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

@app.route('/groups', methods=['GET'])
def show_groups():
    if 'logged_in' not in session:
        return redirect('/login')
    docs = db.collection("allowed_chats").stream()
    groups = []
    for doc in docs:
        data = doc.to_dict()
        groups.append({
            "chat_id": doc.id,
            "added_at": data.get("added_at").strftime("%Y-%m-%d %H:%M:%S") if data.get("added_at") else "-"
        })
    return render_template_string(HTML_GROUPS, groups=groups)

@app.route('/groups/add', methods=['POST'])
def add_group():
    if 'logged_in' not in session:
        return redirect('/login')
    chat_id = request.form.get('chat_id')
    try:
        chat_id = int(chat_id)  # التأكد من أن المدخل رقم
        db.collection("allowed_chats").document(str(chat_id)).set({
            "chat_id": chat_id,
            "added_at": firestore.SERVER_TIMESTAMP
        })
        return redirect('/groups')
    except ValueError:
        return render_template_string(HTML_GROUPS, groups=[], error="❌ معرف المجموعة يجب أن يكون رقمًا")
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

@app.route('/groups/delete/<chat_id>', methods=['POST'])
def delete_group(chat_id):
    if 'logged_in' not in session:
        return redirect('/login')
    try:
        db.collection("allowed_chats").document(chat_id).delete()
        return redirect('/groups')
    except Exception as e:
        return f"❌ خطأ: {str(e)}"

@app.route('/user/<user_id>')
def user_details(user_id):
    if 'logged_in' not in session:
        return redirect('/login')
    violations = db.collection("violations").where("user_id", "==", int(user_id)).stream()
    v_count = len(list(violations))
    verified_query = db.collection("verified_users").where("user_id", "==", int(user_id)).limit(1).stream()
    user_data = next(verified_query, None)
    if user_data:
        user_dict = user_data.to_dict()
    else:
        user_dict = {"first_name": "-", "username": "-", "user_id": user_id}
    # Check blacklist
    bl_query = db.collection("blacklist").where("user_id", "==", int(user_id)).limit(1).stream()
    in_blacklist = "✅" if next(bl_query, None) else "❌"
    return render_template_string(HTML_USER_DETAILS, user=user_dict, violations=v_count, in_blacklist=in_blacklist)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'logged_in' not in session:
        return redirect('/login')
    doc_ref = db.collection("settings").document("main")
    if request.method == 'POST':
        settings_data = {
            "night_mode": bool(request.form.get("night_mode")),
            "block_media": bool(request.form.get("block_media")),
            "kick_links": bool(request.form.get("kick_links")),
            "verify_new_users": bool(request.form.get("verify_new_users"))
        }
        doc_ref.set(settings_data)
    doc = doc_ref.get()
    settings = doc.to_dict() if doc.exists else {
        "night_mode": False,
        "block_media": False,
        "kick_links": False,
        "verify_new_users": False
    }
    return render_template_string(HTML_SETTINGS, settings=settings)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)