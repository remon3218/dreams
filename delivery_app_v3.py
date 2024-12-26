import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO

# إعداد قاعدة البيانات
conn = sqlite3.connect("delivery_app.db")
cursor = conn.cursor()

# إنشاء الجداول إذا لم تكن موجودة
cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        delivery_person TEXT,
        order_id TEXT,
        amount REAL,
        date TEXT,
        exit_time TEXT,
        payment_method TEXT
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS delivery_persons (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    )
""")
conn.commit()

# قراءة أسماء الدليفري
cursor.execute("SELECT name FROM delivery_persons ORDER BY name ASC")
delivery_persons = [row[0] for row in cursor.fetchall()]

# إعدادات كلمة المرور
ADMIN_PASSWORD = "dreams123"

if "password_verified" not in st.session_state:
    st.session_state.password_verified = False

option = st.sidebar.radio(
    "اختر العملية",
    ["إدخال الطلبات", "إدارة أسماء الدليفري", "عرض الطلبات", "تعديل الطلبات"],
    key="menu_option"
)

# القسم الخاص بإدخال الطلبات
if option == "إدخال الطلبات":
    st.header("إدخال طلب جديد")
    
    if not delivery_persons:
        st.warning("يرجى إضافة أسماء الدليفري أولاً من قسم 'إدارة أسماء الدليفري'.")
    else:
        delivery_person = st.selectbox("اسم الدليفري", delivery_persons, key="delivery_person_input")
        order_id = st.text_input("رقم الطلب", key="order_id_input")
        order_amount = st.number_input("قيمة الطلب", min_value=0.0, step=0.01, key="order_amount_input")
        
        # خانة اختيار طريقة الدفع مع إضافة خيارات للمكينة عند اختيار فيزا
        payment_method = st.selectbox("طريقة الدفع", ["كاش", "فيزا", "إنستا"], key="payment_method_input")
        selected_machine = None

        if payment_method == "فيزا":
            selected_machine = st.selectbox("اختار المكنة", ["مكنة 1", "مكنة 2", "مكنة 3", "مكنة 4", "مكنة 5", "مكنة 6"], key="machine_input")

        order_date = datetime.now().strftime("%Y-%m-%d")
        exit_time = datetime.now().strftime("%H:%M:%S")
        
        if st.button("حفظ الطلب", key="save_order_button"):
            if delivery_person and order_id and payment_method:
                if payment_method == "فيزا" and selected_machine:
                    payment_method = f"فيزا - {selected_machine}"
                
                cursor.execute("""
                    INSERT INTO orders (delivery_person, order_id, amount, date, exit_time, payment_method)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (delivery_person, order_id, order_amount, order_date, exit_time, payment_method))
                
                conn.commit()
                st.success("تم حفظ الطلب بنجاح!")

    st.subheader("آخر الطلبات")
    cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 5")
    recent_orders = cursor.fetchall()

    if recent_orders:
        df_recent_orders = pd.DataFrame(recent_orders, columns=["ID", "الدليفري", "رقم الطلب", "المبلغ", "تاريخ الطلب", "وقت الخروج", "طريقة الدفع"])
        st.dataframe(df_recent_orders)
    else:
        st.warning("لا توجد طلبات حالياً.")
        
# القسم الخاص بإدارة أسماء الدليفري
elif option == "إدارة أسماء الدليفري":
    st.header("إدارة أسماء الدليفري")
    
    if not st.session_state.password_verified:
        admin_password = st.text_input("أدخل كلمة المرور لإدارة أسماء الدليفري", type="password", key="admin_password_input")
        
        if admin_password == ADMIN_PASSWORD:
            st.session_state.password_verified = True
            st.success("تم تسجيل الدخول بنجاح!")
        elif admin_password and admin_password != ADMIN_PASSWORD:
            st.error("كلمة المرور غير صحيحة!")

    if st.session_state.password_verified:
        new_delivery_person = st.text_input("أدخل اسم الدليفري الجديد", key="new_delivery_person_input")
        
        if st.button("إضافة اسم الدليفري", key="add_delivery_person_button"):
            if new_delivery_person:
                try:
                    cursor.execute("INSERT INTO delivery_persons (name) VALUES (?)", (new_delivery_person,))
                    conn.commit()
                    st.success("تم إضافة اسم الدليفري بنجاح!")
                except sqlite3.IntegrityError:
                    st.error("اسم الدليفري موجود بالفعل!")
            else:
                st.error("يرجى إدخال اسم الدليفري.")
        
        cursor.execute("SELECT name FROM delivery_persons ORDER BY name ASC")
        delivery_persons_list = [row[0] for row in cursor.fetchall()]
        
        if delivery_persons_list:
            selected_delivery = st.selectbox("اختر اسم الدليفري لحذفه", delivery_persons_list, key="delete_delivery_person_input")
            
            if st.button("حذف اسم الدليفري", key="delete_delivery_person_button"):
                cursor.execute("DELETE FROM delivery_persons WHERE name = ?", (selected_delivery,))
                conn.commit()
                st.success(f"تم حذف {selected_delivery} بنجاح!")
        else:
            st.warning("لا توجد أسماء دليفري حالياً.")
            
# القسم الخاص بعرض الطلبات
elif option == "عرض الطلبات":
    st.header("عرض الطلبات")
    
    with st.expander("خيارات البحث"):
        selected_name = st.selectbox("اسم الدليفري (اختياري)", ["الكل"] + delivery_persons, key="filter_delivery_person")
        selected_payment_method = st.selectbox("طريقة الدفع (اختياري)", ["الكل", "كاش", "فيزا", "إنستا"], key="filter_payment_method")
        start_date = st.date_input("من تاريخ", value=(datetime.now() - timedelta(days=7)), key="filter_start_date")
        end_date = st.date_input("إلى تاريخ", value=datetime.now(), key="filter_end_date")
        apply_filters = st.button("تطبيق الفلاتر")

    query = "SELECT * FROM orders WHERE 1=1"
    params = []

    if apply_filters:
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

    if orders:
        df = pd.DataFrame(orders, columns=["ID", "الدليفري", "رقم الطلب", "المبلغ", "تاريخ الطلب", "وقت الخروج", "طريقة الدفع"])
        st.dataframe(df)
    else:
        st.warning("لا توجد نتائج تطابق الفلاتر.")
        
# القسم الخاص بتعديل الطلبات
elif option == "تعديل الطلبات":
    st.header("تعديل الطلبات")
    
    order_to_edit = st.text_input("أدخل رقم الطلب للتعديل")
    entered_password = st.text_input("أدخل كلمة المرور", type="password")

    if entered_password == ADMIN_PASSWORD:
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_to_edit,))
        order = cursor.fetchone()

        if order:
            order_id, delivery_person, order_number, amount, date, exit_time, payment_method = order
            
            new_delivery_person = st.selectbox("اسم الدليفري", delivery_persons, index=delivery_persons.index(delivery_person) if delivery_person in delivery_persons else 0)
            new_amount = st.number_input("قيمة الطلب", value=amount, step=0.01)
            new_payment_method = st.selectbox("طريقة الدفع", ["كاش", "فيزا", "إنستا"], index=["كاش", "فيزا", "إنستا"].index(payment_method))
            
            if new_payment_method == "فيزا":
                selected_machine = st.selectbox("اختار المكنة", ["مكنة 1", "مكنة 2", "مكنة 3", "مكنة 4", "مكنة 5", "مكنة 6"])
                new_payment_method = f"فيزا - {selected_machine}"

            if st.button("حفظ التعديلات"):
                cursor.execute("""
                    UPDATE orders
                    SET delivery_person = ?, amount = ?, payment_method = ?
                    WHERE order_id = ?
                """, (new_delivery_person, new_amount, new_payment_method, order_to_edit))
                conn.commit()
                st.success(f"تم تعديل الطلب رقم {order_to_edit} بنجاح!")
        else:
            st.warning("رقم الطلب غير موجود.")
    else:
        st.error("كلمة المرور غير صحيحة!")
