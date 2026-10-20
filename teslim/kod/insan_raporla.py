"""İnsan etiketleriyle ilk sonuç ve bonusun sınırlarını raporlar."""
import json
import pandas as pd
from duzen import CIKTILAR as O
r=json.loads((O/'bonus_once_sonra.json').read_text());a,b=r['denemeler']
source=json.loads((O/'insan_altin_set_kaynak.json').read_text());u=r['benzersiz_metin'];u1,u2=u['denemeler'];mixed=r['karisik_sinifi']
g=pd.read_csv(O/'altin_set.csv',keep_default_na=False)
def num(value,digits):return f"{value:.{digits}f}".replace('.', ',')
text=f"""# İnsan değerlendirmesi ve bonus

Referans [altin_set.csv](altin_set.csv), kendim elle doldurduğum 40 kaydın birebir kopyasıdır. {source['etiketleme_yontemi']} Referansın kimlik/metin eşleşmesi ve dosya bütünlüğü kontrol edilir. Konular sıra bağımsız kümelerdir. Virgül/dik çizgi ayracı hesapta temizlenir. Boş/anlamsız yorumun konusu boş küme olabilir. İnsan etiketleri ve notları değiştirilmedi. 40 kayıtta {g.metin.nunique()} farklı metin ve tek insan etiketleyici vardır.

## İlk deneme ve sistematik uyuşmazlıklar

Karışık sınıfında yakalama {mixed['ilk']['dogru']}/{mixed['ilk']['n']} → {mixed['bonus']['dogru']}/{mixed['bonus']['n']}; LLM çekimser yorumlarda bir kutbu seçebiliyor.

İlk LLM duygu {a['duygu_dogru']}/40, konu kümesi {a['konu_dogru']}/40 eşleşmesi verdi. [Sınıf metrikleri](llm_basari.json). 9071'de ironili övgü ile uzun bekleme, 9330'da çekingen memnuniyet verdiğim Karışık etiketinden farklı değerlendirildi. Notlarım alternatif duygu yorumlarına da yer verir; bu farklar kesin model hatası olarak değerlendirilmez. 9451/9639 boş yorumlarda ilk istemin zorunlu Diğer konusu insanın boş kümesiyle uyuşmadı: yönerge farkı. Genel hizmet övgüsünden İş kalitesi çıkarılması 9024/9622'de fazla etiket üretti. 9091/9136 parça beklemesinde Süre; 9300 fatura bilgilendirmesinde Personel konu sınırları farklı yorumlandı. Tek başarı sayısı bu sorunları açıklamaz.

## İnsan bulgularına dayalı bonus değerlendirmesi

Güncellenen yönerge, boş yorumların konu etiketini ve genel hizmet övgüsü ile somut iş sonucu arasındaki ayrımı netleştirdi. İnsan değerlendirmesinde ara denemenin “yine sorunsuz” ifadesindeki İş kalitesini atladığı görülmüştü; teknik arıza adı olmasa da somut hizmet sonucu seçilir. Açık iletişim ve parça bekleme konuları sırf altın sete uymak için bastırılmaz. İroni, olumsuzlama ve çekingen memnuniyet kuralları netleştirildi. [Bonus istemi](../kod/llm_istem_bonus.txt), [36 anonim girdi](../kod/llm_bonus_girdi.json), [ham LLM yanıtı](../kod/llm_bonus_ham_yanit.json), [çıkarım kaydı](bonus_cikarim_kaydi.json).

Başlangıç → bonus: duygu {a['duygu_dogru']}/40 → {b['duygu_dogru']}/40; accuracy %{num(100*a['duygu_accuracy'],1)} → %{num(100*b['duygu_accuracy'],1)}; macro-F1 {num(a['duygu_macro_f1'],3)} → {num(b['duygu_macro_f1'],3)}. Konu tam eşleşmesi {a['konu_dogru']}/40 → {b['konu_dogru']}/40; %{num(100*a['konu_exact_match'],1)} → %{num(100*b['konu_exact_match'],1)}; micro-F1 {num(a['konu_micro_f1'],3)} → {num(b['konu_micro_f1'],3)}. Uyuşmazlık {a['uyusmazlik_kaydi']} → {b['uyusmazlik_kaydi']}. Düzelen {len(r['duzelen_idler'])}, yeni fark {len(r['yeni_uyusmazlik_idler'])}, süren {len(r['suren_uyusmazlik_idler'])}. [Sayısal sonuç](bonus_once_sonra.json), [40 kayıt ve notlar](bonus_once_sonra_kayitlar.csv), [fark dökümü](llm_uyusmazliklar.csv), [bonus sınıf metrikleri](bonus_basari.json).

9071/9330 duygu; 9091/9136 Süre; 9300 Personel farkları kaldı. Bu uyuşmazlıklar, konu sınırları ve duygu yorumlarına ilişkin değerlendirme farkları olarak korundu. 9177/9418 “sorunsuz” hizmet sonucunda İş kalitesi ve Personel seçildi. Boş yorumdaki kazanç daha iyi dil anlama değil yönerge uyumudur.

## İyileşmenin kaynağı ve metin düzeyindeki ölçüm

Düzelen {len(r['duzelen_idler'])} kayıt {u['duzelen_metin_sayisi']} farklı metindir. 9024/9622, bonus istemindeki “Hizmet güzeldi, otopark yetersizdi” örneğiyle aynı yorumu ve etiketleri paylaşır. 9451 (“?”) ve 9639 (boş) boş/anlamsız metin kuralıyla hizalandı. 9524'te duygu yorumu Olumsuzdan Karışığa değişti. Bu kazanımların tümü genel dil anlama başarısı olarak yorumlanamaz.

Benzersiz metin düzeyinde n={u['n']}: duygu {u1['duygu_dogru']}/{u['n']} → {u2['duygu_dogru']}/{u['n']}; konu tam eşleşmesi {u1['konu_dogru']}/{u['n']} → {u2['konu_dogru']}/{u['n']}; herhangi bir uyuşmazlık {u1['uyusmazlik']}/{u['n']} → {u2['uyusmazlik']}/{u['n']}. İstemdeki bir örnek altın setteki bir yorumun yeniden ifadesidir; %82,5 → %92,5 aynı örneklere uyumu gösterir ve genelleme başarısını iyimser gösterebilir. İstemde referans cevap kullanılmaması istenirken referansla uyumdan söz edilmesi de yönergeyi belirsizleştirir; kullanılmış istemi sonradan değiştirmedim.

Bağımsız 11 metinlik ek kontrol gerçekleştirmedim; yeni insan etiketleri olmadan böyle bir değerlendirme sunmuyorum.

## Ölçüm sınırları

Üç LLM etiketleme turu gerçekleştirilmiştir. Başlangıç ve bonus sonuçları aynı insan etiketli 40 kayıt üzerinde karşılaştırılmıştır. Ara turda duygu doğruluğu %95, konu tam eşleşmesi %87,5 olarak ölçülmüştür.

Bonus yönergesi insan değerlendirmesinde belirlenen hatalar doğrultusunda geliştirilmiştir. Son etiketleme sırasında insan etiketleri modelin bağlamında bulunduğundan, sonuçlar **aynı set üzerinde yapılan bir geliştirme karşılaştırmasıdır**; bağımsız veya kör test değildir. Ölçülen başarı yeni metinlerde aynı başarının elde edileceğini göstermez.

Tekrarlanan metinler, tek insan etiketleyici ve yorum farklılıkları değerlendirmeyi sınırlar. Turlar arasında model sürümlerinin aynı olduğu doğrulanmadığından, iyileşmenin tamamı yalnızca yönerge değişimine bağlanamaz.
"""
(O/'insan_degerlendirme.md').write_text(text)
print('İnsan raporu üretildi.')
