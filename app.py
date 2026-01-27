from flask import Flask, render_template, request, send_file, session, redirect, url_for, flash
from fpdf import FPDF
from datetime import datetime
import os
import sqlite3
import tempfile

app = Flask(__name__)
app.secret_key = '723_bilisim_ozel_anahtar_99'
ADMIN_PASSWORD = "admin723_elazig"

# --- AKILLI DOSYA YOLU AYARLARI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Veritabanı Yolu: Vercel'de ise /tmp, yerelde ise proje klasörünü kullanır
if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/teknik_servis.db'
else:
    DB_PATH = os.path.join(BASE_DIR, 'teknik_servis.db')

# 2. Logo Yolu: Önce static/images içinde arar, bulamazsa ana dizine bakar
LOGO_NAME = '723_bilisim_hizmetleri_highres.jpeg'
LOGO_PATH = os.path.join(BASE_DIR, 'static', 'images', LOGO_NAME)

if not os.path.exists(LOGO_PATH):
    LOGO_PATH = os.path.join(BASE_DIR, LOGO_NAME)

FONT_PATH = os.path.join(BASE_DIR, 'DejaVuSans.ttf')

# --- VERİTABANI MOTORU ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def veritabani_hazirla():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS randevular
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      ad TEXT, tel TEXT, adres TEXT, 
                      marka TEXT, model TEXT, detay TEXT, 
                      tarih TEXT)''')
        conn.commit()

# Uygulama başlarken veritabanını kontrol et
try:
    veritabani_hazirla()
except Exception as e:
    print(f"DB Hatasi: {e}")

# --- PDF MOTORU ---
class DijitalServisFormu(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH):
            try:
                self.image(LOGO_PATH, 10, 8, 33)
            except:
                pass
        
        self.set_font('Arial', 'B', 15)
        self.set_text_color(20, 40, 80)
        self.cell(45)
        self.cell(0, 10, '7/23 BILISIM HIZMETLERI', ln=1, align='L')
        self.cell(45)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, 'Teknik Servis Onarim Formu', ln=1, align='L')
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
    with get_db_connection() as conn:
        randevular = conn.execute("SELECT id, ad, tel, tarih FROM randevular ORDER BY id DESC").fetchall()
    return render_template('admin.html', randevular=randevular)

@app.route('/servis-detay/<int:id>')
def servis_detay(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    with get_db_connection() as conn:
        randevu = conn.execute("SELECT * FROM randevular WHERE id = ?", (id,)).fetchone()
    if randevu is None:
        flash('Kayıt bulunamadı!', 'danger')
        return redirect(url_for('admin_paneli'))
    return render_template('detay.html', r=randevu)

@app.route('/randevu-al', methods=['POST'])
def randevu_al():
    try:
        f = request.form
        tarih_str = datetime.now().strftime('%d/%m/%Y %H:%M')

        with get_db_connection() as conn:
            conn.execute("""INSERT INTO randevular (ad, tel, adres, marka, model, detay, tarih) 
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                         (f['ad'], f['tel'], f['adres'], f['marka'], f['model'], f['detay'], tarih_str))
            conn.commit()

        pdf = DijitalServisFormu()
        pdf.add_page()

        if os.path.exists(FONT_PATH):
            pdf.add_font('DejaVu', '', FONT_PATH, uni=True)
            pdf.set_font('DejaVu', '', 11)
        else:
            pdf.set_font('Arial', '', 11)

        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, f" Kayit Tarihi: {tarih_str} ", ln=1, fill=True)
        pdf.ln(5)

        icerik = (
            f"Müşteri: {f['ad']}\nTelefon: {f['tel']}\n\n"
            f"--- CİHAZ BİLGİLERİ ---\nMarka: {f['marka']}\nModel: {f['model']}\n\n"
            f"--- ARIZA DETAYI ---\n{f['detay']}\n\n"
            f"--- MÜŞTERİ ADRESİ ---\n{f['adres']}"
        )
        pdf.multi_cell(0, 8, icerik)

        dosya_adi = f"servis_formu_{datetime.now().strftime('%H%M%S')}.pdf"
        cikti_yolu = os.path.join(tempfile.gettempdir(), dosya_adi)
        pdf.output(cikti_yolu)
        
        return send_file(cikti_yolu, as_attachment=True)

    except Exception as e:
        print(f"Hata: {e}")
        return f"Bir hata oluştu: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
