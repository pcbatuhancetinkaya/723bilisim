from flask import Flask, render_template, request, send_file
from fpdf import FPDF
from datetime import datetime
import os

app = Flask(__name__)

# --- PDF SINIFI YAPILANDIRMASI ---
class DijitalServisFormu(FPDF):
    def header(self):
        logo_yolu = '723_bilisim_hizmetleri_highres.png'
        if os.path.exists(logo_yolu):
            self.image(logo_yolu, 10, 8, 30)
            
        self.set_font('Arial', 'B', 16) # Not: Sistem fontu Arial olarak basitleştirildi
        self.set_text_color(20, 40, 80)
        self.cell(40)
        self.cell(0, 10, '7/23 BILISIM HIZMETLERI', border=False, ln=1, align='L')
        
        self.cell(40)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Profesyonel Teknik Servis & Onarim Formu', border=False, ln=1, align='L')
        self.ln(15)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(34, 139, 34)
        mesaj = ("Bu belge dogayi korumak ve kagit israfini onlemek adina dijital olarak uretilmistir.")
        self.multi_cell(0, 5, mesaj, align='C')
        
        self.set_y(-15)
        self.set_text_color(128)
        self.cell(0, 10, f'Sayfa {self.page_no()}', align='C')

# --- WEB ROTALARI ---

@app.route('/')
def ana_sayfa():
    return render_template('index.html')

@app.route('/hizmetler')
def hizmetler():
    return render_template('hizmetler.html')

@app.route('/blog')
def blog_ana_sayfa():
    return render_template('blog.html')

@app.route('/blog/ssd-yukseltme')
def blog_ssd():
    return render_template('blog_ssd.html')

@app.route('/blog/periyodik-bakim')
def blog_bakim():
    return render_template('blog_bakim.html')

@app.route('/blog/ram-yukseltme')
def blog_ram():
    return render_template('blog_ram.html')

# --- RANDEVU VE PDF İŞLEMLERİ ---

@app.route('/randevu-al', methods=['POST'])
def randevu_al():
    bilgiler = {
        "ad": request.form.get('ad'),
        "tel": request.form.get('tel'),
        "adres": request.form.get('adres'),
        "marka": request.form.get('marka'),
        "model": request.form.get('model'),
        "detay": request.form.get('detay')
    }

    # PDF Yapılandırması
    pdf = DijitalServisFormu()
    # Vercel'deki font yollarını kontrol edin
    try:
        pdf.add_font('TurkishArial', '', "arial.ttf", unicode=True)
        pdf.set_font('TurkishArial', '', 11)
    except:
        pdf.set_font('Arial', '', 11)
    
    pdf.add_page()
    pdf.set_fill_color(240, 240, 240)
    tarih_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    pdf.cell(0, 10, f"Servis Kayit Tarihi: {tarih_str}", ln=1, fill=True)
    pdf.ln(5)

    pdf.cell(0, 10, f"Musteri: {bilgiler['ad']}", ln=1)
    pdf.cell(0, 10, f"Cihaz: {bilgiler['marka']} {bilgiler['model']}", ln=1)
    pdf.multi_cell(0, 10, f"Ariza Detayi: {bilgiler['detay']}")

    dosya_adi = f"723_Servis_Formu_{bilgiler['ad'].replace(' ', '_')}.pdf"
    output_path = os.path.join('/tmp', dosya_adi)
    pdf.output(output_path)
    
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
