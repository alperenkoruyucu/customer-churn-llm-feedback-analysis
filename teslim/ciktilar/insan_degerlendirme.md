# İnsan değerlendirmesi ve bonus

Referans [altin_set.csv](altin_set.csv), kendim elle doldurduğum 40 kaydın birebir kopyasıdır. 40 kaydı kendim elle etiketledim. LLM çıktısını önceden görüp görmediğimden emin olmadığım için kör etiketleme iddiasında bulunmuyorum; LLM etkisini dışlayamıyorum. Referansın kimlik/metin eşleşmesi ve dosya bütünlüğü kontrol edilir. Konular sıra bağımsız kümelerdir. Virgül/dik çizgi ayracı hesapta temizlenir. Boş/anlamsız yorumun konusu boş küme olabilir. İnsan etiketleri ve notları değiştirilmedi. 40 kayıtta 25 farklı metin ve tek insan etiketleyici vardır.

## İlk deneme ve sistematik uyuşmazlıklar

Karışık sınıfında yakalama 5/8 → 6/8; LLM çekimser yorumlarda bir kutbu seçebiliyor.

İlk LLM duygu 37/40, konu kümesi 33/40 eşleşmesi verdi. [Sınıf metrikleri](llm_basari.json). 9071'de ironili övgü ile uzun bekleme, 9330'da çekingen memnuniyet verdiğim Karışık etiketinden farklı değerlendirildi. Notlarım alternatif duygu yorumlarına da yer verir; bu farklar kesin model hatası olarak değerlendirilmez. 9451/9639 boş yorumlarda ilk istemin zorunlu Diğer konusu insanın boş kümesiyle uyuşmadı: yönerge farkı. Genel hizmet övgüsünden İş kalitesi çıkarılması 9024/9622'de fazla etiket üretti. 9091/9136 parça beklemesinde Süre; 9300 fatura bilgilendirmesinde Personel konu sınırları farklı yorumlandı. Tek başarı sayısı bu sorunları açıklamaz.

## İnsan bulgularına dayalı bonus değerlendirmesi

Güncellenen yönerge, boş yorumların konu etiketini ve genel hizmet övgüsü ile somut iş sonucu arasındaki ayrımı netleştirdi. İnsan değerlendirmesinde ara denemenin “yine sorunsuz” ifadesindeki İş kalitesini atladığı görülmüştü; teknik arıza adı olmasa da somut hizmet sonucu seçilir. Açık iletişim ve parça bekleme konuları sırf altın sete uymak için bastırılmaz. İroni, olumsuzlama ve çekingen memnuniyet kuralları netleştirildi. [Bonus istemi](../kod/llm_istem_bonus.txt), [36 anonim girdi](../kod/llm_bonus_girdi.json), [ham LLM yanıtı](../kod/llm_bonus_ham_yanit.json), [çıkarım kaydı](bonus_cikarim_kaydi.json).

Başlangıç → bonus: duygu 37/40 → 38/40; accuracy %92,5 → %95,0; macro-F1 0,919 → 0,948. Konu tam eşleşmesi 33/40 → 37/40; %82,5 → %92,5; micro-F1 0,937 → 0,972. Uyuşmazlık 10 → 5. Düzelen 5, yeni fark 0, süren 5. [Sayısal sonuç](bonus_once_sonra.json), [40 kayıt ve notlar](bonus_once_sonra_kayitlar.csv), [fark dökümü](llm_uyusmazliklar.csv), [bonus sınıf metrikleri](bonus_basari.json).

9071/9330 duygu; 9091/9136 Süre; 9300 Personel farkları kaldı. Bu uyuşmazlıklar, konu sınırları ve duygu yorumlarına ilişkin değerlendirme farkları olarak korundu. 9177/9418 “sorunsuz” hizmet sonucunda İş kalitesi ve Personel seçildi. Boş yorumdaki kazanç daha iyi dil anlama değil yönerge uyumudur.

## İyileşmenin kaynağı ve metin düzeyindeki ölçüm

Düzelen 5 kayıt 4 farklı metindir. 9024/9622, bonus istemindeki “Hizmet güzeldi, otopark yetersizdi” örneğiyle aynı yorumu ve etiketleri paylaşır. 9451 (“?”) ve 9639 (boş) boş/anlamsız metin kuralıyla hizalandı. 9524'te duygu yorumu Olumsuzdan Karışığa değişti. Bu kazanımların tümü genel dil anlama başarısı olarak yorumlanamaz.

Benzersiz metin düzeyinde n=25: duygu 22/25 → 23/25; konu tam eşleşmesi 20/25 → 23/25; herhangi bir uyuşmazlık 8/25 → 4/25. İstemdeki bir örnek altın setteki bir yorumun yeniden ifadesidir; %82,5 → %92,5 aynı örneklere uyumu gösterir ve genelleme başarısını iyimser gösterebilir. İstemde referans cevap kullanılmaması istenirken referansla uyumdan söz edilmesi de yönergeyi belirsizleştirir; kullanılmış istemi sonradan değiştirmedim.

Bağımsız 11 metinlik ek kontrol gerçekleştirmedim; yeni insan etiketleri olmadan böyle bir değerlendirme sunmuyorum.

## Ölçüm sınırları

Üç LLM etiketleme turu gerçekleştirilmiştir. Başlangıç ve bonus sonuçları aynı insan etiketli 40 kayıt üzerinde karşılaştırılmıştır. Ara turda duygu doğruluğu %95, konu tam eşleşmesi %87,5 olarak ölçülmüştür.

Bonus yönergesi insan değerlendirmesinde belirlenen hatalar doğrultusunda geliştirilmiştir. Son etiketleme sırasında insan etiketleri modelin bağlamında bulunduğundan, sonuçlar **aynı set üzerinde yapılan bir geliştirme karşılaştırmasıdır**; bağımsız veya kör test değildir. Ölçülen başarı yeni metinlerde aynı başarının elde edileceğini göstermez.

Tekrarlanan metinler, tek insan etiketleyici ve yorum farklılıkları değerlendirmeyi sınırlar. Turlar arasında model sürümlerinin aynı olduğu doğrulanmadığından, iyileşmenin tamamı yalnızca yönerge değişimine bağlanamaz.
