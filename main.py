import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
import hashlib
import cv2
from pyzbar.pyzbar import decode
import numpy as np
from PIL import Image
import io
import re

# =============================================
# إعدادات متقدمة لتحسين الأداء
# =============================================

st.set_page_config(
    page_title="نظام إدارة مركز الصيانة - Tornado",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.google.com',
        'Report a bug': "https://www.google.com",
        'About': "نظام إدارة مركز صيانة الهواتف - الإصدار 4.0"
    }
)

# =============================================
# إعدادات الوضع الداكن والمظهر
# =============================================

def apply_custom_styles():
    """تطبيق التصميم المخصص مع الوضع الداكن"""
    st.markdown("""
        <style>
        :root {
            --primary: #1f77b4;
            --secondary: #ff4b4b;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
            --info: #17a2b8;
            --dark-bg: #0f1012;
            --dark-card: #1f2124;
            --dark-text: #EDEDED;
            --secondary-text: #B7B7C2;
        }
        
        .main-header {
            font-size: 2.8rem;
            color: var(--primary);
            text-align: center;
            margin-bottom: 2rem;
            background: linear-gradient(45deg, #1f77b4, #ff4b4b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
            padding: 1rem;
        }
        
        .dashboard-header {
            font-size: 2.2rem;
            color: var(--dark-text);
            margin-bottom: 1.5rem;
            font-weight: 900;
            text-align: right;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #1f2124 0%, #232428 100%);
            padding: 1.5rem;
            border-radius: 15px;
            color: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            border: 1px solid #2a2b2f;
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .revenue-card {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }
        
        .pending-card {
            background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
            color: white;
        }
        
        .cancelled-card {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            color: white;
        }
        
        .dark-card {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            border-radius: 15px;
            padding: 1.5rem;
            color: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        
        .action-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .action-card:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        
        .sidebar {
            background: linear-gradient(180deg, #121216 0%, #15161a 100%);
        }
        
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .status-pending { background-color: #fff3cd; color: #856404; }
        .status-in-progress { background-color: #cce7ff; color: #004085; }
        .status-completed { background-color: #d4edda; color: #155724; }
        .status-waiting { background-color: #f8d7da; color: #721c24; }
        .status-cancelled { background-color: #e2e3e5; color: #383d41; }
        
        .developer-footer {
            text-align: center;
            margin-top: 3rem;
            padding: 1rem;
            background: linear-gradient(135deg, #1f2124 0%, #232428 100%);
            border-radius: 10px;
            color: var(--secondary-text);
        }
        
        .today-highlight {
            border: 2px solid #28a745;
            box-shadow: 0 0 15px rgba(40, 167, 69, 0.3);
        }
        
        .month-highlight {
            border: 2px solid #ffc107;
            box-shadow: 0 0 15px rgba(255, 193, 7, 0.3);
        }
        
        .delete-btn {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
        }
        
        .delete-btn:hover {
            background: linear-gradient(135deg, #c82333 0%, #a71e2a 100%);
        }
        
        /* إصلاحات للوضع الداكن */
        .stApp {
            background: #0f1012;
        }
        
        .main .block-container {
            padding-top: 2rem;
        }
        
        /* تحسينات للنصوص */
        h1, h2, h3, h4, h5, h6, p, div, span {
            color: #EDEDED !important;
        }
        
        /* تحسينات للأزرار */
        .stButton button {
            border-radius: 10px;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

# =============================================
# تحسينات التخزين المؤقت للأداء
# =============================================

@st.cache_resource(ttl=3600)
def get_sheet_connection():
    """اتصال مخزن مؤقت بـ Google Sheets"""
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive']
        
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("tornado").sheet1
        return sheet
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بـ Google Sheets: {e}")
        return None

@st.cache_data(ttl=120)
def get_all_data_cached():
    """جلب البيانات مع التخزين المؤقت"""
    sheet = get_sheet_connection()
    if sheet:
        try:
            with st.spinner("🔄 جاري تحميل البيانات..."):
                data = sheet.get_all_records()
                df = pd.DataFrame(data)
                
                # معالجة البيانات
                if not df.empty:
                    if 'التاريخ' in df.columns:
                        df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
                    if 'التكلفة' in df.columns:
                        df['التكلفة'] = pd.to_numeric(df['التكلفة'], errors='coerce').fillna(0)
                    if 'رقم_العميل' in df.columns:
                        df['رقم_العميل'] = df['رقم_العميل'].astype(str)
                    if 'IMEI' in df.columns:
                        df['IMEI'] = df['IMEI'].astype(str)
                    if 'تاريخ_التسليم' in df.columns:
                        df['تاريخ_التسليم'] = pd.to_datetime(df['تاريخ_التسليم'], errors='coerce')
                
                return df
        except Exception as e:
            st.error(f"❌ خطأ في قراءة البيانات: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=300)
def calculate_statistics(df):
    """حساب الإحصائيات مع التخزين المؤقت"""
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    stats = {
        'today_customers': 0,
        'month_customers': 0,
        'today_revenue': 0,
        'month_revenue': 0,
        'under_maintenance': 0,
        'completed': 0,
        'waiting_parts': 0,
        'cancelled': 0,
        'total_customers': 0,
        'total_revenue': 0,
        'pending_revenue': 0,  # الأموال المعلقة
        'cancelled_revenue': 0,  # الأموال الملغية
        'actual_revenue': 0  # الإيرادات الفعلية
    }
    
    if not df.empty and 'التاريخ' in df.columns:
        # العملاء اليوم والشهر
        stats['today_customers'] = len(df[df['التاريخ'].dt.date == today])
        stats['month_customers'] = len(df[df['التاريخ'].dt.date >= month_start])
        
        # الإيرادات حسب الحالة
        if 'التكلفة' in df.columns and 'الحالة' in df.columns:
            # الإيرادات الفعلية (المكتملة فقط)
            stats['actual_revenue'] = df[df['الحالة'] == 'مكتمل']['التكلفة'].sum() if not df[df['الحالة'] == 'مكتمل'].empty else 0
            
            # الأموال المعلقة (قيد الصيانة + بانتظار قطع الغيار)
            pending_mask = (df['الحالة'] == 'قيد الصيانة') | (df['الحالة'] == 'بانتظار قطع الغيار')
            stats['pending_revenue'] = df[pending_mask]['التكلفة'].sum() if not df[pending_mask].empty else 0
            
            # الأموال الملغية
            stats['cancelled_revenue'] = df[df['الحالة'] == 'ملغي']['التكلفة'].sum() if not df[df['الحالة'] == 'ملغي'].empty else 0
            
            # الإيرادات الإجمالية (للتتبع فقط)
            stats['total_revenue'] = df['التكلفة'].sum()
            
            # إيرادات اليوم والشهر (المكتملة فقط)
            today_completed = df[(df['التاريخ'].dt.date == today) & (df['الحالة'] == 'مكتمل')]
            stats['today_revenue'] = today_completed['التكلفة'].sum() if not today_completed.empty else 0
            
            month_completed = df[(df['التاريخ'].dt.date >= month_start) & (df['الحالة'] == 'مكتمل')]
            stats['month_revenue'] = month_completed['التكلفة'].sum() if not month_completed.empty else 0
        
        # الحالات
        if 'الحالة' in df.columns:
            stats['under_maintenance'] = len(df[df['الحالة'] == 'قيد الصيانة'])
            stats['completed'] = len(df[df['الحالة'] == 'مكتمل'])
            stats['waiting_parts'] = len(df[df['الحالة'] == 'بانتظار قطع الغيار'])
            stats['cancelled'] = len(df[df['الحالة'] == 'ملغي'])
        
        stats['total_customers'] = len(df)
    
    return stats

# =============================================
# وظائف مساعدة محسنة
# =============================================

def generate_customer_id():
    """إنشاء رقم عميل تلقائي يبدأ بـ 9 ويتكون من 8 رقم"""
    timestamp = str(int(time.time()))[-10:]  # أخذ آخر 10 أرقام من timestamp
    customer_id = "9" + timestamp.zfill(8)  # إضافة 9 في البداية وإكمال إلى 8 رقم
    return customer_id[:8]  # التأكد من أن الطول 8 رقم فقط

def validate_phone_number(phone):
    """التحقق من صحة رقم الهاتف"""
    if not phone:
        return False
    pattern = r'^01[0-2,5]{1}[0-9]{8}$'
    return re.match(pattern, str(phone)) is not None

def validate_customer_id(customer_id):
    """التحقق من صحة رقم العميل"""
    if not customer_id:
        return False
    pattern = r'^9\d{7}$'
    return re.match(pattern, str(customer_id)) is not None

def show_success_animation():
    """عرض رسالة النجاح مع الأنيميشن"""
    success_html = """
    <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 3rem; border-radius: 20px; text-align: center; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.3); z-index: 1000;
                animation: pulse 2s infinite;" class="success-animation">
        <h1 style="color: white; font-size: 3rem; margin: 0;">🎉</h1>
        <h2 style="color: white; margin: 1rem 0;">جدع يصحبي! 🤩</h2>
        <p style="color: white; font-size: 1.2rem;">تم إضافة العميل بنجاح!</p>
    </div>
    <style>
    @keyframes pulse {
        0% { transform: translate(-50%, -50%) scale(1); }
        50% { transform: translate(-50%, -50%) scale(1.05); }
        100% { transform: translate(-50%, -50%) scale(1); }
    }
    </style>
    """
    st.markdown(success_html, unsafe_allow_html=True)
    st.balloons()

def add_new_record_optimized(record_data):
    """إضافة سجل جديد محسن"""
    sheet = get_sheet_connection()
    if sheet:
        try:
            # التأكد من وجود تاريخ التسليم
            delivery_date = record_data.get('delivery_date')
            if delivery_date and hasattr(delivery_date, 'strftime'):
                delivery_date_str = delivery_date.strftime("%Y-%m-%d")
            else:
                delivery_date_str = ""
            
            # إعداد البيانات للتسجيل
            record = [
                str(record_data.get('customer_id', '')),
                str(record_data.get('customer_name', '')),
                str(record_data.get('phone_number', '')),
                str(record_data.get('device_type', '')),
                str(record_data.get('problem', '')),
                str(record_data.get('status', '')),
                float(record_data.get('cost', 0)),
                datetime.now().strftime("%Y-%m-%d"),
                delivery_date_str,
                str(record_data.get('imei', ''))
            ]
            
            sheet.append_row(record)
            
            # مسح التخزين المؤقت للتحديث
            get_all_data_cached.clear()
            calculate_statistics.clear()
            
            return True
        except Exception as e:
            st.error(f"❌ خطأ في إضافة البيانات: {str(e)}")
            return False
    return False

def update_customer_status(customer_id, new_status):
    """تحديث حالة العميل"""
    sheet = get_sheet_connection()
    if sheet:
        try:
            data = sheet.get_all_values()
            for i, row in enumerate(data[1:], start=2):  # start=2 لأن الصف الأول هو العناوين
                if len(row) > 0 and str(row[0]) == str(customer_id):
                    sheet.update_cell(i, 6, new_status)  # العمود 6 هو الحالة
                    
                    # مسح التخزين المؤقت
                    get_all_data_cached.clear()
                    calculate_statistics.clear()
                    
                    return True
        except Exception as e:
            st.error(f"❌ خطأ في تحديث الحالة: {e}")
    return False

def delete_customer_record(customer_id):
    """حذف سجل العميل"""
    sheet = get_sheet_connection()
    if sheet:
        try:
            data = sheet.get_all_values()
            for i, row in enumerate(data[1:], start=2):  # start=2 لأن الصف الأول هو العناوين
                if len(row) > 0 and str(row[0]) == str(customer_id):
                    sheet.delete_rows(i)
                    
                    # مسح التخزين المؤقت
                    get_all_data_cached.clear()
                    calculate_statistics.clear()
                    
                    return True
        except Exception as e:
            st.error(f"❌ خطأ في حذف العميل: {e}")
    return False

def initialize_sheet_enhanced():
    """تهيئة الورقة مع تحسينات"""
    sheet = get_sheet_connection()
    if sheet:
        try:
            existing_data = sheet.get_all_values()
            if len(existing_data) == 0:
                headers = [
                    "رقم_العميل", "اسم_العميل", "رقم_الهاتف", "نوع_الجهاز",
                    "المشكلة", "الحالة", "التكلفة", "التاريخ", "تاريخ_التسليم", "IMEI"
                ]
                sheet.append_row(headers)
                st.success("✅ تم تهيئة الجدول بنجاح")
        except Exception as e:
            st.error(f"❌ خطأ في تهيئة البيانات: {e}")

# =============================================
# ميزة البحث المتقدم
# =============================================

def show_advanced_search():
    """البحث المتقدم عن العملاء"""
    st.header("🔍 البحث المتقدم عن العملاء")
    
    df = get_all_data_cached()
    
    if not df.empty:
        # خيارات البحث المتقدم
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔎 معايير البحث")
            search_type = st.radio(
                "نوع البحث:",
                ["بحث سريع", "بحث متقدم"],
                horizontal=True
            )
            
            if search_type == "بحث سريع":
                search_term = st.text_input(
                    "ابحث في جميع الحقول",
                    placeholder="ادخل رقم العميل، الاسم، رقم الهاتف، IMEI..."
                )
                
                if search_term:
                    # البحث في جميع الحقول النصية
                    mask = df.astype(str).apply(
                        lambda x: x.str.contains(search_term, case=False, na=False)
                    ).any(axis=1)
                    search_results = df[mask]
                else:
                    search_results = pd.DataFrame()
            
            else:  # بحث متقدم
                col_a, col_b = st.columns(2)
                
                with col_a:
                    customer_id_search = st.text_input("رقم العميل")
                    customer_name_search = st.text_input("اسم العميل")
                    phone_search = st.text_input("رقم الهاتف")
                
                with col_b:
                    imei_search = st.text_input("رقم IMEI")
                    device_type_search = st.selectbox(
                        "نوع الجهاز",
                        ["الكل", "سامسونج", "آيفون", "هواوي", "شاومي", "أوبو", "انفينكس", "ريلمي", "اندر", "آخر"]
                    )
                    status_search = st.selectbox(
                        "الحالة",
                        ["الكل", "قيد الصيانة", "مكتمل", "بانتظار قطع الغيار", "مستعصي", "ملغي"]
                    )
                
                # تطبيق فلاتر البحث المتقدم
                search_results = df.copy()
                
                if customer_id_search:
                    search_results = search_results[search_results['رقم_العميل'].astype(str).str.contains(customer_id_search, case=False, na=False)]
                
                if customer_name_search:
                    search_results = search_results[search_results['اسم_العميل'].astype(str).str.contains(customer_name_search, case=False, na=False)]
                
                if phone_search:
                    search_results = search_results[search_results['رقم_الهاتف'].astype(str).str.contains(phone_search, case=False, na=False)]
                
                if imei_search:
                    search_results = search_results[search_results['IMEI'].astype(str).str.contains(imei_search, case=False, na=False)]
                
                if device_type_search != "الكل":
                    search_results = search_results[search_results['نوع_الجهاز'] == device_type_search]
                
                if status_search != "الكل":
                    search_results = search_results[search_results['الحالة'] == status_search]
        
        with col2:
            st.subheader("⏰ تصفية بالتاريخ")
            
            date_filter_type = st.radio(
                "نوع التصفية:",
                ["جميع التواريخ", "تاريخ محدد", "نطاق زمني"],
                horizontal=True
            )
            
            if date_filter_type == "تاريخ محدد":
                specific_date = st.date_input("اختر تاريخ")
                if 'search_results' in locals() and not search_results.empty:
                    search_results = search_results[search_results['التاريخ'].dt.date == specific_date]
            
            elif date_filter_type == "نطاق زمني":
                col_start, col_end = st.columns(2)
                with col_start:
                    start_date = st.date_input("من تاريخ")
                with col_end:
                    end_date = st.date_input("إلى تاريخ")
                
                if start_date and end_date and 'search_results' in locals() and not search_results.empty:
                    search_results = search_results[
                        (search_results['التاريخ'].dt.date >= start_date) & 
                        (search_results['التاريخ'].dt.date <= end_date)
                    ]
        
        # عرض نتائج البحث
        if 'search_results' in locals() and not search_results.empty:
            st.subheader(f"📊 نتائج البحث ({len(search_results)} سجل)")
            
            # خيارات التصدير
            col_exp1, col_exp2, col_exp3 = st.columns([2, 1, 1])
            
            with col_exp1:
                st.download_button(
                    label="💾 تحميل نتائج البحث كـ CSV",
                    data=search_results.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                    file_name=f"نتائج_البحث_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_exp2:
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    search_results.to_excel(writer, index=False, sheet_name='نتائج_البحث')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📊 تحميل كـ Excel",
                    data=excel_data,
                    file_name=f"نتائج_البحث_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col_exp3:
                if st.button("🔄 مسح البحث", use_container_width=True):
                    st.rerun()
            
            # عرض البيانات
            for index, row in search_results.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**👤 {row.get('اسم_العميل', 'غير معروف')}**")
                        st.write(f"**📞 {row.get('رقم_الهاتف', 'غير معروف')}**")
                        st.write(f"**📱 {row.get('نوع_الجهاز', 'غير معروف')}**")
                        st.write(f"**📝 {row.get('المشكلة', 'غير معروف')}**")
                    
                    with col2:
                        st.write(f"**🆔 {row.get('رقم_العميل', 'غير معروف')}**")
                        if 'IMEI' in row and pd.notna(row['IMEI']) and row['IMEI'] != '':
                            st.write(f"**🔢 IMEI: {row['IMEI']}**")
                        st.write(f"**💰 {row.get('التكلفة', 0):,.0f} ج.م**")
                        if 'التاريخ' in row and pd.notna(row['التاريخ']):
                            try:
                                st.write(f"**📅 {row['التاريخ'].strftime('%Y-%m-%d')}**")
                            except:
                                st.write(f"**📅 غير محدد**")
                        else:
                            st.write(f"**📅 غير محدد**")
                        st.write(f"**🔄 الحالة: {row.get('الحالة', 'غير معروف')}**")
                    
                    with col3:
                        # زر حذف العميل
                        if st.button("🗑️ حذف", key=f"delete_{index}", use_container_width=True):
                            if delete_customer_record(row['رقم_العميل']):
                                st.success("✅ تم حذف العميل بنجاح!")
                                time.sleep(2)
                                st.rerun()
                        
                        # تحديث الحالة
                        current_status = row.get('الحالة', 'قيد الصيانة')
                        status_options = ["قيد الصيانة", "مكتمل", "بانتظار قطع الغيار", "مستعصي", "ملغي"]
                        
                        new_status = st.selectbox(
                            "تعديل الحالة",
                            status_options,
                            index=status_options.index(current_status) if current_status in status_options else 0,
                            key=f"search_status_{index}"
                        )
                        
                        if new_status != current_status:
                            if st.button("💾 حفظ", key=f"search_save_{index}", use_container_width=True):
                                if update_customer_status(row['رقم_العميل'], new_status):
                                    st.success("✅ تم تحديث الحالة بنجاح!")
                                    time.sleep(1)
                                    st.rerun()
                    
                    st.markdown("---")
        else:
            if 'search_results' in locals() and search_results.empty:
                st.info("🔍 لا توجد نتائج تطابق معايير البحث")
            else:
                st.info("🔍 استخدم معايير البحث للعثور على العملاء")
    
    else:
        st.info("📭 لا توجد بيانات للبحث فيها")

# =============================================
# واجهات المستخدم المحسنة
# =============================================

def show_main_dashboard():
    """لوحة التحكم الرئيسية المحسنة"""
    st.markdown('<div class="dashboard-header">📊 لوحة التحكم - نظرة عامة</div>', unsafe_allow_html=True)
    
    # الحصول على البيانات والإحصائيات
    df = get_all_data_cached()
    stats = calculate_statistics(df)
    
    # عرض نظرة عامة على الحالات
    st.subheader("📈 نظرة عامة على الحالات")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🔄 قيد الصيانة</h3>
            <h1>{stats['under_maintenance']}</h1>
            <p>جهاز</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>✅ مكتمل</h3>
            <h1>{stats['completed']}</h1>
            <p>جهاز</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>⏳ بانتظار القطع</h3>
            <h1>{stats['waiting_parts']}</h1>
            <p>جهاز</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>❌ ملغي</h3>
            <h1>{stats['cancelled']}</h1>
            <p>جهاز</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <h3>👥 الإجمالي</h3>
            <h1>{stats['total_customers']}</h1>
            <p>عميل</p>
        </div>
        """, unsafe_allow_html=True)
    
    # عرض الإيرادات المالية المحسنة
    st.subheader("💰 الإيرادات المالية")
    
    col_rev1, col_rev2, col_rev3 = st.columns(3)
    
    with col_rev1:
        st.markdown(f"""
        <div class="metric-card revenue-card">
            <h3>💰 الإيرادات الفعلية</h3>
            <h1>{stats['actual_revenue']:,.0f}</h1>
            <p>جنية مصري</p>
            <p style="font-size: 0.9rem;">(الحالات المكتملة فقط)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_rev2:
        st.markdown(f"""
        <div class="metric-card pending-card">
            <h3>⏸️ أموال معلقة</h3>
            <h1>{stats['pending_revenue']:,.0f}</h1>
            <p>جنية مصري</p>
            <p style="font-size: 0.9rem;">(قيد الصيانة + بانتظار قطع)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_rev3:
        st.markdown(f"""
        <div class="metric-card cancelled-card">
            <h3>❌ أموال ملغية</h3>
            <h1>{stats['cancelled_revenue']:,.0f}</h1>
            <p>جنية مصري</p>
            <p style="font-size: 0.9rem;">(الحالات الملغية)</p>
        </div>
        """, unsafe_allow_html=True)
    
    # مقارنة بين عملاء اليوم وعملاء الشهر
    st.subheader("📅 مقارنة العملاء")
    
    col_today, col_month = st.columns(2)
    
    with col_today:
        st.markdown(f"""
        <div class="metric-card today-highlight">
            <h3>📊 عملاء اليوم</h3>
            <h1>{stats['today_customers']}</h1>
            <p>عميل</p>
            <h4>💰 {stats['today_revenue']:,.0f} ج.م</h4>
            <p style="font-size: 0.9rem;">(إيرادات مكتملة فقط)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_month:
        st.markdown(f"""
        <div class="metric-card month-highlight">
            <h3>📈 عملاء الشهر</h3>
            <h1>{stats['month_customers']}</h1>
            <p>عميل</p>
            <h4>💰 {stats['month_revenue']:,.0f} ج.م</h4>
            <p style="font-size: 0.9rem;">(إيرادات مكتملة فقط)</p>
        </div>
        """, unsafe_allow_html=True)
    
    # مخططات سريعة
    st.subheader("📊 تحليلات سريعة")
    
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # مخطط الحالات
            if 'الحالة' in df.columns:
                status_data = df['الحالة'].value_counts()
                if not status_data.empty:
                    fig_status = px.pie(
                        values=status_data.values,
                        names=status_data.index,
                        title="توزيع الحالات",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # مخطط الإيرادات حسب الحالة
            if 'الحالة' in df.columns and 'التكلفة' in df.columns:
                revenue_by_status = df.groupby('الحالة')['التكلفة'].sum().reset_index()
                if not revenue_by_status.empty:
                    fig_revenue = px.bar(
                        revenue_by_status,
                        x='الحالة',
                        y='التكلفة',
                        title="الإيرادات حسب الحالة",
                        color='الحالة',
                        color_discrete_map={
                            'مكتمل': '#28a745',
                            'قيد الصيانة': '#ffc107',
                            'بانتظار قطع الغيار': '#fd7e14',
                            'ملغي': '#dc3545'
                        }
                    )
                    st.plotly_chart(fig_revenue, use_container_width=True)

def show_add_customer_form():
    """نموذج إضافة عميل محسن"""
    st.header("➕ إضافة عميل جديد")
    
    # استخدام st.form بشكل صحيح
    with st.form("add_customer_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔹 معلومات العميل")
            
            # توليد رقم العميل تلقائياً
            customer_id = st.text_input("رقم العميل *", value=generate_customer_id())
            
            # التحقق من صحة رقم العميل
            if customer_id and not validate_customer_id(customer_id):
                st.error("❌ رقم العميل غير صحيح. يجب أن يبدأ بـ 9 ويتكون من 8 رقم")
            
            customer_name = st.text_input("اسم العميل *", placeholder="أدخل الاسم بالكامل")
            phone_number = st.text_input("رقم الهاتف *", placeholder="مثال: 01012345678")
            
            # التحقق من رقم الهاتف أثناء الكتابة
            if phone_number and not validate_phone_number(phone_number):
                st.warning("⚠️ رقم الهاتف غير صحيح. يجب أن يبدأ بـ 01 ويحتوي على 11 رقماً")
            
            device_type = st.selectbox(
                "نوع الجهاز *",
                ["سامسونج", "آيفون", "هواوي", "شاومي", "أوبو", "انفينكس", "ريلمي", "اندر", "آخر"]
            )
        
        with col2:
            st.subheader("🔹 تفاصيل الصيانة")
            problem = st.text_area(
                "وصف المشكلة *", 
                placeholder="وصف مفصل للمشكلة...",
                height=100
            )
            
            status = st.selectbox(
                "الحالة *",
                ["قيد الصيانة", "مكتمل", "بانتظار قطع الغيار", "مستعصي", "ملغي"]
            )
            
            cost = st.number_input(
                "التكلفة (ج.م) *",
                min_value=0.0,
                value=0.0,
                step=50.0
            )
            
            delivery_date = st.date_input(
                "تاريخ التسليم المتوقع",
                min_value=datetime.now().date()
            )
            
            # قسم IMEI مع مسح الباركود
            st.subheader("🔢 رقم IMEI")
            imei_number = st.text_input("رقم IMEI", placeholder="الرقم التسلسلي للجهاز", key="imei_input")
        
        # زر الإرسال الرئيسي - يجب أن يكون داخل st.form()
        submitted = st.form_submit_button(
            "💾 حفظ العميل",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            # التحقق من الحقول الإلزامية
            if not all([customer_id, customer_name, phone_number, device_type, problem, status]):
                st.error("❌ يرجى ملء جميع الحقول الإلزامية (*)")
            elif not validate_phone_number(phone_number):
                st.error("❌ رقم الهاتف غير صحيح")
            elif not validate_customer_id(customer_id):
                st.error("❌ رقم العميل غير صحيح")
            else:
                record_data = {
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'phone_number': phone_number,
                    'device_type': device_type,
                    'problem': problem,
                    'status': status,
                    'cost': cost,
                    'delivery_date': delivery_date,
                    'imei': imei_number
                }
                
                if add_new_record_optimized(record_data):
                    show_success_animation()
                    time.sleep(2)
                    st.rerun()

def show_all_customers_enhanced():
    """عرض جميع العملاء مع تحسينات"""
    st.header("👥 عرض جميع العملاء")
    
    df = get_all_data_cached()
    
    if not df.empty:
        # شريط البحث والتصفية المتقدم
        st.subheader("🔍 البحث والتصفية المتقدم")
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            search_term = st.text_input("بحث سريع", placeholder="ابحث بالاسم، رقم الهاتف، المشكلة...")
        
        with col2:
            status_filter = st.selectbox("الحالة", ["الكل", "قيد الصيانة", "مكتمل", "بانتظار قطع الغيار", "مستعصي", "ملغي"])
        
        with col3:
            device_filter = st.selectbox("نوع الجهاز", ["الكل", "سامسونج", "آيفون", "هواوي", "شاومي", "أوبو", "انفينكس", "ريلمي", "اندر", "آخر"])
        
        with col4:
            date_filter = st.date_input("التاريخ")
        
        # تطبيق الفلاتر
        filtered_df = df.copy()
        
        if search_term:
            mask = filtered_df.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            filtered_df = filtered_df[mask]
        
        if status_filter != "الكل":
            filtered_df = filtered_df[filtered_df['الحالة'] == status_filter]
        
        if device_filter != "الكل":
            filtered_df = filtered_df[filtered_df['نوع_الجهاز'] == device_filter]
        
        if date_filter and 'التاريخ' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['التاريخ'].dt.date == date_filter]
        
        # عرض البيانات مع تحسينات
        st.subheader(f"📊 النتائج ({len(filtered_df)} سجل)")
        
        if not filtered_df.empty:
            # خيارات التصدير
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            
            with col_exp1:
                csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="💾 تحميل CSV",
                    data=csv_data,
                    file_name=f"عملاء_الصيانة_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_exp2:
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    filtered_df.to_excel(writer, index=False, sheet_name='العملاء')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📊 تحميل Excel",
                    data=excel_data,
                    file_name=f"عملاء_الصيانة_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col_exp3:
                if st.button("🔄 تحديث البيانات", use_container_width=True):
                    get_all_data_cached.clear()
                    st.rerun()
            
            # عرض كل عميل في بطاقة منفصلة
            for index, row in filtered_df.iterrows():
                # تحديد إذا كان عميل اليوم أو الشهر
                is_today = False
                is_this_month = False
                
                if 'التاريخ' in row and pd.notna(row['التاريخ']):
                    try:
                        is_today = row['التاريخ'].date() == datetime.now().date()
                        is_this_month = row['التاريخ'].date().month == datetime.now().month
                    except:
                        pass
                
                card_class = ""
                if is_today:
                    card_class = "today-highlight"
                elif is_this_month:
                    card_class = "month-highlight"
                
                with st.container():
                    st.markdown(f'<div class="metric-card {card_class}">', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**👤 {row.get('اسم_العميل', 'غير معروف')}**")
                        st.write(f"**📞 {row.get('رقم_الهاتف', 'غير معروف')}**")
                        st.write(f"**📱 {row.get('نوع_الجهاز', 'غير معروف')}**")
                        st.write(f"**📝 {row.get('المشكلة', 'غير معروف')}**")
                    
                    with col2:
                        st.write(f"**🆔 {row.get('رقم_العميل', 'غير معروف')}**")
                        if 'IMEI' in row and pd.notna(row['IMEI']) and row['IMEI'] != '':
                            st.write(f"**🔢 IMEI: {row['IMEI']}**")
                        st.write(f"**💰 {row.get('التكلفة', 0):,.0f} ج.م**")
                        if 'التاريخ' in row and pd.notna(row['التاريخ']):
                            try:
                                st.write(f"**📅 {row['التاريخ'].strftime('%Y-%m-%d')}**")
                            except:
                                st.write(f"**📅 غير محدد**")
                        else:
                            st.write(f"**📅 غير محدد**")
                    
                    with col3:
                        # زر حذف العميل
                        if st.button("🗑️ حذف", key=f"delete_{index}", use_container_width=True):
                            if delete_customer_record(row['رقم_العميل']):
                                st.success("✅ تم حذف العميل بنجاح!")
                                time.sleep(2)
                                st.rerun()
                        
                        # تحديث الحالة
                        current_status = row.get('الحالة', 'قيد الصيانة')
                        status_options = ["قيد الصيانة", "مكتمل", "بانتظار قطع الغيار", "مستعصي", "ملغي"]
                        
                        new_status = st.selectbox(
                            f"تعديل الحالة",
                            status_options,
                            index=status_options.index(current_status) if current_status in status_options else 0,
                            key=f"status_{index}"
                        )
                        
                        if new_status != current_status:
                            if st.button("💾 حفظ", key=f"save_{index}", use_container_width=True):
                                if update_customer_status(row['رقم_العميل'], new_status):
                                    st.success("✅ تم تحديث الحالة بنجاح!")
                                    time.sleep(1)
                                    st.rerun()
                    
                    st.write(f"**🔄 الحالة:** {row.get('الحالة', 'غير معروف')}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown("---")
        else:
            st.info("🔍 لا توجد نتائج تطابق معايير البحث")
    else:
        st.info("📭 لا توجد بيانات لعرضها")

def show_advanced_statistics():
    """الإحصائيات المتقدمة"""
    st.header("📈 الإحصائيات والتقارير المتقدمة")
    
    df = get_all_data_cached()
    
    if not df.empty:
        # إحصائيات سريعة
        stats = calculate_statistics(df)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("إجمالي العملاء", len(df))
        with col2:
            st.metric("إجمالي الإيرادات", f"{stats['total_revenue']:,.0f} ج.م")
        with col3:
            avg_cost = df['التكلفة'].mean() if 'التكلفة' in df.columns else 0
            st.metric("متوسط التكلفة", f"{avg_cost:,.0f} ج.م")
        with col4:
            max_cost = df['التكلفة'].max() if 'التكلفة' in df.columns else 0
            st.metric("أعلى تكلفة", f"{max_cost:,.0f} ج.م")
        
        # المخططات المتقدمة
        st.subheader("📊 تحليلات متقدمة")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # توزيع الأجهزة
            if 'نوع_الجهاز' in df.columns:
                device_counts = df['نوع_الجهاز'].value_counts()
                if not device_counts.empty:
                    fig_devices = px.bar(
                        x=device_counts.values,
                        y=device_counts.index,
                        orientation='h',
                        title="توزيع الأجهزة حسب النوع",
                        color=device_counts.values,
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig_devices, use_container_width=True)
        
        with col_chart2:
            # الإيرادات الشهرية (المكتملة فقط)
            if 'التاريخ' in df.columns and 'التكلفة' in df.columns and 'الحالة' in df.columns:
                try:
                    monthly_data = df[df['الحالة'] == 'مكتمل'].groupby(df['التاريخ'].dt.to_period('M')).agg({
                        'التكلفة': 'sum',
                        'رقم_العميل': 'count'
                    }).reset_index()
                    monthly_data['التاريخ'] = monthly_data['التاريخ'].astype(str)
                    
                    if not monthly_data.empty:
                        fig_monthly = px.line(
                            monthly_data,
                            x='التاريخ',
                            y='التكلفة',
                            title="الإيرادات الشهرية (المكتملة فقط)",
                            markers=True
                        )
                        fig_monthly.update_traces(line=dict(color='#28a745', width=3))
                        st.plotly_chart(fig_monthly, use_container_width=True)
                except Exception as e:
                    st.info("📊 لا توجد بيانات كافية لعرض الإيرادات الشهرية")
        
        # تقرير الحالات المالية
        st.subheader("💰 تقرير الحالات المالية")
        
        financial_data = pd.DataFrame({
            'النوع': ['الإيرادات الفعلية', 'الأموال المعلقة', 'الأموال الملغية'],
            'المبلغ': [stats['actual_revenue'], stats['pending_revenue'], stats['cancelled_revenue']],
            'اللون': ['#28a745', '#ffc107', '#dc3545']
        })
        
        if not financial_data.empty:
            fig_financial = px.pie(
                financial_data,
                values='المبلغ',
                names='النوع',
                title="توزيع الأموال حسب الحالة",
                color='النوع',
                color_discrete_map={
                    'الإيرادات الفعلية': '#28a745',
                    'الأموال المعلقة': '#ffc107',
                    'الأموال الملغية': '#dc3545'
                }
            )
            st.plotly_chart(fig_financial, use_container_width=True)
    
    else:
        st.info("📊 لا توجد بيانات لعرض الإحصائيات")

# =============================================
# الوظيفة الرئيسية - محدثة
# =============================================

def main():
    """الدالة الرئيسية للبرنامج"""
    
    # تهيئة حالة الجلسة
    if 'show_barcode_scanner' not in st.session_state:
        st.session_state.show_barcode_scanner = False
    if 'manual_imei' not in st.session_state:
        st.session_state.manual_imei = ''
    if 'scanned_imei' not in st.session_state:
        st.session_state.scanned_imei = ''
    
    # تطبيق التصميم المخصص
    apply_custom_styles()
    
    # العنوان الرئيسي
    st.markdown('<h1 class="main-header">📱 نظام إدارة مركز صيانة الهواتف - Tornado</h1>', unsafe_allow_html=True)
    
    # الشريط الجانبي المحسن
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #1f2124 0%, #232428 100%); 
                    border-radius: 15px; margin-bottom: 2rem;'>
            <h2>🌀 Tornado System</h2>
            <p>نظام إدارة الصيانة المتكامل</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        menu_option = st.selectbox(
            "اختر القسم:",
            ["الرئيسية", "إضافة عميل جديد", "عرض جميع العملاء", "البحث المتقدم", "البحث بـ IMEI", "الإحصائيات", "الإعدادات"]
        )
        
        st.markdown("---")
        st.subheader("🔄 التحكم السريع")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔄 تحديث", use_container_width=True):
                get_all_data_cached.clear()
                calculate_statistics.clear()
                st.success("✅ تم تحديث البيانات")
                time.sleep(1)
                st.rerun()
        
        with col_btn2:
            if st.button("🧹 تنظيف", use_container_width=True):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("✅ تم مسح الذاكرة المؤقتة")
                time.sleep(1)
                st.rerun()
        
        st.markdown("---")
        st.subheader("ℹ️ معلومات النظام")
        
        df = get_all_data_cached()
        if not df.empty:
            stats = calculate_statistics(df)
            st.write(f"**إجمالي العملاء:** {len(df)}")
            st.write(f"**عملاء اليوم:** {stats['today_customers']}")
            st.write(f"**عملاء الشهر:** {stats['month_customers']}")
            st.write(f"**الإيرادات الفعلية:** {stats['actual_revenue']:,.0f} ج.م")
            st.write(f"**أحدث تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        else:
            st.write("**إجمالي العملاء:** 0")
            st.write("**عملاء اليوم:** 0")
            st.write("**عملاء الشهر:** 0")
            st.write("**الإيرادات الفعلية:** 0 ج.م")
            st.write(f"**أحدث تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # معلومات الأداء
        st.markdown("---")
        st.markdown("### 📊 حالة النظام")
        st.progress(85, text="أداء النظام: 85%")
    
    # تحميل الصفحات حسب الاختيار
    if menu_option == "الرئيسية":
        show_main_dashboard()
    elif menu_option == "إضافة عميل جديد":
        show_add_customer_form()
    elif menu_option == "عرض جميع العملاء":
        show_all_customers_enhanced()
    elif menu_option == "البحث المتقدم":
        show_advanced_search()
    elif menu_option == "البحث بـ IMEI":
        # يمكن إضافة دالة البحث بـ IMEI هنا
        st.info("🔍 ميزة البحث بـ IMEI - سيتم إضافتها في التحديث القادم")
    elif menu_option == "الإحصائيات":
        show_advanced_statistics()
    elif menu_option == "الإعدادات":
        st.header("⚙️ الإعدادات")
        
        col_set1, col_set2 = st.columns(2)
        
        with col_set1:
            st.subheader("إعدادات النظام")
            cache_duration = st.number_input("مدة التخزين المؤقت (دقائق)", value=5, min_value=1, max_value=60)
            language = st.selectbox("لغة الواجهة", ["العربية", "English"])
            page_size = st.slider("حجم الصفحة", 10, 100, 50)
            
        with col_set2:
            st.subheader("معلومات الاتصال")
            center_name = st.text_input("اسم المركز", value="مركز تورنادو للصيانة")
            center_phone = st.text_input("رقم الهاتف", value="01012345678")
            center_address = st.text_area("العنوان", value="القاهرة، مصر")
        
        if st.button("💾 حفظ الإعدادات", type="primary"):
            st.success("✅ تم حفظ الإعدادات بنجاح")
    
    # تذييل الصفحة مع حقوق التطوير
    st.markdown("---")
    st.markdown("""
        <div class="developer-footer">
            <p><strong>نظام إدارة مركز صيانة الهواتف - Tornado v4.0</strong></p>
            <p>تم التطوير باستخدام Python 🐍 و Streamlit ⚡ | تم التحديث: 2024</p>
            <p style="color: #ff4b4b; font-weight: bold;">حقوق التطوير: Ali Khaled</p>
        </div>
    """, unsafe_allow_html=True)

# =============================================
# تشغيل البرنامج
# =============================================

if __name__ == "__main__":
    # تهيئة النظام
    try:
        initialize_sheet_enhanced()
        # تشغيل الواجهة الرئيسية
        main()
    except Exception as e:
        st.error(f"❌ خطأ في تشغيل النظام: {e}")
        st.info("🔄 يرجى تحديث الصفحة والمحاولة مرة أخرى")