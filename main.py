import os
import qrcode
import pandas as pd
import streamlit as st
from datetime import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="سيستم تسجيل طلاب المبدع", page_icon="🎓", layout="wide")

# 2. زرار تبديل المظهر العصري (شبه الصورة - شمس وقمر) في القائمة الجانبية
is_dark_mode = st.sidebar.toggle("🌙 الوضع الداكن (Dark Mode)", value=False)

# تحديد الألوان بناءً على اختيار الزرار العصري
if not is_dark_mode:
    bg_color = "#fcfbf7"          # أوف وايت / سكري هادئ ومريح للعين
    text_color = "#000000"        # أسود واضح
    card_bg = "#0b192c"           # كحلي فاخر للخانات
    card_text = "#ffffff"         # نص أبيض داخل الخانات
    sidebar_bg = "#0b192c"        # كحلي فاخر
else:
    bg_color = "#121212"          # أسود رمادي داكن فخم
    text_color = "#ffffff"        # أبيض واضح
    card_bg = "#1e3e62"           # كحلي داكن متناسق
    card_text = "#ffffff"         # نص أبيض
    sidebar_bg = "#09101d"        # كحلي أدكن للـ Sidebar

# تطبيق التنسيقات المتقدمة عبر CSS
st.markdown(f"""
    <style>
    /* خلفية التطبيق العامة */
    .stApp {{
        background-color: {bg_color};
    }}
    
    /* القائمة الجانبية (Sidebar) */
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
    }}
    
    /* نصوص القائمة الجانبية باللون الأبيض */
    [data-testid="stSidebar"] * {{
        color: #ffffff !important;
    }}
    
    /* العنوان الرئيسي باللمسة الذهبية */
    h1 {{
        color: {text_color} !important;
        font-family: 'Tahoma', sans-serif;
        border-bottom: 3px solid #d4af37;
        padding-bottom: 10px;
    }}
    
    /* العناوين الفرعية */
    h2, h3 {{
        color: {text_color} !important;
    }}
    
    /* أسماء الخانات والخيارات فوق المربعات */
    label, .stTextInput label, .stSelectbox label, .stRadio label {{
        color: {text_color} !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }}
    
    /* النصوص والخيارات داخل الـ Radio والـ Checkbox */
    .stRadio div label p, .stCheckbox div label p {{
        color: {text_color} !important;
    }}
    
    /* خلفية خانات الإدخال وقوائم الاختيار بلون كحلي متناسق */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {{
        background-color: {card_bg} !important;
        border-radius: 8px;
        border: 1px solid #d4af37;
    }}
    
    /* النص داخل الخانات لون أبيض واضح */
    input, select, option {{
        color: {card_text} !important;
    }}

    /* الأزرار بلون كحلي وتصميم مميز بلمسة ذهبية */
    .stButton>button {{
        background-color: #0b192c;
        color: #ffffff;
        border: 2px solid #d4af37;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5rem 1rem;
    }}
    .stButton>button:hover {{
        background-color: #d4af37;
        color: #0b192c;
        border-color: #0b192c;
    }}
    </style>
""", unsafe_allow_html=True)

# قائمة المراحل الدراسية (إعدادي + أولى ثانوي فقط)
GRADES_LIST = [
    "الصف الأول الإعدادي",
    "الصف الثاني الإعدادي",
    "الصف الثالث الإعدادي",
    "الصف الأول الثانوي"
]

# إنشاء المجلدات وملفات البيانات لو مش موجودة
if not os.path.exists("qr_codes"):
    os.makedirs("qr_codes")

if not os.path.exists("students.csv"):
    pd.DataFrame(columns=["كود الطالب", "الاسم", "المرحلة", "رقم ولي الأمر", "نظام الدفع", "فئة الخصم"]).to_csv("students.csv", index=False)

if not os.path.exists("grades.csv"):
    pd.DataFrame(columns=["كود الطالب", "التاريخ", "الحالة", "درجة الواجب", "درجة الامتحان"]).to_csv("grades.csv", index=False)

if not os.path.exists("payments.csv"):
    pd.DataFrame(columns=["كود الطالب", "التاريخ", "نوع الدفع", "المبلغ المدفوع", "رقم الحصة في الاشتراك", "ملاحظات"]).to_csv("payments.csv", index=False)

# دالة لقراءة جدول الطلاب بمرونة تامة
def load_students_df():
    df = pd.read_csv("students.csv")
    if "فئة الخصم" not in df.columns:
        df["فئة الخصم"] = "عادي (بدون خصم - 35 ج)"
    if "نظام الدفع" not in df.columns:
        df["نظام الدفع"] = "بالحصة"
    df.to_csv("students.csv", index=False)
    return df

# دالة لتحديد الكود التلقائي التالي
def get_next_student_id():
    df = load_students_df()
    if df.empty:
        return "1"
    try:
        numeric_ids = pd.to_numeric(df["كود الطالب"], errors='coerce').dropna()
        if not numeric_ids.empty:
            next_id = int(numeric_ids.max()) + 1
            return str(next_id)
    except:
        pass
    return str(len(df) + 1)

# دالة لتحديث وتوليد الـ QR Code الشامل للطالب
def update_student_qr(student_id):
    students_df = load_students_df()
    grades_df = pd.read_csv("grades.csv")
    payments_df = pd.read_csv("payments.csv")
    
    s_match = students_df[students_df["كود الطالب"].astype(str) == str(student_id).strip()]
    if s_match.empty:
        return
    
    s_info = s_match.iloc[0]
    name = s_info["الاسم"]
    grade = s_info["المرحلة"]
    parent_phone = s_info["رقم ولي الأمر"]
    pay_system = s_info.get("نظام الدفع", "بالحصة")
    discount_cat = s_info.get("فئة الخصم", "عادي (بدون خصم - 35 ج)")
    
    s_grades = grades_df[grades_df["كود الطالب"].astype(str) == str(student_id).strip()]
    attendance_text = "لا توجد حصص مسجلة بعد"
    if not s_grades.empty:
        last_g = s_grades.iloc[-1]
        attendance_text = f"التاريخ: {last_g['التاريخ']} | الحالة: {last_g['الحالة']}\nالواجب: {last_g['درجة الواجب']} | الامتحان: {last_g['درجة الامتحان']}"
    
    s_payments = payments_df[payments_df["كود الطالب"].astype(str) == str(student_id).strip()]
    total_paid = 0
    last_pay_text = "لا توجد مدفوعات مسجلة"
    if not s_payments.empty:
        total_paid = s_payments["المبلغ المدفوع"].sum()
        last_p = s_payments.iloc[-1]
        last_pay_text = f"أخر دفع: {last_p['المبلغ المدفوع']} ج ({last_p['نوع الدفع']}) بتاريخ {last_p['التاريخ']}"
        
    qr_content = (
        f"--- سيستم تسجيل طلاب المبدع ---\n"
        f"الاسم: {name}\n"
        f"الكود: {student_id}\n"
        f"المرحلة: {grade}\n"
        f"ولي الأمر: {parent_phone}\n"
        f"نظام الدفع: {pay_system} | الخصم: {discount_cat}\n\n"
        f"--- أحدث حضور ودرجات ---\n"
        f"{attendance_text}\n\n"
        f"--- الملف المالي ---\n"
        f"إجمالي المدفوعات: {total_paid} جنيه\n"
        f"{last_pay_text}"
    )
    
    qr_img = qrcode.make(qr_content)
    qr_path = f"qr_codes/{student_id}.png"
    qr_img.save(qr_path)
    return qr_path

st.title("⭐ سيستم تسجيل طلاب المبدع")

menu = [
    "تسجيل طالب جديد",
    "تسجيل الحضور والدفع السريع",
    "إدارة المدفوعات والإيرادات اليومية",
    "تعديل بيانات طالب",
    "عرض بيانات طالب (QR)",
]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

# ----------------- 1. قسم تسجيل طالب جديد -----------------
if choice == "تسجيل طالب جديد":
    st.header("📝 إضافة طالب جديد وتوليد QR Code")

    suggested_id = get_next_student_id()

    with st.form("add_student_form"):
        student_id = st.text_input("كود الطالب", value=suggested_id)
        name = st.text_input("اسم الطالب")
        grade = st.selectbox("المرحلة الدراسية", GRADES_LIST)
        parent_phone = st.text_input("رقم ولي الأمر")
        payment_system = st.radio("نظام الدفع الأساسي", ["بالحصة", "بالشهر (اشتراك)"])
        discount_category = st.selectbox(
            "فئة الخصم والاتفاق الثابت",
            ["عادي (بدون خصم - 35 ج)", "يتيم / المميزين (يدفع 20 ج)", "معفي تماماً (0 ج)", "أخوات - توأم (مبلغ ثابت 35 ج)", "أخوات - مراحل مختلفة (مبلغ ثابت 30 ج)"]
        )
        submit = st.form_submit_button("حفظ الطالب")

    if submit:
        if student_id and name:
            students_df = load_students_df()

            if student_id.strip() in students_df["كود الطالب"].astype(str).values:
                st.error("كود الطالب هذا مسجل مسبقاً!")
            else:
                new_student = {
                    "كود الطالب": student_id.strip(),
                    "الاسم": name,
                    "المرحلة": grade,
                    "رقم ولي الأمر": parent_phone,
                    "نظام الدفع": payment_system,
                    "فئة الخصم": discount_category,
                }
                students_df = pd.concat([students_df, pd.DataFrame([new_student])], ignore_index=True)
                students_df.to_csv("students.csv", index=False)

                qr_path = update_student_qr(student_id.strip())

                st.success(f"تم حفظ الطالب {name} (كود: {student_id.strip()}) وتوليد الـ QR Code بنجاح!")
                st.image(qr_path, caption=f"QR Code الخاص بـ {name}", width=200)
        else:
            st.warning("يرجى كتابة كود الطالب واسمه.")

# ----------------- 2. قسم تسجيل الحضور والدفع السريع -----------------
elif choice == "تسجيل الحضور والدفع السريع":
    st.header("⚡ تسجيل الحضور والدفع في خطوة واحدة")

    students_df = load_students_df()
    if students_df.empty:
        st.info("لا يوجد طلاب مسجلين بعد.")
    else:
        search_id = st.text_input("أدخل كود الطالب لتسجيل الحضور والدفع")

        if search_id:
            student_match = students_df[students_df["كود الطالب"].astype(str) == search_id.strip()]

            if not student_match.empty:
                s_info = student_match.iloc[0]
                student_name = s_info["الاسم"]
                student_grade = s_info["المرحلة"]
                discount_cat = s_info.get("فئة الخصم", "عادي (بدون خصم - 35 ج)")
                
                fixed_amount = 35 
                if "20 ج" in discount_cat:
                    fixed_amount = 20
                elif "معفي" in discount_cat:
                    fixed_amount = 0
                elif "35 ج" in discount_cat:
                    fixed_amount = 35
                elif "30 ج" in discount_cat:
                    fixed_amount = 30

                st.success(f"الطالب: **{student_name}** | المرحلة: **{student_grade}** | نظام الخصم: **{discount_cat}** (المبلغ الثابت: {fixed_amount} جنيه)")

                with st.form("quick_attendance_form"):
                    date = st.date_input("تاريخ اليوم للحصة", value=datetime.today())
                    status = st.radio("حالة الحضور", ["حاضر", "غائب"])
                    
                    add_grades = st.checkbox("إضافة درجات الواجب والامتحان (اختياري)")
                    hw_score, ex_score = 0, 0
                    if add_grades:
                        hw_score = st.number_input("درجة الواجب", min_value=0, max_value=100, value=0)
                        ex_score = st.number_input("درجة الامتحان", min_value=0, max_value=100, value=0)
                        
                    auto_pay = st.checkbox("تسجيل دفع المصروفات مع الحصة تلقائياً (بالمبلغ الثابت)", value=True)
                    notes = st.text_input("ملاحظات الحصة أو الدفع (اختياري)")
                    
                    submit_quick = st.form_submit_button("إتمام وتسجيل الحصة")

                if submit_quick:
                    date_str = str(date)
                    s_id_clean = search_id.strip()
                    
                    grades_df = pd.read_csv("grades.csv")
                    already_attended = not grades_df[(grades_df["كود الطالب"].astype(str) == s_id_clean) & (grades_df["التاريخ"] == date_str)].empty
                    
                    if already_attended:
                        st.warning(f"⚠️ تنبيه: الطالب {student_name} مسجل له حضور بالفعل في تاريخ اليوم ({date_str})!")
                    else:
                        new_grade = {
                            "كود الطالب": s_id_clean,
                            "التاريخ": date_str,
                            "الحالة": status,
                            "درجة الواجب": hw_score,
                            "درجة الامتحان": ex_score,
                        }
                        grades_df = pd.concat([grades_df, pd.DataFrame([new_grade])], ignore_index=True)
                        grades_df.to_csv("grades.csv", index=False)
                        
                        if auto_pay and status == "حاضر":
                            payments_df = pd.read_csv("payments.csv")
                            new_pay = {
                                "كود الطالب": s_id_clean,
                                "التاريخ": date_str,
                                "نوع الدفع": "حصة بالحضور (تلقائي)",
                                "المبلغ المدفوع": fixed_amount,
                                "رقم الحصة في الاشتراك": "-",
                                "ملاحظات": notes if notes else f"خصم: {discount_cat}"
                            }
                            payments_df = pd.concat([payments_df, pd.DataFrame([new_pay])], ignore_index=True)
                            payments_df.to_csv("payments.csv", index=False)
                        
                        update_student_qr(s_id_clean)
                        st.success(f"✨ تم تسجيل الحضور والدفع أوتوماتيكياً للطالب {student_name} بنجاح دون تكرار!")
            else:
                st.error("عذراً، هذا الكود غير مسجل في السيستم.")

# ----------------- 3. قسم إدارة المدفوعات والإيرادات اليومية -----------------
elif choice == "إدارة المدفوعات والإيرادات اليومية":
    st.header("💰 ملخص الإيرادات والعمليات المالية اليومية")

    payments_df = pd.read_csv("payments.csv")
    students_df = load_students_df()

    if payments_df.empty:
        st.info("لا توجد عمليات دفع مسجلة بعد.")
    else:
        selected_date = st.date_input("اختر تاريخ اليوم لعرض إيراداته", value=datetime.today())
        date_str = str(selected_date)
        
        day_payments = payments_df[payments_df["التاريخ"] == date_str]
        
        st.subheader(f"📅 ملخص إيرادات يوم: {date_str}")
        if day_payments.empty:
            st.info("لا توجد تحصيلات مالية مسجلة في هذا التاريخ.")
        else:
            total_day_revenue = day_payments["المبلغ المدفوع"].sum()
            st.metric(label="إجمالي إيرادات اليوم", value=f"{total_day_revenue} جنيه")
            
            merged_pay = day_payments.merge(students_df[["كود الطالب", "الاسم"]], on="كود الطالب", how="left")
            st.dataframe(merged_pay[["كود الطالب", "الاسم", "نوع الدفع", "المبلغ المدفوع", "ملاحظات"]])

        st.divider()
        st.subheader("سجل جميع المدفوعات العامة للسنتر")
        st.dataframe(payments_df)

# ----------------- 4. قسم تعديل بيانات طالب -----------------
elif choice == "تعديل بيانات طالب":
    st.header("⚙️ تعديل البيانات الأساسية وفئات الخصم للطالب")

    students_df = load_students_df()
    if students_df.empty:
        st.info("لا يوجد طلاب للتعديل.")
    else:
        edit_id = st.text_input("أدخل كود الطالب لتعديل بياناته")

        if edit_id:
            edit_id_clean = edit_id.strip()
            student_idx = students_df[students_df["كود الطالب"].astype(str) == edit_id_clean].index

            if not student_idx.empty:
                idx = student_idx[0]
                current_data = students_df.loc[idx]

                st.success(f"تعديل بيانات الطالب: **{current_data['الاسم']}**")

                cur_grade = current_data.get("المرحلة", "الصف الأول الثانوي")
                current_grade_idx = GRADES_LIST.index(cur_grade) if cur_grade in GRADES_LIST else 0
                
                cur_pay_sys = current_data.get("نظام الدفع", "بالحصة")
                pay_sys_idx = 0 if cur_pay_sys == "بالحصة" else 1

                discount_list = [
                    "عادي (بدون خصم - 35 ج)",
                    "يتيم / المميزين (يدفع 20 ج)",
                    "معفي تماماً (0 ج)",
                    "أخوات - توأم (مبلغ ثابت 35 ج)",
                    "أخوات - مراحل مختلفة (مبلغ ثابت 30 ج)"
                ]
                cur_disc = current_data.get("فئة الخصم", "عادي (بدون خصم - 35 ج)")
                disc_idx = discount_list.index(cur_disc) if cur_disc in discount_list else 0

                with st.form("edit_student_form"):
                    new_name = st.text_input("اسم الطالب", value=current_data["الاسم"])
                    new_grade = st.selectbox("المرحلة الدراسية", GRADES_LIST, index=current_grade_idx)
                    new_phone = st.text_input("رقم ولي الأمر", value=str(current_data.get("رقم ولي الأمر", "")))
                    new_pay_sys = st.radio("نظام الدفع الأساسي", ["بالحصة", "بالشهر (اشتراك)"], index=pay_sys_idx)
                    new_disc = st.selectbox("فئة الخصم والاتفاق الثابت", discount_list, index=disc_idx)
                    
                    save_changes = st.form_submit_button("حفظ التعديلات وتحديث الـ QR")

                if save_changes:
                    students_df.loc[idx, "الاسم"] = new_name
                    students_df.loc[idx, "المرحلة"] = new_grade
                    students_df.loc[idx, "رقم ولي الأمر"] = new_phone
                    students_df.loc[idx, "نظام الدفع"] = new_pay_sys
                    students_df.loc[idx, "فئة الخصم"] = new_disc
                    
                    students_df.to_csv("students.csv", index=False)
                    update_student_qr(edit_id_clean)
                    
                    st.success("تم تحديث بيانات الطالب وتحديث الـ QR Code بنجاح! 🎉")
            else:
                st.error("لم يتم العثور على طالب بهذا الكود.")

# ----------------- 5. قسم عرض البيانات والـ QR -----------------
elif choice == "عرض بيانات طالب (QR)":
    st.header("🔍 استعراض الملف الكامل للطالب والـ QR Code")

    students_df = load_students_df()
    grades_df = pd.read_csv("grades.csv")
    payments_df = pd.read_csv("payments.csv")

    if students_df.empty:
        st.info("لا يوجد طلاب مسجلين.")
    else:
        search_id = st.text_input("أدخل كود الطالب للبحث عن سجله الكامل")

        if search_id:
            student_info = students_df[students_df["كود الطالب"].astype(str) == search_id.strip()]

            if not student_info.empty:
                qr_path = update_student_qr(search_id.strip())
                
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader("📌 البيانات الثابتة والاتفاق المالي:")
                    st.dataframe(student_info)

                with col2:
                    if os.path.exists(qr_path):
                        st.image(qr_path, caption="QR Code الطالب (محدث بالبيانات الحية)", width=200)

                st.subheader("📊 سجل الحضور والدرجات:")
                s_grades = grades_df[grades_df["كود الطالب"].astype(str) == search_id.strip()]
                if s_grades.empty:
                    st.write("لا توجد حصص مسجلة بعد.")
                else:
                    st.dataframe(s_grades)

                st.subheader("💰 سجل المدفوعات:")
                s_payments = payments_df[payments_df["كود الطالب"].astype(str) == search_id.strip()]
                if s_payments.empty:
                    st.write("لا توجد مدفوعات مسجلة بعد.")
                else:
                    st.dataframe(s_payments)
            else:
                st.error("لم يتم العثور على طالب بهذا الكود.")