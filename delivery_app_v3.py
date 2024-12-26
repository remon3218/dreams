import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO

# إعداد قاعدة البيانات
conn = sqlite3.connect("delivery_app.db")
cursor = conn.cursor()

# إعداد واجهة التطبيق
st.set_page_config(page_title="تطبيق إدارة الطلبات", layout="wide", initial_sidebar_state="expanded")
st.markdown("<style>body { direction: ltr; text-align: left; }</style>", unsafe_allow_html=True)

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

if option == "إدخال الطلبات":
    st.header("إدخال طلب جديد")
    if not delivery_persons:
        st.warning("يرجى إضافة أسماء الدليفري أولاً من قسم 'إدارة أسماء الدليفري'.")
    else:
        delivery_person = st.selectbox("اسم الدليفري", delivery_persons, key="delivery_person_input")
        order_id = st.text_input("رقم الطلب", key="order_id_input")
        order_amount = st.number_input("قيمة الطلب", min_value=0.0, step=0.01, format="%.2f", key="order_amount_input")
        payment_method = st.selectbox("طريقة الدفع", ["كاش", "فيزا", "إنستا"], key="payment_method_input")
        order_date = datetime.now().strftime("%Y-%m-%d")
        exit_time = datetime.now().strftime("%H:%M:%S")
        if st.button("حفظ الطلب", key="save_order_button"):
            if delivery_person and order_id and payment_method:
                cursor.execute("""
                    INSERT INTO orders (delivery_person, order_id, amount, date, exit_time, payment_method)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (delivery_person, order_id, order_amount, order_date, exit_time, payment_method))
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
        start_date = st.date_input("من تاريخ", value=(datetime.now() - timedelta(days=7)), key="filter_start_date")
        end_date = st.date_input("إلى تاريخ", value=datetime.now(), key="filter_end_date")
        apply_filters = st.button("تطبيق البحث", key="apply_filters_button")

    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    if apply_filters:
        if selected_name != "الكل":
            query += " AND delivery_person = ?"
            params.append(selected_name)
        if start_date and end_date:
            query += " AND date BETWEEN ? AND ?"
            params.append(start_date.strftime("%Y-%m-%d"))
            params.append(end_date.strftime("%Y-%m-%d"))
    query += " ORDER BY date DESC, exit_time DESC"
    cursor.execute(query, params)
    orders = cursor.fetchall()
    if orders:
        df = pd.DataFrame(orders, columns=["ID", "الدليفري", "رقم الطلب", "المبلغ", "تاريخ الطلب", "وقت الخروج", "طريقة الدفع"])
        df["المبلغ"] = df["المبلغ"].apply(lambda x: "{:.2f}".format(x).rstrip("0").rstrip("."))
        st.dataframe(df.style.set_properties(**{'text-align': 'center'}).set_table_styles(
            [{'selector': 'th', 'props': [('text-align', 'center')]}]))
        
        # تنزيل النتائج كملف Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="نتائج البحث", index=False)
        output.seek(0)
        st.download_button(
            label="تحميل الملف كـ Excel",
            data=output,
            file_name="نتائج_البحث.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # عرض ملخص الطلبات لكل دليفري
        st.subheader("ملخص الطلبات لكل دليفري")
        query_summary = """
        SELECT delivery_person, COUNT(*) as num_orders
        FROM orders
        GROUP BY delivery_person
        ORDER BY num_orders DESC
        """
        cursor.execute(query_summary)
        summary = cursor.fetchall()
        if summary:
            df_summary = pd.DataFrame(summary, columns=["الدليفري", "عدد الطلبات"])
            st.dataframe(df_summary)
        else:
            st.warning("لا توجد بيانات لتعرضها.")
    else:
        st.warning("لا توجد نتائج تطابق البحث.")

elif option == "تعديل الطلبات":
    st.header("تعديل الطلبات")
    order_to_edit = st.text_input("أدخل رقم الطلب المراد التعديل عليه")
    entered_password = st.text_input("أدخل كلمة المرور", type="password")
    if entered_password == ADMIN_PASSWORD:
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_to_edit,))
        order = cursor.fetchone()
        if order:
            order_id, delivery_person, order_number, amount, date, exit_time, payment_method = order
            edited_delivery_person = st.selectbox("اسم الدليفري", delivery_persons, index=delivery_persons.index(delivery_person))
            edited_order_amount = st.number_input("قيمة الطلب", value=amount, min_value=0.0, step=0.01)
            edited_payment_method = st.selectbox("طريقة الدفع", ["كاش", "فيزا", "إنستا"], index=["كاش", "فيزا", "إنستا"].index(payment_method))
            edited_order_id = st.text_input("رقم الطلب المعدل", value=order_number)
            if st.button("حفظ التعديلات"):
                cursor.execute("""
                    UPDATE orders
                    SET delivery_person = ?, amount = ?, payment_method = ?, order_id = ?
                    WHERE order_id = ?
                """, (edited_delivery_person, edited_order_amount, edited_payment_method, edited_order_id, order_to_edit))
                conn.commit()
                st.success(f"تم تعديل الطلب {order_to_edit} بنجاح!")
        else:
            st.warning("لم يتم العثور على الطلب.")
    else:
        st.error("كلمة المرور غير صحيحة!")
