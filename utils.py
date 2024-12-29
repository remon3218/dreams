import sqlite3

# دالة لفتح الاتصال بقاعدة البيانات الخاصة بكل فرع
def get_connection(branch_name):
    conn = sqlite3.connect(f"delivery_app_{branch_name}.db")
    return conn

# دالة للتحقق من وجود الفرع في قاعدة البيانات
def validate_branch_exists(branch_name):
    try:
        conn = get_connection(branch_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except sqlite3.Error as e:
        return False

# دالة لإضافة اسم دليفري جديد
def add_delivery_person(branch_name, delivery_person):
    conn = get_connection(branch_name)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO delivery_persons (name) VALUES (?)", (delivery_person,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# دالة لحذف اسم دليفري من قاعدة البيانات
def delete_delivery_person(branch_name, delivery_person):
    conn = get_connection(branch_name)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM delivery_persons WHERE name = ?", (delivery_person,))
    conn.commit()
    conn.close()

# دالة لاسترجاع جميع أسماء الدليفري
def get_all_delivery_persons(branch_name):
    conn = get_connection(branch_name)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM delivery_persons ORDER BY name ASC")
    delivery_persons = [row[0] for row in cursor.fetchall()]
    conn.close()
    return delivery_persons

# دالة لإدخال طلب جديد إلى قاعدة البيانات
def insert_order(branch_name, delivery_person, order_id, amount, date, exit_time, payment_method):
    conn = get_connection(branch_name)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (delivery_person, order_id, amount, date, exit_time, payment_method)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (delivery_person, order_id, amount, date, exit_time, payment_method))
    conn.commit()
    conn.close()

# دالة لاسترجاع آخر 5 طلبات
def get_recent_orders(branch_name):
    conn = get_connection(branch_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 5")
    orders = cursor.fetchall()
    conn.close()
    return orders

# دالة لإجراء فلاتر عرض الطلبات بناءً على بعض المعايير
def filter_orders(branch_name, selected_name, selected_payment_method, start_date, end_date):
    conn = get_connection(branch_name)
    cursor = conn.cursor()
    query = "SELECT * FROM orders WHERE 1=1"
    params = []

    if selected_name != "الكل":
        query += " AND delivery_person = ?"
        params.append(selected_name)
    if selected_payment_method != "الكل":
        query += " AND payment_method = ?"
        params.append(selected_payment_method)

    query += " AND date BETWEEN ? AND ?"
    params.extend([start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")])

    query += " ORDER BY date DESC, exit_time DESC"
    cursor.execute(query, params)
    orders = cursor.fetchall()
    conn.close()
    return orders

# دالة لحساب مجموع الطلبات لكل دليفري
def get_summary_orders(branch_name, selected_name, selected_payment_method, start_date, end_date):
    conn = get_connection(branch_name)
    cursor = conn.cursor()
    query = """
        SELECT delivery_person, SUM(amount) as total_amount, COUNT(*) as total_orders
        FROM orders
        WHERE 1=1
    """
    params = []

    if selected_name != "الكل":
        query += " AND delivery_person = ?"
        params.append(selected_name)
    if selected_payment_method != "الكل":
        query += " AND payment_method = ?"
        params.append(selected_payment_method)

    query += " AND date BETWEEN ? AND ?"
    params.extend([start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")])

    query += " GROUP BY delivery_person ORDER BY total_amount DESC"
    cursor.execute(query, params)
    summary_data = cursor.fetchall()
    conn.close()
    return summary_data
