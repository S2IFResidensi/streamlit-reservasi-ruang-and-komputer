# import streamlit as st
# from streamlit_option_menu import option_menu

# # --------------------- LOGIN --------------------- #
# if "login_status" not in st.session_state:
#     st.session_state.login_status = False
#     st.session_state.username = ""
#     st.session_state.role = ""

# # Hardcode username & password
# users = {
#     "admin": {"password": "admin123", "role": "admin"},
#     "user1": {"password": "user123", "role": "user"}
# }

# # Jika belum login, tampilkan form login
# if not st.session_state.login_status:
#     st.title("🔒 Login Sistem Reservasi")
#     username = st.text_input("Username")
#     password = st.text_input("Password", type="password")
#     if st.button("Login"):
#         if username in users and password == users[username]["password"]:
#             st.session_state.login_status = True
#             st.session_state.username = username
#             st.session_state.role = users[username]["role"]
#             st.success(f"Login berhasil! Halo {username}")
#             st.rerun()
#         else:
#             st.error("Username atau password salah")

# # Jika sudah login
# else:
#     # Sidebar info & logout
#     with st.sidebar:
#         st.write(f"👤 Login sebagai: {st.session_state.username} ({st.session_state.role})")
#         if st.button("Logout"):
#             st.session_state.login_status = False
#             st.rerun()

#     # --------------------- NAVBAR --------------------- #
#     selected = option_menu(
#         menu_title=None,
#         options=["Home", "Booking", "Data User"] if st.session_state.role == "admin" else ["Home", "Booking"],
#         icons=["house", "calendar", "people"],
#         menu_icon="cast",
#         default_index=0,
#         orientation="horizontal",
#         styles={
#             "container": {"padding": "0!important", "background-color": "#f0f2f6"},
#             "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#eee"},
#             "nav-link-selected": {"background-color": "#04AA6D"},
#         }
#     )

#     # --------------------- KONTEN --------------------- #
#     container = st.container()
#     if selected == "Home":
#         container.subheader("🏠 Selamat datang di Home!")
#         container.write("Ini adalah halaman utama aplikasi reservasi komputer.")
#     elif selected == "Booking":
#         container.subheader("📅 Halaman Booking Komputer")
#         container.write("Di sini user dapat melakukan booking komputer.")
#     elif selected == "Data User":
#         container.subheader("👥 Halaman Data User (Hanya Admin)")
#         container.write("Admin dapat melihat dan mengelola daftar user.")


import streamlit as st
import sqlite3
from datetime import datetime, date, time, timedelta
from streamlit_option_menu import option_menu
import pandas as pd
import calendar


# ------------------ DB SETUP ------------------ #
def get_conn():
    conn = sqlite3.connect("booking.db", check_same_thread=False)
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        computer_name TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING'
    )
    """)

    # user default
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0]==0:
        c.execute("INSERT INTO users (username, password, role) VALUES ('rana','rana','admin')")
        c.execute("INSERT INTO users (username, password, role) VALUES ('bintang','bintang','admin')")
        conn.commit()
    conn.close()

# ------------------ DB SETUP (tambahan untuk ruangan) ------------------ #
def init_db_rooms():
    conn = get_conn()
    c = conn.cursor()
    # Tabel rooms
    c.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_name TEXT UNIQUE NOT NULL
    )
    """)
    # Tabel booking ruangan
    c.execute("""
    CREATE TABLE IF NOT EXISTS room_reservations (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        room_name TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        capacity INTEGER,
        purpose TEXT,
        status TEXT NOT NULL DEFAULT 'PENDING',
        FOREIGN KEY (username) REFERENCES users(username),
        FOREIGN KEY (room_name) REFERENCES rooms(room_name)
    )
    """)
    # Masukkan default rooms kalau kosong
    c.execute("SELECT COUNT(*) FROM rooms")
    if c.fetchone()[0] == 0:
        default_rooms = ['RO3.02.02','RO3.02.06','RO3.02.09','RO3.01.04 (Residensi)']
        for room in default_rooms:
            c.execute("INSERT INTO rooms (room_name) VALUES (?)", (room,))
    conn.commit()
    conn.close()

# Panggil init DB ruangan setelah init_db()
init_db_rooms()


# ------------------ DB ------------------ #
def get_conn():
    return sqlite3.connect("booking.db", check_same_thread=False)

# Ambil data booking
today = datetime.now().date()
one_month = today + timedelta(days=30)

conn = get_conn()
c = conn.cursor()
c.execute("""
    SELECT username, room_name, start_date, end_date
    FROM room_reservations
    WHERE status='APPROVED'
""")
rows = c.fetchall()
conn.close()



# ------------------ RESERVASI & USER FUNCTIONS ------------------ #
def check_login(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username,password))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def create_reservation(username, computer_name, start_date, end_date, start_time, end_time):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO reservations (username, computer_name, start_date, end_date, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, computer_name, start_date, end_date, start_time, end_time))
    conn.commit()
    conn.close()

def get_user_reservations(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, computer_name, start_date, end_date, start_time, end_time, status
        FROM reservations
        WHERE username=?
        ORDER BY start_date
    """, (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_reservations(status_filter=None):
    conn = get_conn()
    c = conn.cursor()
    if status_filter and status_filter!="ALL":
        c.execute("""
            SELECT id, username, computer_name, start_date, end_date, start_time, end_time, status
            FROM reservations WHERE status=? ORDER BY start_date
        """, (status_filter,))
    else:
        c.execute("""
            SELECT id, username, computer_name, start_date, end_date, start_time, end_time, status
            FROM reservations ORDER BY start_date
        """)
    rows = c.fetchall()
    conn.close()
    return rows


def get_available_computers(current_date, current_time):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT computer_name FROM reservations
        WHERE status='APPROVED' AND date(?) BETWEEN date(start_date) AND date(end_date)
        AND time(?) BETWEEN time(start_time) AND time(end_time)
    """, (current_date, current_time))
    booked = [r[0] for r in c.fetchall()]
    conn.close()
    all_computers = ["S2IF-1","S2IF-2","S2IF-5","S2IF-6","S2IF-7","S2IF-8","S2IF-9"]
    return [pc for pc in all_computers if pc not in booked]

def get_available_computers_for_range(start_date, end_date, start_time, end_time):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT computer_name FROM reservations
        WHERE status='APPROVED' AND NOT (
            date(end_date)<date(?) OR date(start_date)>date(?) OR
            time(end_time)<=time(?) OR time(start_time)>=time(?)
        )
    """, (start_date, end_date, start_time, end_time))
    booked = [r[0] for r in c.fetchall()]
    conn.close()
    all_computers = ["S2IF-1","S2IF-2","S2IF-5","S2IF-6","S2IF-7","S2IF-8","S2IF-9"]
    return [pc for pc in all_computers if pc not in booked]

# Tambahkan data spesifikasi komputer
COMPUTER_SPECS = {
    "S2IF-1": "Quadro RTX 6000| 12th Gen Intel(R) Core(TM) i9-12900 3.20 GHz | RAM 32GB",
    "S2IF-2": "RTX 3070 | Intel(R) Core(TM) i7-3770 CPU @ 3.40 GHz | RAM 8GB",
    "S2IF-5": "NVIDIA GeForce GT 430 | Intel(R) Core(TM) i7-3770 CPU @ 3.40 GHz | RAM 8GB",
    "S2IF-6": "NVIDIA GeForce GT 430 | Intel(R) Core(TM) i7-3770 CPU @ 3.40 GHz | RAM 8GB",
    "S2IF-7": "Intel® UHD Graphics 770 | 12th Gen Intel(R) Core(TM) i5-12500 3.00 GHz | RAM 16GB",
    "S2IF-8": "Intel® UHD Graphics 770 | 12th Gen Intel(R) Core(TM) i5-12500 3.00 GHz | RAM 16GB",
    "S2IF-9": "Intel® UHD Graphics 770 | 12th Gen Intel(R) Core(TM) i5-12500 3.00 GHz | RAM 16GB"
}

# Buat dictionary untuk menandai booking per tanggal
booking_dict = {}
for row in rows:
    username, room_name, start_date, end_date = row
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    for single_date in pd.date_range(start_date, end_date):
        d = single_date.date()
        if d >= today and d <= one_month:
            if d not in booking_dict:
                booking_dict[d] = []
            booking_dict[d].append(f"{username} ({room_name})")


# ------------------ FUNGSI RUANGAN ------------------ #
def get_available_rooms_for_range(start_date, end_date, start_time, end_time):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT room_name FROM room_reservations
        WHERE status='APPROVED' AND NOT (
            date(end_date) < date(?) OR date(start_date) > date(?) OR
            time(end_time) <= time(?) OR time(start_time) >= time(?)
        )
    """, (start_date, end_date, start_time, end_time))
    booked = [r[0] for r in c.fetchall()]
    # Ambil semua room
    c.execute("SELECT room_name FROM rooms")
    all_rooms = [r[0] for r in c.fetchall()]
    conn.close()
    return [room for room in all_rooms if room not in booked]

def create_room_reservation(username, room_name, start_date, end_date, start_time, end_time, capacity, purpose):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO room_reservations (username, room_name, start_date, end_date, start_time, end_time, capacity, purpose)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, room_name, start_date, end_date, start_time, end_time, capacity, purpose))
    conn.commit()
    conn.close()

def get_user_room_reservations(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT reservation_id, room_name, start_date, end_date, start_time, end_time, capacity, purpose, status
        FROM room_reservations
        WHERE username=?
        ORDER BY start_date
    """, (username,))
    rows = c.fetchall()
    conn.close()
    return rows


def update_reservation_status(res_id, new_status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE reservations SET status=? WHERE id=?", (new_status,res_id))
    conn.commit()
    conn.close()

def delete_reservation(res_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM reservations WHERE id=?", (res_id,))
    conn.commit()
    conn.close()

def add_user(username,password,role="user"):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",(username,password,role))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def delete_user(username):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM users WHERE username=?",(username,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT username,password,role FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

# ------------------ UI ------------------ #
init_db()
st.set_page_config(page_title="Reservasi Komputer", layout="wide")

# Custom CSS styling
st.markdown("""
    <style>
    .main {
        background-color: #F7F9FC;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .reservation-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid #4C8BF5;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    }
    .status-approved {
        color: #0FA958;
        font-weight: bold;
    }
    .status-pending {
        color: #E5B300;
        font-weight: bold;
    }
    .status-rejected {
        color: #D33A2C;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in=False
    st.session_state.username=None
    st.session_state.role=None

# ---------- LOGIN ----------
if not st.session_state.logged_in:
    st.title("🔒 Tel-U Master's Degree in Informatics Student Residence Reservation System Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        role = check_login(username,password)
        if role:
            st.session_state.logged_in=True
            st.session_state.username=username
            st.session_state.role=role
            st.rerun()
        else:
            st.error("Incorrect username/password")
    st.info("Contact the Admin (Mbak Rana) to register a new user")
    st.warning("This is specifically for the celoe room : https://celoe.telkomuniversity.ac.id/auth")
    st.warning("For Building C, please contact PSAL via : https://tel-u.ac.id/pinjamruangpasca")
    st.warning("If the courtroom at TULT can only be used by employees and lecturers : https://apps-soc.telkomuniversity.ac.id/login")

# ---------- NAVBAR ----------
if st.session_state.logged_in:
    with st.sidebar:
        st.write(f"👤 Login as: {st.session_state.username} ({st.session_state.role})")
        if st.button("Logout"):
            st.session_state.logged_in=False
            st.session_state.username=None
            st.session_state.role=None
            st.rerun()

    menu_options = ["Home", "Computer", "Room"] + (["Data User"] if st.session_state.role=="admin" else [])
    selected = option_menu(
        menu_title=None,
        options=menu_options,
        icons=["house","calendar","calendar","people"],
        default_index=0,
        orientation="horizontal"
    )

    # ------------------ HOME ------------------ #
    if selected=="Home":
        st.title("🏠 Home - Computer Status & One-Month Booking")
        now = datetime.now()
        current_date = now.date().isoformat()
        current_time = now.strftime("%H:%M")
        all_computers = ["S2IF-1","S2IF-2","S2IF-5","S2IF-6","S2IF-7","S2IF-8","S2IF-9"]
        available = get_available_computers(current_date,current_time)
        
        st.subheader("📌 Current Computer Status")
        # status_list = []
        # for pc in all_computers:
        #     status = "AVAILABLE" if pc in available else "NOT AVAILABLE"
        #     status_list.append({"Computer": pc, "Status": status})

        # df_status = pd.DataFrame(status_list)

        # Buat data tabel dengan status dan spesifikasi
        status_data = []
        for pc, spec in COMPUTER_SPECS.items():
            status = "AVAILABLE" if pc in available else "NOT AVAILABLE"
            status_style = (
                "<span style='color:#0FA958;font-weight:bold;'>AVAILABLE</span>"
                if status == "AVAILABLE" else
                "<span style='color:#D33A2C;font-weight:bold;'>NOT AVAILABLE</span>"
            )
            status_data.append([pc, spec, status_style])

        # Tampilkan tabel HTML
        st.markdown("""
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color:#f0f0f0;">
                <th style="padding: 8px;">Komputer</th>
                <th style="padding: 8px;">Status</th>
                <th style="padding: 8px;">Spesifikasi</th>
            </tr>
        """ + "".join([
            f"<tr><td style='padding: 8px;'>{row[0]}</td><td style='padding: 8px;'>{row[1]}</td><td style='padding: 8px;'>{row[2]}</td></tr>"
            for row in status_data
        ]) + "</table>", unsafe_allow_html=True)

        # status_list = []
        # for pc in all_computers:
        #     status = "AVAILABLE" if pc in available else "NOT AVAILABLE"
        #     status_list.append({"Computer": pc, "Status": status})

        # df_status = pd.DataFrame(status_list)

        # # Styling
        # def highlight_status(val):
        #     color = 'green' if val == "AVAILABLE" else 'red'
        #     return f'background-color: {color}; color: white; font-weight: bold'

        # st.dataframe(df_status.style.applymap(highlight_status, subset=['Status']), use_container_width=True)

        st.subheader("📌 Computer Booking Schedule for the Next Month")
        today = datetime.now().date()
        one_month = today+timedelta(days=30)
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT username, computer_name, start_date, end_date, start_time, end_time
            FROM reservations
            WHERE status='APPROVED'
            AND date(start_date)<=date(?)
            AND date(end_date)>=date(?)
            ORDER BY start_date
        """,(one_month,today))
        rows = c.fetchall()
        conn.close()
        if rows:
            st.dataframe(pd.DataFrame(rows,columns=["User","Computer","Start Date","End Date","Start Time","End Time"]), use_container_width=True)
        else:
            st.info("No Computer reservations in the next month.")

        # st.subheader("📌 Room Booking Schedule for the Next Month")

        
        st.subheader("📌 Room Booking Calendar (Next 30 Days)")

        # Buat kalender grid per bulan
        current = today
        while current <= one_month:
            year = current.year
            month = current.month


            st.markdown(f"###  {calendar.month_name[month]} {year}")
            
            # Header hari
            cols = st.columns(7)
            for i, day_name in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
                cols[i].markdown(f"**{day_name}**")
            
            # Tanggal mulai dari Senin
            first_weekday, days_in_month = calendar.monthrange(year, month)
            first_weekday = (first_weekday + 1) % 7  # Ubah Senin=0
            weeks = []
            week = [""]*7
            day = 1
            for i in range(first_weekday, 7):
                week[i] = day
                day +=1
            weeks.append(week)
            
            while day <= days_in_month:
                week = [""]*7
                for i in range(7):
                    if day <= days_in_month:
                        week[i] = day
                        day +=1
                weeks.append(week)
            
            # Tampilkan grid
            for week in weeks:
                cols = st.columns(7)
                for i, day_num in enumerate(week):
                    if day_num == "":
                        cols[i].markdown(" ")
                    else:
                        dt = date(year, month, day_num)
                        if dt in booking_dict:
                            # Jika dibooking, beri warna dan tampilkan info
                            info = "\n".join(booking_dict[dt])
                            cols[i].markdown(
                                f"<div style='background-color:#42c792; padding:10px; border-radius:5px;'>"
                                f"<b>{day_num}</b><br>{info}</div>",
                                unsafe_allow_html=True
                            )
                        else:
                            # Jika kosong
                            cols[i].markdown(f"{day_num}")
            
            # Lanjut ke bulan berikutnya
            if month == 12:
                current = date(year+1,1,1)
            else:
                current = date(year, month+1, 1)

        # today = datetime.now().date()
        # one_month = today+timedelta(days=30)
        # conn = get_conn()
        # c = conn.cursor()
        # c.execute("""
        #     SELECT username, room_name, start_date, end_date, start_time, end_time
        #     FROM room_reservations
        #     WHERE status='APPROVED'
        #     AND date(start_date)<=date(?)
        #     AND date(end_date)>=date(?)
        #     ORDER BY start_date
        # """,(one_month,today))
        # rows = c.fetchall()
        # conn.close()
        # if rows:
        #     st.dataframe(pd.DataFrame(rows,columns=["User","Room","Start Date","End Date","Start Time","End Time"]), use_container_width=True)
        # else:
        #     st.info("No Room reservations in the next month.")

    # ------------------ BOOKING (User) ------------------ #
    elif selected=="Computer":
        st.title("📅 Reservation Computer")
        if st.session_state.role!="user" and st.session_state.role!="admin":
            st.warning("Only users or administrators can make Reservations.")
        else:
            col1,col2 = st.columns(2)
            with col1:
                tanggal_range = st.date_input("Select date range (start-end)", value=(date.today(),date.today()))
                jam_mulai = st.time_input("Start Time", value=time(0,0))
            with col2:
                jam_selesai = st.time_input("End Time", value=time(23,59))
                if isinstance(tanggal_range,(list,tuple)) and len(tanggal_range)==2:
                    start_date,end_date = tanggal_range
                    available_computers = get_available_computers_for_range(
                        start_date.isoformat(),end_date.isoformat(),
                        jam_mulai.strftime("%H:%M"), jam_selesai.strftime("%H:%M")
                    )
                else:
                    st.warning("Select start and end dates")
                    st.stop()
                computer_name = st.selectbox("Select Computer", available_computers)
            if st.button("Submit Reservation"):
                create_reservation(st.session_state.username, computer_name,
                                   start_date.isoformat(), end_date.isoformat(),
                                   jam_mulai.strftime("%H:%M"), jam_selesai.strftime("%H:%M"))
                st.success("Reservation submitted. Awaiting admin approval.")

            # # Tampilkan reservasi
            # st.subheader("Computer Reservations")
            # if st.session_state.role=="user":
            #     rows = get_user_reservations(st.session_state.username)
            # elif st.session_state.role=="admin":
            #     rows = get_all_reservations()  # Admin lihat semua
            # else:
            #     rows = []
            
            # if rows:
            #     # <-- Ganti baris ini dengan versi aman:
            #     n_cols = len(rows[0])
            #     if n_cols == 8:
            #         columns = ["ID","User","Computer","Start Date","End Date","Start Time","End Time","Status"]
            #     elif n_cols == 7:
            #         columns = ["ID","Computer","Start Date","End Date","Start Time","End Time","Status"]
            #     else:
            #         st.error(f"Unexpected number of columns: {n_cols}")
            #         st.stop()
            #     df_user = pd.DataFrame(rows, columns=columns)
            #     st.dataframe(df_user,use_container_width=True)
                
            #     # Untuk admin, tombol Approve / Reject
            #     if st.session_state.role=="admin":
            #         st.subheader("Approve/Reject Action")
            #         for r in rows:
            #             rid,status = r[0], r[7]
            #             col1,col2,col3 = st.columns([4,1,1])
            #             with col1:
            #                 st.write(f"ID: {rid} | User: {r[1]} | Status: {status}")
            #             with col2:
            #                 if status!="APPROVED":
            #                     if st.button("✔ APPROVE", key=f"a{rid}"):
            #                         update_reservation_status(rid,"APPROVED")
            #                         st.success("Booking approved")
            #                         st.rerun()
            #                 if status!="REJECTED":
            #                     if st.button("✖ REJECT", key=f"r{rid}"):
            #                         update_reservation_status(rid,"REJECTED")
            #                         st.warning("Booking rejected")
            #                         st.rerun()
            #             with col3:
            #                 if st.button("🗑 HAPUS", key=f"rh{rid}"):
            #                     conn = get_conn()
            #                     c = conn.cursor()
            #                     c.execute("DELETE FROM reservations WHERE id=?", (rid,))
            #                     conn.commit()
            #                     conn.close()
            #                     st.error("Computer booking deleted")
            #                     st.rerun()
            # else:
            #     st.info("No reservations yet.")
            # Tampilkan reservasi
            # Tampilkan reservasi
            st.subheader("Computer Reservations")

            # Pastikan computer_name ada di session_state
            if "computer_name" not in st.session_state:
                st.session_state["computer_name"] = computer_name  # assign nilai default

            # Ambil semua reservasi
            all_rows = get_all_reservations()

            # Filter per komputer
            # comp_rows = [r for r in all_rows if r[2] == st.session_state["computer_name"]] if st.session_state["computer_name"] else all_rows
            comp_rows = [r for r in all_rows if r[2] == st.session_state["computer_name"]]


            if comp_rows:
                for r in comp_rows:
                    rid, uname, comp, sdate, edate, stime, etime, status = r
                    status_label = "🟢 Approved" if status=="APPROVED" else ("🟡 Pending" if status=="PENDING" else "🔴 Rejected")
                    st.markdown(f"""
                    <div class="reservation-card">
                        <strong>Reservasi #{rid}</strong><br>
                        📌 User: {uname} <br>
                        🖥 Komputer: {comp}<br>
                        📅 {sdate} → {edate}<br>
                        ⏱ {stime} - {etime} <br><br>
                        {status_label}
                    </div>
                    """, unsafe_allow_html=True)

                # Tombol admin
                if st.session_state.role == "admin":
                    for r in all_rows:
                        rid, uname, comp, sdate, edate, stime, etime, status = r
                        col1, col2, col3 = st.columns([4,1,1])
                        with col1:
                            st.write(f"ID: {rid} | User: {uname} | Computer: {comp} | Status: {status}")
                        with col2:
                            if status != "APPROVED" and st.button("✔ APPROVE", key=f"a{rid}"):
                                update_reservation_status(rid, "APPROVED")
                                st.success("Booking approved")
                                st.rerun()
                            if status != "REJECTED" and st.button("✖ REJECT", key=f"r{rid}"):
                                update_reservation_status(rid, "REJECTED")
                                st.warning("Booking rejected")
                                st.rerun()
                        with col3:
                            if st.button("🗑 HAPUS", key=f"d{rid}"):
                                conn = get_conn()
                                c = conn.cursor()
                                c.execute("DELETE FROM reservations WHERE id=?", (rid,))
                                conn.commit()
                                conn.close()
                                st.error("Computer booking deleted")
                                st.rerun()
            else:
                st.info("No reservations yet.")

            st.markdown("---")

            if st.session_state.role=="user":
                rows = get_user_reservations(st.session_state.username)
            elif st.session_state.role=="admin":
                rows = get_all_reservations()  # Admin lihat semua
            else:
                rows = []
            
            if rows:
                # <-- Ganti baris ini dengan versi aman:
                n_cols = len(rows[0])
                if n_cols == 8:
                    columns = ["ID","User","Computer","Start Date","End Date","Start Time","End Time","Status"]
                elif n_cols == 7:
                    columns = ["ID","Computer","Start Date","End Date","Start Time","End Time","Status"]
                else:
                    st.error(f"Unexpected number of columns: {n_cols}")
                    st.stop()
                df_user = pd.DataFrame(rows, columns=columns)
                st.dataframe(df_user,use_container_width=True)
                



    # ------------------ BOOKING (User) ------------------ #
    elif selected=="Room":
        st.title("📅 Reservation Room")
        
        # Cek role
        if st.session_state.role not in ["user","admin"]:
            st.warning("Only users or administrators can make Reservations.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                tanggal_range = st.date_input("Select date range (start-end)", value=(date.today(), date.today()))
                jam_mulai = st.time_input("Start Time", value=time(0,0))
                purpose = st.text_input("Keperluan penggunaan ruangan (misal: sidang tesis)")
            with col2:
                jam_selesai = st.time_input("End Time", value=time(23,59))
                # *** Tambahan baru disini ***
                capacity = st.number_input("Jumlah peserta (kapasitas max 25 orang)", min_value=1, value=5)
                # purpose = st.text_input("Keperluan penggunaan ruangan (misal: sidang tesis)")
                # *** sampai sini ***


                # Ambil daftar ruangan yang tersedia
                if isinstance(tanggal_range, (list, tuple)) and len(tanggal_range) == 2:
                    start_date, end_date = tanggal_range
                    available_rooms = get_available_rooms_for_range(
                        start_date.isoformat(), end_date.isoformat(),
                        jam_mulai.strftime("%H:%M"), jam_selesai.strftime("%H:%M")
                    )
                else:
                    st.warning("Select start and end dates")
                    st.stop()
                
                room_name = st.selectbox("Select Room", available_rooms)
            
            
            
            # # Tombol submit booking
            # if st.button("Submit Reservation"):
            #     create_room_reservation(
            #         st.session_state.username, room_name,
            #         start_date.isoformat(), end_date.isoformat(),
            #         jam_mulai.strftime("%H:%M"), jam_selesai.strftime("%H:%M")
            #     )
            #     st.success("Room reservations submitted. Awaiting admin approval.")

            if st.button("Book Room"):
                create_room_reservation(
                    st.session_state.username,
                    room_name,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    jam_mulai.strftime("%H:%M"),
                    jam_selesai.strftime("%H:%M"),
                    capacity,
                    purpose
                )
                st.success("Room reservation requested successfully!")
            
            # Tampilkan reservasi user
            st.subheader("Reservation Room")
            if st.session_state.role=="user":
                rows = get_user_room_reservations(st.session_state.username)
            elif st.session_state.role=="admin":
                conn = get_conn()
                c = conn.cursor()
                c.execute("""
                    SELECT reservation_id, username, room_name, start_date, end_date, start_time, end_time, capacity, purpose, status
                    FROM room_reservations
                    ORDER BY start_date
                """)
                rows = c.fetchall()
                conn.close()

            else:
                rows = []

            # if rows:
            #     df_user = pd.DataFrame(rows, columns=["ID","User","Ruangan","Start","End","Jam Mulai","Jam Selesai","Status"])
            #     st.dataframe(df_user,use_container_width=True)
            # Tampilkan reservasi user / admin
            if rows:
                n_cols = len(rows[0])
                if n_cols == 10:
                    columns = ["ID","User","Room","Start Date","End Date","Start Time","End Time","Capacity","Purpose","Status"]
                elif n_cols == 9:
                    columns=["ID","Room","Start Date","End Date","Start Time","End Time","Capacity","Purpose","Status"]
                else:
                    st.error(f"Unexpected number of columns: {n_cols}")
                    st.stop()
                df_user = pd.DataFrame(rows, columns=columns)
                st.dataframe(df_user,use_container_width=True)

                
                if st.session_state.role=="admin":
                    st.subheader("Approve / Reject Action")
                    for r in rows:
                        rid = r[0]
                        status = r[9]  # index status yang benar

                        col1,col2,col3 = st.columns([4,1,1])

                        with col1:
                            st.write(f"ID: {rid} | User: {r[1]} | Status: {status}")

                        with col2:
                            if status != "APPROVED":
                                if st.button("✔ APPROVE", key=f"ra{rid}"):
                                    conn = get_conn()
                                    c = conn.cursor()
                                    c.execute("UPDATE room_reservations SET status='APPROVED' WHERE reservation_id=?", (rid,))
                                    conn.commit()
                                    conn.close()
                                    st.success("Room reservation approved")
                                    st.rerun()

                            if status != "REJECTED":
                                if st.button("✖ REJECT", key=f"rr{rid}"):
                                    conn = get_conn()
                                    c = conn.cursor()
                                    c.execute("UPDATE room_reservations SET status='REJECTED' WHERE reservation_id=?", (rid,))
                                    conn.commit()
                                    conn.close()
                                    st.warning("Room reservation rejected")
                                    st.rerun()

                        with col3:
                            if st.button("🗑 HAPUS", key=f"rh{rid}"):
                                conn = get_conn()
                                c = conn.cursor()
                                c.execute("DELETE FROM room_reservations WHERE reservation_id=?", (rid,))
                                conn.commit()
                                conn.close()
                                st.error("Room reservation canceled")
                                st.rerun()

            else:
                st.info("No room reservations yet.")


    # ------------------ DATA USER / ADMIN ------------------ #
    elif selected=="Data User" and st.session_state.role=="admin":
        st.title("👥 Data User & Admin ")

        st.write("Add New User")
        new_user=st.text_input("Username")
        new_pass=st.text_input("Password",type="password")
        if st.button("Add New User"):
            if add_user(new_user,new_pass):
                st.success("User has been successfully added.")
                st.rerun()
            else:
                st.error("Failed, the username may already exist")

        st.subheader("Kelola User")
        users = get_all_users()
        df_users=pd.DataFrame(users,columns=["Username","Password","Role"])
        st.dataframe(df_users,use_container_width=True)
        
        # Tombol hapus user
        st.subheader("Delete User")
        for u in users:
            username = u[0]
            role = u[2]

            col1, col2 = st.columns([4,1])
            with col1:
                st.write(f"Username: {username} | Role: {role}")
            with col2:
                if role != "admin":  # admin tidak bisa dihapus
                    if st.button("🗑 Hapus", key=f"del_{username}"):
                        conn = get_conn()
                        c = conn.cursor()
                        c.execute("DELETE FROM users WHERE username=?", (username,))
                        conn.commit()
                        conn.close()
                        st.error(f"User '{username}' berhasil dihapus!")
                        st.rerun()
                else:
                    st.write("❌")


        st.title("👥 Approve Booking")
        st.subheader("All Reservations")
        rows = get_all_reservations()
        if rows:
            df_all=pd.DataFrame(rows,columns=["ID","User","Komputer","Start","End","Jam Mulai","Jam Selesai","Status"])
            st.dataframe(df_all,use_container_width=True)
        else:
            st.info("No data reservations yet")



