from flask import Flask, render_template, request, send_file
from fpdf import FPDF
from datetime import datetime
import os

app = Flask(__name__)

# --- PDF SINIFI YAPILANDIRMASI ---
class DijitalServisFormu(FPDF):
    def header(self):
        # Logo Dosyası Kontrolü
        logo_yolu = '723_bilisim_hizmetleri_highres.png'
        if os.path.exists(logo_yolu):
            self.image(logo_yolu, 10, 8, 30)
            
        # Başlık Bölümü
        self.set_font('TurkishArial', 'B', 16)
        self.set_text_color(20, 40, 80) # Kurumsal Lacivert
        self.cell(40) # Logo için boşluk
        self.cell(0, 10, '7/23 BİLİŞİM HİZMETLERİ', border=False, ln=1, align='L')
        
        # Alt Başlık
        self.cell(40)
        self.set_font('TurkishArial', 'I', 10)
        self.cell(0, 10, 'Profesyonel Teknik Servis & Onarım Formu', border=False, ln=1, align='L')
        self.ln(15)

    def footer(self):
        # Sayfa Altı Çevreci Mesaj ve Sayfa Numarası
        self.set_y(-30)
        self.set_font('TurkishArial', 'I', 8)
        self.set_text_color(34, 139, 34) # Çevreci Yeşil
        mesaj = ("Bu belge doğayı korumak ve kağıt israfını önlemek adına dijital olarak üretilmiştir. "
                 "7/23 Bilişim Hizmetleri olarak sürdürülebilirliği destekliyoruz.")
        self.multi_cell(0, 5, mesaj, align='C')
        
        self.set_y(-15)
        self.set_text_color(128)
        self.cell(0, 10, f'Sayfa {self.page_no()}', align='C')

# --- WEB ROTALARI ---

@app.route('/')
def ana_sayfa():
    return render_template('index.html')

@app.route('/randevu-al', methods=['POST'])
def randevu_al():
    # Formdan Gelen Verileri Yakalama
    bilgiler = {
        "ad": request.form.get('ad'),
        "tel": request.form.get('tel'),
        "adres": request.form.get('adres'),
        "marka": request.form.get('marka'),
        "model": request.form.get('model'),
        "detay": request.form.get('detay')
    }

    # PDF Nesnesi ve Font Tanımlamaları
    # Vercel (Linux) üzerinde çalışması için yerel font dosyalarını kullanıyoruz
    pdf = DijitalServisFormu()
    pdf.add_font('TurkishArial', '', "arial.ttf")
    pdf.add_font('TurkishArial', 'B', "arialbd.ttf")
    pdf.add_font('TurkishArial', 'I', "ariali.ttf")
    
    pdf.add_page()
    pdf.set_font('TurkishArial', '', 12)

    # 1. Bölüm: Tarih ve Servis No
    pdf.set_fill_color(240, 240, 240)
    tarih_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    servis_no = datetime.now().strftime('%Y%m%d') + "-001"
    
    pdf.cell(0, 10, f"Tarih: {tarih_str}", ln=1, fill=True)
    pdf.cell(0, 10, f"Servis Kayıt No: {servis_no}", ln=1)
    pdf.ln(5)

    # 2. Bölüm: Müşteri Bilgileri
    pdf.set_font('TurkishArial', 'B', 12)
    pdf.cell(0, 10, "Müşteri ve İletişim Bilgileri", ln=1)
    pdf.set_font('TurkishArial', '', 11)
    pdf.multi_cell(0, 8, f"Ad Soyad: {bilgiler['ad']}\nTelefon: {bilgiler['tel']}\nAdres: {bilgiler['adres']}")
    pdf.ln(5)

    # 3. Bölüm: Cihaz ve Arıza Detayları
    pdf.set_font('TurkishArial', 'B', 12)
    pdf.cell(0, 10, "Cihaz ve Arıza Detayları", ln=1)
    pdf.set_font('TurkishArial', '', 11)
    cihaz_metni = (f"Marka: {bilgiler['marka']}\n"
                   f"Model: {bilgiler['model']}\n\n"
                   f"Arıza & Talep Özeti:\n{bilgiler['detay']}")
    pdf.multi_cell(0, 8, cihaz_metni)
    
    pdf.ln(10)
    pdf.set_font('TurkishArial', 'B', 10)
    pdf.cell(0, 10, "Bu form cihazınızın teslim alındığına dair resmi kayıttır.", ln=1, align='C')

    # PDF'i Geçici Olarak Kaydet ve Gönder
    dosya_adi = f"servis_formu_{bilgiler['ad'].replace(' ', '_')}.pdf"
    
    # Vercel'de /tmp klasörü yazılabilir tek yerdir, ancak send_file doğrudan çıktı verebilir
    pdf.output(dosya_adi)
    
    return send_file(dosya_adi, as_attachment=True)

# Vercel entegrasyonu için uygulama nesnesini dışa aktarıyoruz
if __name__ == '__main__':
    app.run(debug=True)