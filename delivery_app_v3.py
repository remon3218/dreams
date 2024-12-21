import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

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
        exit_time TEXT
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
ADMIN_PASSWORD = "dreams123"  # كلمة مرور لإدارة الدليفري

# إعداد الجلسة
if "password_verified" not in st.session_state:
    st.session_state.password_verified = False  # الحالة الافتراضية للتحقق من كلمة المرور

# تبويب بين إدخال الطلبات، إدارة أسماء الدليفري، عرض الطلبات
option = st.sidebar.radio(
    "اختر العملية",
    ["إدخال الطلبات", "إدارة أسماء الدليفري", "عرض الطلبات"],
    key="menu_option"
)

if option == "إدخال الطلبات":
    st.header("إدخال طلب جديد")
    
    if not delivery_persons:
        st.warning("يرجى إضافة أسماء الدليفري أولاً من قسم 'إدارة أسماء الدليفري'.")
    else:
        delivery_person = st.selectbox("اسم الدليفري", delivery_persons, key="delivery_person_input")
        order_id = st.text_input("رقم الطلب", key="order_id_input")
        order_amount = st.number_input("قيمة الطلب", min_value=0.0, step=0.01, format="%.2f", key="order_amount_input")
        order_date = datetime.now().strftime("%Y-%m-%d")
        exit_time = datetime.now().strftime("%H:%M:%S")
        
        if st.button("حفظ الطلب", key="save_order_button"):
            if delivery_person and order_id:
                cursor.execute("""
                    INSERT INTO orders (delivery_person, order_id, amount, date, exit_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (delivery_person, order_id, order_amount, order_date, exit_time))
                conn.commit()
                st.success("تم حفظ الطلب بنجاح!")
            else:
                st.error("يرجى ملء جميع الحقول.")

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
                try:
                    cursor.execute("DELETE FROM delivery_persons WHERE name = ?", (selected_delivery,))
                    conn.commit()
                    st.success(f"تم حذف {selected_delivery} بنجاح!")
                except sqlite3.Error as e:
                    st.error(f"حدث خطأ أثناء الحذف: {e}")
        else:
            st.warning("لا توجد أسماء دليفري حالياً.")

elif option == "عرض الطلبات":
    st.header("عرض الطلبات")
    
    with st.expander("خيارات البحث"):
        selected_name = st.selectbox("اسم الدليفري (اختياري)", ["الكل"] + delivery_persons, index=0, key="filter_delivery_person")
        selected_date = st.date_input("تاريخ الطلب (اختياري)", key="filter_order_date")
        apply_filters = st.button("تطبيق البحث", key="apply_filters_button")

    query = "SELECT * FROM orders WHERE 1=1"
    params = []

    if apply_filters:
        if selected_name != "الكل":
            query += " AND delivery_person = ?"
            params.append(selected_name)
        if selected_date:
            query += " AND date = ?"
            params.append(selected_date.strftime("%Y-%m-%d"))

    query += " ORDER BY date DESC, exit_time DESC"
    cursor.execute(query, params)
    orders = cursor.fetchall()
    
    if orders:
        df = pd.DataFrame(orders, columns=["ID", "الدليفري", "رقم الطلب", "المبلغ", "تاريخ الطلب", "وقت الخروج"])
        st.dataframe(df)
    else:
        st.warning("لا توجد نتائج تطابق البحث.")

    st.subheader("إجمالي المبالغ لكل دليفري")
    cursor.execute("SELECT delivery_person, SUM(amount) as total FROM orders GROUP BY delivery_person ORDER BY total DESC")
    totals = cursor.fetchall()
    
    if totals:
        totals_df = pd.DataFrame(totals, columns=["الدليفري", "إجمالي المبلغ"])
        st.dataframe(totals_df)
        
        st.subheader("رسم بياني لإجمالي الطلبات")
        chart_data = totals_df.set_index("الدليفري")
        st.bar_chart(chart_data["إجمالي المبلغ"])
    else:

        st.warning("لا توجد بيانات لعرض الإجماليات.")
