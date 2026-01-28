from flask import Flask, render_template, request, send_file, session, redirect, url_for, flash
from fpdf import FPDF
from datetime import datetime
import os
import sqlite3
import psycopg2  # PostgreSQL için eklendi
from psycopg2 import extras
import tempfile

app = Flask(__name__)
app.secret_key = '723_bilisim_ozel_anahtar_99'
ADMIN_PASSWORD = "admin723_elazig"

# --- AKILLI DOSYA VE VERİTABANI AYARLARI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Vercel'de tanımladığın DATABASE_URL'i kontrol eder
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        # PostgreSQL (Vercel/Supabase) bağlantısı
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        # Yerel SQLite bağlantısı
        conn = sqlite3.connect(os.path.join(BASE_DIR, 'teknik_servis.db'))
        conn.row_factory = sqlite3.Row
        return conn

def veritabani_hazirla():
    conn = get_db_connection()
    cur = conn.cursor()
    if DATABASE_URL:
        # PostgreSQL uyumlu tablo yapısı
        cur.execute('''CREATE TABLE IF NOT EXISTS randevular
                     (id SERIAL PRIMARY KEY, 
                      ad TEXT, tel TEXT, adres TEXT, 
                      marka TEXT, model TEXT, detay TEXT, 
                      tarih TEXT)''')
    else:
        # SQLite uyumlu tablo yapısı
        cur.execute('''CREATE TABLE IF NOT EXISTS randevular
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      ad TEXT, tel TEXT, adres TEXT, 
                      marka TEXT, model TEXT, detay TEXT, 
                      tarih TEXT)''')
    conn.commit()
    cur.close()
    conn.close()

# Logo ve Font Ayarları (Eski çalışan yapın korunmuştur)
LOGO_NAME = '723_bilisim_hizmetleri_highres.jpeg'
LOGO_PATH = os.path.join(BASE_DIR, 'static', 'images', LOGO_NAME)
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = os.path.join(BASE_DIR, LOGO_NAME)

FONT_PATH = os.path.join(BASE_DIR, 'DejaVuSans.ttf')

try:
    veritabani_hazirla()
except Exception as e:
    print(f"DB Hatasi: {e}")

# --- PDF MOTORU ---
class DijitalServisFormu(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH):
            try: self.image(LOGO_PATH, 10, 8, 33)
            except: pass
        self.set_font('Arial', 'B', 15)
        self.set_text_color(20, 40, 80)
        self.cell(45)
        self.cell(0, 10, '7/23 BILISIM HIZMETLERI', ln=1, align='L')
        self.ln(15)

# --- ROTALAR ---
@app.route('/')
def ana_sayfa(): return render_template('index.html')

@app.route('/hizmetler')
def hizmetler(): return render_template('hizmetler.html')

@app.route('/blog')
def blog_ana_sayfa(): return render_template('blog.html')

@app.route('/blog/ssd-yukseltme')
def blog_ssd(): return render_template('blog_ssd.html')

@app.route('/blog/periyodik-bakim')
def blog_bakim(): return render_template('blog_bakim.html')

@app.route('/blog/ram-yukseltme')
def blog_ram(): return render_template('blog_ram.html')

@app.route('/blog/sivi-temasi')
def blog_sivi_temasi(): return render_template('blog_sivi_temasi.html')

@app.route('/blog/ekran-degisimi')
def blog_ekran(): return render_template('blog_ekran.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_paneli'))
        flash('Şifre hatalı!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('ana_sayfa'))

@app.route('/servis-yonetim')
def admin_paneli():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    # PostgreSQL için DictCursor kullanarak SQLite.Row davranışını taklit ediyoruz
    cur = conn.cursor(cursor_factory=extras.RealDictCursor) if DATABASE_URL else conn.cursor()
    
    query = "SELECT id, ad, tel, tarih FROM randevular ORDER BY id DESC"
    if DATABASE_URL:
        cur.execute(query)
        randevular = cur.fetchall()
    else:
        randevular = conn.execute(query).fetchall()
    
    cur.close()
    conn.close()
    return render_template('admin.html', randevular=randevular)

@app.route('/servis-detay/<int:id>')
def servis_detay(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=extras.RealDictCursor) if DATABASE_URL else conn.cursor()
    
    if DATABASE_URL:
        cur.execute("SELECT * FROM randevular WHERE id = %s", (id,))
        r = cur.fetchone()
    else:
        r = conn.execute("SELECT * FROM randevular WHERE id = ?", (id,)).fetchone()
    
    cur.close()
    conn.close()
    if r is None:
        flash('Kayıt bulunamadı!', 'danger')
        return redirect(url_for('admin_paneli'))
    return render_template('detay.html', r=r)

@app.route('/randevu-al', methods=['POST'])
def randevu_al():
    try:
        f = request.form
        tarih_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        conn = get_db_connection()
        cur = conn.cursor()
        
        # SQL yer tutucuları (Postgres: %s, SQLite: ?)
        placeholder = "%s" if DATABASE_URL else "?"
        query = f"INSERT INTO randevular (ad, tel, adres, marka, model, detay, tarih) VALUES ({','.join([placeholder]*7)})"
        
        cur.execute(query, (f['ad'], f['tel'], f['adres'], f['marka'], f['model'], f['detay'], tarih_str))
        conn.commit()
        cur.close()
        conn.close()

        # PDF Oluşturma Bölümü (Aynı kaldı)
        pdf = DijitalServisFormu()
        pdf.add_page()
        if os.path.exists(FONT_PATH):
            pdf.add_font('DejaVu', '', FONT_PATH, uni=True)
            pdf.set_font('DejaVu', '', 11)
        else: pdf.set_font('Arial', '', 11)

        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, f" Kayit Tarihi: {tarih_str} ", ln=1, fill=True)
        pdf.ln(5)
        pdf.multi_cell(0, 8, f"Müşteri: {f['ad']}\nTelefon: {f['tel']}\nCihaz: {f['marka']} {f['model']}\nArıza: {f['detay']}")

        dosya_adi = f"servis_formu_{datetime.now().strftime('%H%M%S')}.pdf"
        cikti_yolu = os.path.join(tempfile.gettempdir(), dosya_adi)
        pdf.output(cikti_yolu)
        return send_file(cikti_yolu, as_attachment=True)

    except Exception as e:
        print(f"Hata: {e}")
        return f"Bir hata oluştu: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
