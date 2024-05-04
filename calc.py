# Başlangıç parametreleri
baslangic_sermayesi = 1000  # x lira olarak varsayılır
kaldıraç = 2  # Kaldıraç oranı
artis_orani = 0.02  # Her adımdaki yüzdesel artış

# Toplam adım sayısı hesaplama
y = 3.60 # Coin başlangıç değeri
mevcut_deger = y
toplam_adim_sayisi = 0
while mevcut_deger < 9 * y:
    mevcut_deger += mevcut_deger * (artis_orani)
    toplam_adim_sayisi += 1
print("Kaç kata çıkıyor ", mevcut_deger / y)

print(toplam_adim_sayisi)


mevcut_sermaye = baslangic_sermayesi
for _ in range(toplam_adim_sayisi):
    mevcut_sermaye *= (1 + kaldıraç * artis_orani)

print(mevcut_sermaye)
