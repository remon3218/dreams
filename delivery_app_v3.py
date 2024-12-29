import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO

# إعدادات كلمة المرور لكل فرع
BRANCH_PASSWORDS = {
    "بالم هيلز": "dreams@123",
    "القطامية": "dreams@123"
}

# إعدادات كلمة مرور الإدارة
ADMIN_PASSWORD = "admin123"

# اختيار الفرع وكلمة المرور
if "branch" not in st.session_state:
    st.session_state.branch = None
    st.session_state.password_verified = False

if not st.session_state.password_verified:
    st.title("تسجيل الدخول للنظام")
    
    branch_name = st.selectbox("اختر الفرع", ["-- اختر الفرع --", "بالم هيلز", "القطامية"], key="branch_name_input")
    password = st.text_input("أدخل كلمة المرور", type="password", key="password_input", placeholder="كلمة المرور")

    if branch_name and password:
        if branch_name in BRANCH_PASSWORDS and BRANCH_PASSWORDS[branch_name] == password:
            st.session_state.password_verified = True
            st.session_state.branch = branch_name
            st.success(f"تم تسجيل الدخول بنجاح إلى فرع {branch_name}!")
        else:
            st.error("اسم الفرع أو كلمة المرور غير صحيحة!")

# فقط إذا تم التحقق من كلمة المرور
if st.session_state.password_verified:
    # اتصال بقاعدة بيانات الفرع المحدد
    db_name = f"delivery_app_{st.session_state.branch}.db"
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()    # إنشاء الجداول إذا لم تكن موجودة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            delivery_person TEXT,
            order_id TEXT,
            amount REAL,
            date TEXT,
            exit_time TEXT,
            payment_method TEXT,
            machine INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_persons (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    """)
    conn.commit()

    # استرجاع أسماء الدليفري
    cursor.execute("SELECT name FROM delivery_persons ORDER BY name ASC")
    delivery_persons = [row[0] for row in cursor.fetchall()]

    # تحديد الخيارات في الشريط الجانبي
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
        order_amount = st.number_input("قيمة الطلب", min_value=0.0, step=0.01, format="%.2f", key="order_amount_input")
        
        # تحديد طريقة الدفع
        payment_method = st.selectbox("طريقة الدفع", ["كاش", "فيزا", "إنستا"], key="payment_method_input")
        
        # إظهار قائمة المكنة إذا تم اختيار فيزا
        machine = None
        if payment_method == "فيزا":
            machine = st.selectbox("اختر المكنة", ["مكنة 1", "مكنة 2", "مكنة 3", "مكنة 4", "مكنة 5", "مكنة 6"], key="machine_input")

        order_date = datetime.now().strftime("%Y-%m-%d")
        exit_time = datetime.now().strftime("%H:%M:%S")
        
        # زر الحفظ
        if st.button("حفظ الطلب", key="save_order_button"):
            if delivery_person and order_id and payment_method:
                cursor.execute("""
                    INSERT INTO orders (delivery_person, order_id, amount, date, exit_time, payment_method)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (delivery_person, order_id, order_amount, order_date, exit_time, payment_method))
                
                if machine and payment_method == "فيزا":
                    # يمكن تخزين اختيار المكنة إذا كانت ضرورية في الجدول
                    st.success(f"تم تسجيل الطلب باستخدام {machine}")
                conn.commit()
                st.success("تم حفظ الطلب بنجاح!")


        # استعراض الطلبات المدخلة أسفل إدخال الطلب
        st.subheader("الطلبات المدخلة")

        cursor.execute("SELECT * FROM orders ORDER BY date DESC, exit_time DESC LIMIT 10")
        orders = cursor.fetchall()
        if orders:
            df = pd.DataFrame(orders, columns=["ID", "الدليفري", "رقم الطلب", "المبلغ", "تاريخ الطلب", "وقت الخروج", "طريقة الدفع", "المكنة"])
            st.dataframe(df.style.set_properties(**{'text-align': 'center'}).set_table_styles(
                [{'selector': 'th', 'props': [('text-align', 'center')]}]))
        else:
            st.warning("لا توجد طلبات مدخلة بعد.")

    # القسم الخاص بإدارة أسماء الدليفري
    elif option == "إدارة أسماء الدليفري":
        st.header("إدارة أسماء الدليفري")

        admin_password = st.text_input("أدخل كلمة المرور للإدارة", type="password", key="admin_password_input", placeholder="كلمة المرور")
            
        if admin_password == ADMIN_PASSWORD:
            st.session_state.password_verified = True
            st.success("تم تسجيل الدخول بنجاح!")

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
                
    # القسم الخاص بتعديل الطلبات
    elif option == "تعديل الطلبات":
        st.header("تعديل الطلبات")
        
        # إدخال رقم الطلب وكلمة السر
        order_to_edit = st.text_input("أدخل رقم الطلب المراد التعديل عليه")
        
        entered_password = st.text_input("أدخل كلمة المرور", type="password")
        
        if entered_password == ADMIN_PASSWORD:
            cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_to_edit,))
            order = cursor.fetchone()

            if order:
                order_id, delivery_person, order_number, amount, date, exit_time, payment_method, machine = order
                
                # عرض التفاصيل في حقول يمكن تعديلها
                edited_delivery_person = st.selectbox("اسم الدليفري", delivery_persons, index=delivery_persons.index(delivery_person) if delivery_person in delivery_persons else 0)
                edited_order_amount = st.number_input("قيمة الطلب", value=amount, min_value=0.0, step=0.01)
                edited_payment_method = st.selectbox("طريقة الدفع", ["كاش", "فيزا", "إنستا"], index=["كاش", "فيزا", "إنستا"].index(payment_method))
                edited_machine = st.selectbox("المكنة", ["مكينة 1", "مكينة 2", "مكينة 3", "مكينة 4", "مكينة 5", "مكينة 6"], index=machine-1)
                edited_order_id = st.text_input("رقم الطلب المعدل", value=order_number)
                
                if st.button("حفظ التعديلات"):
                    cursor.execute("""
                        UPDATE orders
                        SET delivery_person = ?, amount = ?, payment_method = ?, machine = ?, order_id = ?
                        WHERE order_id = ?
                    """, (edited_delivery_person, edited_order_amount, edited_payment_method, edited_machine, edited_order_id, order_to_edit))
                    conn.commit()
                    st.success(f"تم تعديل الطلب {order_to_edit} بنجاح!")
            else:
                st.warning("لم يتم العثور على الطلب.")
        else:
            st.error("كلمة المرور غير صحيحة!")
            
    # القسم الخاص بعرض الطلبات مع الفلاتر
    elif option == "عرض الطلبات":
        st.header("عرض الطلبات")
        
        with st.expander("خيارات البحث"):
            selected_name = st.selectbox("اسم الدليفري (اختياري)", ["الكل"] + delivery_persons, index=0, key="filter_delivery_person")
            selected_payment_method = st.selectbox("طريقة الدفع (اختياري)", ["الكل", "كاش", "فيزا", "إنستا"], index=0, key="filter_payment_method")
            start_date = st.date_input("من تاريخ", value=(datetime.now() - timedelta(days=7)), key="filter_start_date")
            end_date = st.date_input("إلى تاريخ", value=datetime.now(), key="filter_end_date")
            apply_filters = st.button("تطبيق البحث", key="apply_filters_button")

        query = "SELECT * FROM orders WHERE 1=1"
        params = []

        if apply_filters:
            if selected_name != "الكل":
                query += " AND delivery_person = ?"
                params.append(selected_name)
            if selected_payment_method != "الكل":
                query += " AND payment_method = ?"
                params.append(selected_payment_method)
            if start_date and end_date:
                query += " AND date BETWEEN ? AND ?"
                params.append(start_date.strftime("%Y-%m-%d"))
                params.append(end_date.strftime("%Y-%m-%d"))

        query += " ORDER BY date DESC, exit_time DESC"
        cursor.execute(query, params)
        orders = cursor.fetchall()
        
        if orders:
            df = pd.DataFrame(orders, columns=["ID", "الدليفري", "رقم الطلب", "المبلغ", "تاريخ الطلب", "وقت الخروج", "طريقة الدفع", "المكنة"])
            
            # عرض النتائج في جدول أنيق
            st.dataframe(df.style.set_properties(**{'text-align': 'center'}).set_table_styles(
                [{'selector': 'th', 'props': [('text-align', 'center')]}]))

            # عرض ملخص الطلبات: عدد الطلبات التي قام بها كل دليفري
            st.subheader("ملخص الطلبات لكل دليفري")
            
            query_summary = """
            SELECT delivery_person, COUNT(*) as num_orders, SUM(amount) as total_amount
            FROM orders
            GROUP BY delivery_person
            ORDER BY num_orders DESC
            """
            cursor.execute(query_summary)
            summary = cursor.fetchall()
            
            if summary:
                df_summary = pd.DataFrame(summary, columns=["الدليفري", "عدد الطلبات", "إجمالي المبلغ"])
                st.dataframe(df_summary)
            else:
                st.warning("لا توجد بيانات لتعرضها.")

            # تنزيل النتائج كملف Excel
            st.subheader("تحميل النتائج كملف Excel")
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, sheet_name="نتائج البحث", index=False)
            
            output.seek(0)
            
            st.download_button(
                label="تحميل الملف",
                data=output,
                file_name="نتائج_البحث.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("لا توجد نتائج تطابق البحث.")
