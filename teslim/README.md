# Çalıştırma ve teslim

[Ana rapor](RAPOR.md) güncel sonuçları içerir. [altin_set.csv](ciktilar/altin_set.csv), kendim elle doldurduğum 40 kaydın birebir kopyasıdır. Başlangıç LLM etiketleri ve insan bulgularına dayalı bonus etiketleri ayrı dosyalardadır.

## Çalıştırma

ZIP yeni bir klasörde, Python 3.9.6 ile oluşturulan temiz sanal ortamda doğrulandı. Test aynı macOS bilgisayarında yapıldı; Linux veya ayrı makine testi yapılmadı. ZIP açılınca veri/ ve teslim/ aynı kökte bulunmalıdır. Sabit paket sürümleri kod/requirements.txt içindedir. Paket kökünde:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r teslim/kod/requirements.txt
python3 teslim/kod/etiketleri_aktar.py
python3 teslim/kod/analiz.py > teslim/ciktilar/calistirma.log 2> teslim/ciktilar/calistirma_uyarilari.log
python3 teslim/kod/insan_degerlendir.py
python3 teslim/kod/insan_raporla.py
python3 teslim/kod/raporla.py
python3 teslim/kod/kontrol.py
```

Kod yolları kendi konumundan bulur. Ham veriler ve insan etiketleri değiştirilmez. Çalıştırma sırasında yeni LLM çağrısı yapılmaz. Kod, etiketleme aşamasında kaydedilen ham JSON yanıtlarını birebir eşleşen metinlere aktarır. Teknik etiketler CSV/JSON'da korunur; görünen adlar yalnız sunum içindir. Boş konu hücresi boş kümedir; konular virgül veya dik çizgiyle ayrıştırılır.

## Yöntem ve sınırlar

40 kaydı kendim elle etiketledim. LLM çıktısını önceden görüp görmediğimden emin olmadığım için kör etiketleme iddiasında bulunmuyorum; LLM etkisini dışlayamıyorum.

200 kayıt tohum 42 ile seçildi. İnsan örneklemi için ilk taslakta seçilmiş 40 kimlik çıkarıldı; kalan 160 kayıt kimliğe göre sıralanıp tohum 44 ile 40 kayıt seçildi. [Örnekleme kaydı](ciktilar/insan_ornekleme_kaydi.json) bu seçimden yeniden doğrulamayı sağlar. Model ayrımları 42/43, bootstrap 44 ve değişken önemleri 42 tohumlarını kullanır.

Başlangıç etiketleri `llm_etiketleri.csv`, bonus etiketleri `llm_etiketleri_bonus.csv`, aynı insan setindeki karşılaştırma ise `bonus_once_sonra.json` dosyasındadır. Üç etiketleme turu gerçekleştirilmiştir. Bonus değerlendirmesinde, insan etiketleriyle yapılan karşılaştırmada belirlenen hatalara göre yönerge güncellenmiş ve son turun sonuçları başlangıç sonuçlarıyla karşılaştırılmıştır. Ara turun sonuçları ayrıntılı değerlendirmede sunulmuştur. İnsan etiketleri geliştirme sırasında modelin bağlamında bulunduğundan, sonuçlar aynı set üzerinde yapılan bir geliştirme karşılaştırmasıdır; kör veya bağımsız test olarak değerlendirilmemelidir. Turlar arasında kullanılan model sürümlerinin aynı olduğu doğrulanmamıştır.

Bonus kazanımlarının örnek/kural uyumu ve benzersiz metin ölçümü ayrıntılı değerlendirmede açıklanır. 11 farklı metin için ek bağımsız insan kontrolü yapılmadı.

[Yöntem kaydı](ciktilar/bonus_cikarim_kaydi.json), [ayrıntılı değerlendirme](ciktilar/insan_degerlendirme.md), [kullanım günlüğü](ciktilar/llm_kullanim_gunlugu.txt).

Dosya bütünlüğü kontrolü yalnız 8 sabit girdiye uygulanır. Yeniden üretilen `model_sonuclari.json` ve `musteri_analiz.csv` bayt özetiyle karşılaştırılmaz; küçük platform farkları için sayısal tutarlılık kontrolleri kullanılır.

Ön işleme yalnız eğitimde öğrenilir; eşik doğrulamada seçilir. %20 kapasite varsayımdır. Model üretime alınmadı; müşterilere iletişim gönderilmedi. BLAS uyarılarına karşı eşdeğer einsum skoru ayrı toplamla kontrol edilir; uyarılar bastırılmaz. Sonlu değerler ve metrik tutarlılığı doğrulanır.

## Paketleme

`python3 teslim/kod/paketle.py` güncel ZIP'i oluşturur. Sanal ortam, önbellek ve ZIP'in kendisi pakete alınmaz. [Çalıştırma doğrulaması](ciktilar/teslim_dogrulama.txt) teslim paketinin ayrı klasörden sınanmasını belgeler.