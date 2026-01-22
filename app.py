from flask import Flask, render_template, request, send_file
from fpdf import FPDF
from datetime import datetime
import os

app = Flask(__name__)

# --- PDF SINIFI YAPILANDIRMASI ---
class DijitalServisFormu(FPDF):
    def header(self):
        # Logo dosyasının GitHub ana dizininde olduğundan emin ol
        # Not: Önceki sürümde .jpg olan dosya adını koduna göre .png olarak güncelledim
        logo_yolu = '723_bilisim_hizmetleri_highres.png'
        if os.path.exists(logo_yolu):
            self.image(logo_yolu, 10, 8, 30)
            
        # Başlık Bölümü (TurkishArial Fontu Kullanılır)
        self.set_font('TurkishArial', 'B', 16)
        self.set_text_color(20, 40, 80) # Kurumsal Lacivert
        self.cell(40) # Logo boşluğu
        self.cell(0, 10, '7/23 BİLİŞİM HİZMETLERİ', border=False, ln=1, align='L')
        
        self.cell(40)
        self.set_font('TurkishArial', 'I', 10)
        self.cell(0, 10, 'Profesyonel Teknik Servis & Onarım Formu', border=False, ln=1, align='L')
        self.ln(15)

    def footer(self):
        # Sayfa Altı Çevreci Mesaj
        self.set_y(-30)
        self.set_font('TurkishArial', 'I', 8)
        self.set_text_color(34, 139, 34) # Doğa dostu yeşil
        mesaj = ("Bu belge doğayı korumak ve kağıt israfını önlemek adına dijital olarak üretilmiştir. "
                 "7/23 Bilişim Hizmetleri olarak sürdürülebilirliği destekliyoruz.")
        self.multi_cell(0, 5, mesaj, align='C')
        
        self.set_y(-15)
        self.set_text_color(128)
        self.cell(0, 10, f'Sayfa {self.page_no()}', align='C')

# --- WEB ROTALARI ---

@app.route('/')
def ana_sayfa():
    # templates/index.html dosyasının varlığına dikkat edilmeli
    return render_template('index.html')

@app.route('/hizmetler')
def hizmetler():
    # Yeni oluşturduğumuz templates/hizmetler.html sayfasına yönlendirir
    return render_template('hizmetler.html')

@app.route('/blog')
def blog():
    # İleride ekleyeceğimiz blog yazıları için hazır alan
    return render_template('blog.html')

@app.route('/randevu-al', methods=['POST'])
def randevu_al():
    # Form verilerini yakalama
    bilgiler = {
        "ad": request.form.get('ad'),
        "tel": request.form.get('tel'),
        "adres": request.form.get('adres'),
        "marka": request.form.get('marka'),
        "model": request.form.get('model'),
        "detay": request.form.get('detay')
    }

    # PDF Nesnesi ve Fontlar (Vercel uyumu için .ttf uzantıları gereklidir)
    pdf = DijitalServisFormu()
    # Fontların GitHub'da .ttf uzantısıyla mevcut olduğundan emin olun
    pdf.add_font('TurkishArial', '', "arial.ttf")
    pdf.add_font('TurkishArial', 'B', "arialbd.ttf")
    pdf.add_font('TurkishArial', 'I', "ariali.ttf")
    
    pdf.add_page()
    pdf.set_font('TurkishArial', '', 11)

    # İçerik Bölümü: Tarih ve Bilgiler
    pdf.set_fill_color(240, 240, 240)
    tarih_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    pdf.cell(0, 10, f"Servis Kayıt Tarihi: {tarih_str}", ln=1, fill=True)
    pdf.ln(5)

    pdf.set_font('TurkishArial', 'B', 12)
    pdf.cell(0, 10, "Müşteri Bilgileri", ln=1)
    pdf.set_font('TurkishArial', '', 11)
    pdf.multi_cell(0, 8, f"Ad Soyad: {bilgiler['ad']}\nTelefon: {bilgiler['tel']}\nAdres: {bilgiler['adres']}")
    
    pdf.ln(5)
    
    pdf.set_font('TurkishArial', 'B', 12)
    pdf.cell(0, 10, "Teknik Servis Detayları", ln=1)
    pdf.set_font('TurkishArial', '', 11)
    detay_metni = (f"Cihaz Marka: {bilgiler['marka']}\n"
                   f"Cihaz Model: {bilgiler['model']}\n\n"
                   f"Arıza & Talep Detayı:\n{bilgiler['detay']}")
    pdf.multi_cell(0, 8, detay_metni)
    
    pdf.ln(10)
    pdf.set_font('TurkishArial', 'B', 10)
    pdf.set_text_color(20, 40, 80)
    pdf.cell(0, 10, "Bu belge 7/23 Bilişim Hizmetleri tarafından dijital olarak onaylanmıştır.", ln=1, align='C')

    # --- VERCEL İÇİN KRİTİK DOSYA YOLU ---
    # Vercel sadece /tmp klasörüne yazma izni verir
    dosya_adi = f"723_Servis_Formu_{bilgiler['ad'].replace(' ', '_')}.pdf"
    output_path = os.path.join('/tmp', dosya_adi)
    
    pdf.output(output_path)
    
    # Oluşturulan dosyayı tarayıcıya gönder
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
