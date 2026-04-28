import streamlit as st
import math
import pandas as pd
import plotly.express as px

# --- YÖNEYLEM HESAPLAMA MOTORU (M/M/c) ---
def mmc_kuyruk_hesapla(istasyon_adi, lam, mu, c):
    rho = lam / (c * mu)
    
    # Kararlılık Kontrolü (Sistem Patlıyor mu?)
    if rho >= 1:
        return {
            "İstasyon": istasyon_adi,
            "Durum": "🛑 Kapasite Aşıldı!",
            "Kullanım Oranı (Rho)": rho,
            "Boş Kalma Olasılığı (P0)": 0.0,
            "Kuyruktaki İş (Lq)": float('inf'), # Sonsuz
            "Kuyruk Süresi (Wq)": float('inf')  # Sonsuz
        }

    # Kararlı Durum Hesaplamaları
    toplam = sum((math.pow(lam / mu, n) / math.factorial(n)) for n in range(c))
    ikinci_kisim = (math.pow(lam / mu, c) / math.factorial(c)) * (1 / (1 - rho))
    p0 = 1 / (toplam + ikinci_kisim)

    lq = (p0 * math.pow(lam / mu, c) * rho) / (math.factorial(c) * math.pow(1 - rho, 2))
    wq = lq / lam

    return {
        "İstasyon": istasyon_adi,
        "Durum": "✅ Kararlı",
        "Kullanım Oranı (Rho)": rho,
        "Boş Kalma Olasılığı (P0)": p0,
        "Kuyruktaki İş (Lq)": lq,
        "Kuyruk Süresi (Wq)": wq
    }

# --- STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="Matek Kuyruk Teorisi Analizi", layout="wide")

st.title("📊 Matek Grup - Jackson Ağı Kuyruk Teorisi Analizi")
st.markdown("Bu panel, üretim hattınızın **M/M/c Kararlı Durum (Steady State)** analitiğini yapar. İstasyonların kapasite kullanım oranlarını ve sistemdeki darboğazı anlık olarak tespit edin.")

# --- YAN PANEL: PARAMETRELER ---
st.sidebar.header("⚙️ Sistem Parametreleri")
st.sidebar.markdown("**Zaman Birimi:** Gün")

lam = st.sidebar.slider("Geliş Hızı (λ - Sipariş/Gün)", min_value=0.1, max_value=5.0, value=0.5, step=0.1, help="Günde ortalama kaç sipariş geliyor?")

st.sidebar.markdown("---")
st.sidebar.subheader("1. Kesim İstasyonu")
c_kesim = st.sidebar.number_input("Makine Sayısı (c)", 1, 5, 1, key='c1')
mu_kesim = st.sidebar.slider("Hizmet Hızı (μ - İş/Gün)", 0.1, 10.0, 2.0, step=0.1, key='m1')

st.sidebar.subheader("2. Montaj İstasyonu")
c_montaj = st.sidebar.number_input("Ekip Sayısı (c)", 1, 5, 2, key='c2')
mu_montaj = st.sidebar.slider("Hizmet Hızı (μ - İş/Gün)", 0.1, 5.0, 0.4, step=0.1, key='m2')

st.sidebar.subheader("3. Boya İstasyonu")
c_boya = st.sidebar.number_input("Fırın Sayısı (c)", 1, 5, 1, key='c3')
mu_boya = st.sidebar.slider("Hizmet Hızı (μ - İş/Gün)", 0.1, 10.0, 1.0, step=0.1, key='m3')

st.sidebar.subheader("4. Paketleme İstasyonu")
c_paket = st.sidebar.number_input("Ekip Sayısı (c)", 1, 5, 1, key='c4')
mu_paket = st.sidebar.slider("Hizmet Hızı (μ - İş/Gün)", 0.1, 10.0, 3.0, step=0.1, key='m4')

# --- HESAPLAMA VE GÖRSELLEŞTİRME ---
istasyonlar = [
    ("Kesim", mu_kesim, c_kesim),
    ("Montaj", mu_montaj, c_montaj),
    ("Boya", mu_boya, c_boya),
    ("Paket", mu_paket, c_paket)
]

sonuclar = []
for ad, mu, c in istasyonlar:
    sonuclar.append(mmc_kuyruk_hesapla(ad, lam, mu, c))

df = pd.DataFrame(sonuclar)

# Analiz Özeti
st.subheader("📋 Sistem Kararlılık Özeti")

# Darboğazı Bul (Rho değeri en yüksek olan istasyon)
darbogaz_istasyon = df.loc[df['Kullanım Oranı (Rho)'].idxmax()]
maks_rho = darbogaz_istasyon['Kullanım Oranı (Rho)']

if maks_rho >= 1:
    st.error(f"🚨 **SİSTEM ÇÖKTÜ!** Darboğaz noktası: **{darbogaz_istasyon['İstasyon']}**. Kullanım oranı %{maks_rho*100:.0f}. Bu istasyonda siparişler sonsuza kadar birikecek. Lütfen kapasiteyi (c) veya işlem hızını (μ) artırın!")
else:
    st.success(f"✅ Sistem Kararlı. En yoğun istasyon (Darboğaz): **{darbogaz_istasyon['İstasyon']}** (Kullanım: %{maks_rho*100:.1f})")

# Tablo Gösterimi
st.dataframe(
    df.style.format({
        'Kullanım Oranı (Rho)': '{:.1%}',
        'Boş Kalma Olasılığı (P0)': '{:.1%}',
        'Kuyruktaki İş (Lq)': '{:.2f}',
        'Kuyruk Süresi (Wq)': '{:.2f} Gün'
    }).map(lambda x: 'background-color: #ffcccc' if x == "🛑 Kapasite Aşıldı!" else '', subset=['Durum'])
)

# Grafikler
col1, col2 = st.columns(2)

with col1:
    fig_rho = px.bar(df, x='İstasyon', y='Kullanım Oranı (Rho)', 
                     title='İstasyonların Kapasite Kullanım Oranları (ρ)',
                     color='Kullanım Oranı (Rho)', color_continuous_scale='RdYlGn_r')
    fig_rho.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Kapasite Sınırı (Patlama Noktası)")
    fig_rho.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_rho, use_container_width=True)

with col2:
    # Lq grafiği (Eğer sistem çöktüyse sonsuz değerleri grafikte göstermek zor, onları filtreliyoruz)
    df_kararli = df[df['Kullanım Oranı (Rho)'] < 1]
    if not df_kararli.empty:
        fig_lq = px.bar(df_kararli, x='İstasyon', y='Kuyruktaki İş (Lq)',
                        title='İstasyon Önünde Bekleyen Ortalama Sipariş Sayısı (Lq)',
                        color_discrete_sequence=['#3498db'])
        st.plotly_chart(fig_lq, use_container_width=True)
    else:
        st.warning("Tüm istasyonlar çöktüğü için kuyruk uzunluğu grafiği çizilemiyor.")