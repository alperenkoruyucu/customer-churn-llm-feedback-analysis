from pathlib import Path
import json,html
import pandas as pd
P=Path(__file__).resolve().parents[1];O=P/'ciktilar'
r=json.loads((O/'model_sonuclari.json').read_text());q=json.loads((O/'veri_kalite.json').read_text());b=pd.read_csv(O/'musteri_analiz.csv');c=pd.read_csv(O/'merkez_karsilastirma.csv');imp=pd.read_csv(O/'degisken_onemleri.csv');candidates=pd.read_csv(O/'aksiyon_adaylari.csv')
def tr(value,digits=0):return f"{value:,.{digits}f}".replace(',', '_').replace('.', ',').replace('_', '.')
def pct(v):return f'%{tr(100*v,1)}'
def svg_bars():
 rows=[]
 for feature,label in [('recency_gun','Son servisten bu yana gün (ortalama)'),('frequency','Ziyaret sayısı (ortalama)'),('ort_memnuniyet','Yanıt veren müşteri puanı (ortalama, 1–5)')]:
  vals=[b.loc[b.churn.eq(k),feature].mean() for k in [0,1]];rows.append((label,vals))
 s=['<svg xmlns="http://www.w3.org/2000/svg" width="850" height="500" viewBox="0 0 850 500"><rect width="850" height="500" fill="white"/><g font-family="Arial" fill="#182f44"><text x="30" y="30" font-size="20">Terk eden ve etmeyen müşteriler</text><text x="30" y="55" font-size="12">Kaynak: temiz servis verisi · 2022-01-01–2025-06-30 · müşteri başına özet</text>']
 for j,(title,vals) in enumerate(rows):
  yy=95+j*125;s.append(f'<text x="30" y="{yy}" font-size="15">{html.escape(title)}</text>')
  for k,v in enumerate(vals):
   y=yy+12+k*32;w=v/max(vals)*440;color=['#557a95','#b75c45'][k];label=['Servise geldi (churn=0)','Servise gelmedi (churn=1)'][k]
   s.append(f'<text x="30" y="{y+18}" font-size="12">{label}</text><rect x="215" y="{y}" width="{w}" height="24" fill="{color}"/><text x="{225+w}" y="{y+18}" font-size="13">{tr(v,2)}</text>')
 s.append('<text x="30" y="480" font-size="12">Çubuk uzunlukları her ölçüt içinde ölçeklidir; paneller arasında kıyaslanmaz.</text></g></svg>');(O/'churn_bulgular.svg').write_text(''.join(s))
def svg_centers():
 s=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="500"><rect width="900" height="500" fill="white"/><g font-family="Arial" fill="#182f44"><text x="25" y="30" font-size="20">Servis merkezlerinin memnuniyeti</text><text x="25" y="53" font-size="12">Kaynak: gözlem dönemi servis anketleri · 2022-01-01–2025-06-30</text><text x="25" y="73" font-size="12">Mavi: ham puan ve müşteri kümesi bootstrap %95 aralık · Turuncu: bileşime göre standart puan</text>']
 def x(v):return 220+(v-3.8)/.3*520
 for j,row in c.iterrows():
  y=115+j*43;s.append(f'<text x="25" y="{y+4}" font-size="13">{html.escape(row.merkez)}</text><line x1="{x(row.ci_alt)}" x2="{x(row.ci_ust)}" y1="{y}" y2="{y}" stroke="#557a95" stroke-width="2"/><circle cx="{x(row.ham_ortalama)}" cy="{y}" r="5" fill="#557a95"/><circle cx="{x(row.standart_ortalama)}" cy="{y+12}" r="5" fill="#b75c45"/><text x="770" y="{y+4}" font-size="12">n={int(row.yanit)}</text>')
 for tick in [3.8,3.9,4,4.1]:s.append(f'<text x="{x(tick)-10}" y="435" font-size="12">{tr(tick,1)}</text>')
 s.append('<text x="320" y="459" font-size="13">Memnuniyet puanı (1–5; eksen 3,8–4,1 aralığında)</text><text x="25" y="485" font-size="11">Standartlaştırma: ortak müşteri tipi × işlem tipi dağılımı; nedensel merkez etkisi değildir.</text></g></svg>');(O/'merkezler.svg').write_text(''.join(s))
svg_bars();svg_centers()
# Aksiyon cümleleri LLM tarafından adayların gerçek metinleri üzerinden üretildi.
actions={103088:'Müşteriyi arayıp yeniden gelme konusundaki tereddüdünün nedenini dinleyin ve çözüm için ilgili servis danışmanına iletin.',102339:'Müşteriyi arayıp web randevusunda yaşadığı sorunu doğrulayın, uygun randevu oluşturmasına yardımcı olun ve hatayı ilgili ekibe iletin.',103705:'Müşteriyi arayıp düşük değerlendirmesine neden olan deneyimi ayrıntılandırmasını isteyin ve şikâyetini ilgili servis sorumlusuna iletin.'}
assert set(candidates.musteri_id)==set(actions)
candidates['aksiyon']=[actions[x] for x in candidates.musteri_id];assert all(not any(t in x.lower() for t in ['%','indirim','ücretsiz','hediye','kampanya']) for x in candidates.aksiyon)
candidates.to_csv(O/'llm_aksiyonlar.csv',index=False)
(O/'aksiyon_istem.txt').write_text('Bu üç adayın kesim öncesi olumsuz metnini ve konularını kullanarak müşteri temsilcisine tek cümlelik aksiyon üret. İzinli öneriler: sorunu dinleme/doğrulama, mevcut randevu sürecine yardım, ilgili ekibe veya servis sorumlusuna iletme. İndirim, hediye, ücretsiz hizmet veya kampanya vaat etme; metinde bulunmayan olay veya neden ekleme. Liste bir öneridir, şirketin gerçek yetkileri iş birimiyle doğrulanmalıdır. Aday girdiler: aksiyon_adaylari.csv; risk, konular ve metin gerçek analizden alınmıştır.')
metrics=r['test_model'];bl=r['test_baseline'];qc=q['kontroller'];groups=b.groupby('churn')
bonus=json.loads((O/'bonus_once_sonra.json').read_text());v1,v2=bonus['denemeler']
# Sunum adları veri şemasından ayrıdır; CSV/JSON etiketleri değişmez.
names={'recency_gun':'Son ziyaretten geçen süre','ort_memnuniyet':'Ortalama memnuniyet','ort_km':'Ortalama kilometre','ort_arac_yasi':'Ortalama araç yaşı','frequency':'Ziyaret sıklığı'}
reasons={'recency_gun':'İlişkinin soğumasını ve bakım aralığını yansıtabilir.','ort_memnuniyet':'Hizmet deneyimiyle yeniden gelme isteği arasındaki ilişkiyi temsil edebilir.','ort_km':'Kullanım yoğunluğu ve bakım ihtiyacını temsil eder; sözlükteki ×1000 birimi kaynakla doğrulanmalıdır.','ort_arac_yasi':'Garanti ve bakım ekonomisinin değişmesini yansıtabilir.','frequency':'Geçmiş ilişkinin sürekliliğini gösterir; araç sayısıyla birlikte yorumlanmalıdır.'}
importance='\n'.join(f"- **{names.get(row.ozellik,row.ozellik)}:** AUC düşüşü {tr(row.auc_azalis,3)}. {reasons[row.ozellik]}" for row in imp.head(5).itertuples())
findings=[]
for field,label,interpret in [('recency_gun','Son ziyaretten geçen süre','Daha uzun ara, yeniden ziyaretin azalmasıyla birlikte görülüyor.'),('frequency','Ziyaret sıklığı','Daha sık geçmiş ziyaret, ilişkinin sürmesiyle birlikte görülüyor.'),('ort_memnuniyet','Memnuniyet','Daha düşük deneyim puanı terk grubuyla ilişkili; yalnız yanıt veren müşterileri temsil ediyor.')]:
 vals=[groups.get_group(k)[field].mean() for k in [0,1]]
 findings.append(f'- **{label}:** gelenlerde {tr(vals[0],2)}, gelmeyenlerde {tr(vals[1],2)}. {interpret}')
act='\n'.join(f'- **{row.musteri_id}** (risk {pct(row.risk)}): {row.aksiyon}' for row in candidates.itertuples())
maslak=c[c.merkez.eq('SM-Maslak')].iloc[0];izmir=c[c.merkez.eq('SM-İzmir1')].iloc[0]
counts=r['churn_dagilimi'];crm=q['crm_hedef_tanisi'];notes=crm['son_iletisim_notu'];status=crm['crm_musteri_durumu']
lost_notes=['Araç satıldı','Başka servise geçti','İlgilenmiyor','Ulaşılamadı'];contact_notes=['Kampanya bilgilendirmesi','Randevu hatırlatması yapıldı','Memnuniyet araması']
n_lost=sum(notes[x]['n'] for x in lost_notes);churn_lost=sum(notes[x]['churn'] for x in lost_notes);n_contact=sum(notes[x]['n'] for x in contact_notes);return_contact=n_contact-sum(notes[x]['churn'] for x in contact_notes)
u=bonus['benzersiz_metin'];u1,u2=u['denemeler'];mixed=bonus['karisik_sinifi'];gold_source=json.loads((O/'insan_altin_set_kaynak.json').read_text())
human_method=gold_source['etiketleme_yontemi']
first_prompt=(P/'kod/llm_istem.txt').read_text().strip()
report=f'''# Müşteri terk vakası — teslim raporu

Analiz, insan değerlendirmesi ve bonus sonuçları. Çalıştırma: [README](README.md).

## 1. Veri hazırlığı ve keşif

Gözlem penceresi **2022-01-01–2025-06-30**, hedef penceresi **2025-07-01–2026-06-30**; uç tarihler dahildir. Popülasyonda vakadaki “2025-06-30'dan önce” ifadesi sıkı `< 2025-06-30` yorumlandı: yalnız kesim günü ilk ziyareti olan bir müşteri dışarıdadır. Mevcut müşterilerin o günkü işlemleri özelliklere dahildir. Hedefte en az bir ziyaret varsa `churn=0`, yoksa `churn=1`: **{tr(counts['0'])} gelen, {tr(counts['1'])} gelmeyen (%{tr(100*counts['1']/r['n'],1)})**. Servise gelmemek, başka servise geçtiğini kanıtlamaz.

Kaynakta **{tr(q['dosyalar']['musteriler']['temiz_satir'])} farklı müşteri**, son analizde **{tr(r['n'])} tekil müşteri satırı** vardır. Araçlar üzerinden servis ve geri bildirimleri doğrudan birleştirmek, ham servis satırlarını {tr(q['dosyalar']['servis_kayitlari']['ham_satir'])}'ten {tr(qc['ham_servis_feedback_left_join_satir'])}'ya çıkarır. Bu nedenle tablolar ayrı özetlenip müşteri seviyesinde birleştirildi; tekillik kontrol edildi. Dört tarih biçimi ayrıştırıldı; geçersiz tarih/yetim ilişki bulunmadı. [Kontrol dökümü](ciktilar/veri_kalite.json).

**Üç veri kalitesi kararı:**

1. **Bulgu:** müşteri kartlarında {q['dosyalar']['musteriler']['tam_tekrar']}, serviste {q['dosyalar']['servis_kayitlari']['tam_tekrar']} tam tekrar. **İşlem:** birebir tekrarları kaldırdım. **Gerekçe:** tekrarlar yeni ziyaret değildir; farklı içerikli satırlar korunmalıdır.
2. **Bulgu:** {qc['negatif_tutar']} negatif tutar ve {qc['negatif_km']} negatif kilometre. **İşlem:** ilgili değerler eksik bırakıldı, ziyaret korundu. **Gerekçe:** işlem kodu olmadan iade ile hatayı ayıramayız; değeri pozitif yapmak veri uydurur. Yüksek pozitif faturalar harcama toplamında korundu; modelde yalnız eğitimden öğrenilen %1–%99 sınırları uygulandı. Bu karar büyük filo faturalarını bastırabilir.
3. **Bulgu:** {qc['satinalma_oncesi_geribildirim']} geri bildirim satın alma tarihinden önce. **İşlem:** tarihsel özelliklerden ve aksiyon adaylarından çıkarıldı, ham LLM örnekleminde korundu. **Gerekçe:** sahiplik geçmişi olmadan o tarihte müşteriye aidiyet doğrulanamaz.

Recency son ziyaretten geçen gün, frequency ziyaret sayısı, monetary geçerli fatura toplamıdır. Tamamı eksik tutar sıfır sayılmaz. [Müşteri tablosu](ciktilar/musteri_analiz.csv).

**Üç keşif bulgusu** — “gelen”, hedef döneminde servisi ziyaret edendir:

{chr(10).join(findings)}

![Müşteri gruplarının üç ölçütte karşılaştırılması](ciktilar/churn_bulgular.svg)

Bunlar ilişki bulgularıdır. [Ayrıntılı özetler](ciktilar/churn_bulgular.csv).

**Merkezler:** %{tr(100*qc['ham_memnuniyet_eksik_orani'],1)} anket yanıtsızlığı var; eksik puanlar doldurulmadı. [Merkez tablosu](ciktilar/merkez_karsilastirma.csv) işlem/müşteri/yanıt sayılarını, yanıt oranını ve 500 müşteri kümesi bootstrap tekrarından %95 aralıkları içerir. Aynı kişinin ziyaretleri bağımsız sayılmaz; aralıkların örtüşmesi resmi fark testi değildir.

Maslak'ın arıza onarım payı %{tr(100*maslak.ariza_orani,1)}; diğerlerinde yaklaşık %14–15'tir. Ortak müşteri tipi × işlem tipi dağılımıyla puanı {tr(maslak.ham_ortalama,3)}'den {tr(maslak.standart_ortalama,3)}'e değişir. Düzeltilmiş puanlarda İzmir1 {tr(izmir.standart_ortalama,3)} ile en düşük, Maslak en yüksektir; bu sıralama nedensel merkez etkisi değildir. [Bileşim dökümü](ciktilar/merkez_bilesim.csv) hücre örneklemlerini gösterir. Güncel müşteri tipiyle standardizasyon betimseldir; düzeltilmiş puanın belirsizlik aralığı hesaplanmadı.

![Servis merkezlerinde ham ve standart memnuniyet puanı](ciktilar/merkezler.svg)

**İş birimine yanıt:** “Merkezlerin puanlarında küçük farklar var, ancak hizmet verdikleri işler aynı zorlukta değil. Maslak daha çok arıza onarımı yapıyor; benzer müşteri ve işlem dağılımıyla karşılaştırınca kötü merkez olduğu sonucu desteklenmiyor. Anketi yanıtlamayanların görüşünü bilmiyoruz ve puanlarda belirsizlik var. Yönetim veya iş hacmi kararı öncesinde aynı tür işlerdeki şikâyetleri inceleyip yanıtsız müşterilerden de görüş toplayalım.”

## 2. Model, değerlendirme ve sınırlar

**Baseline**, eğitim sınıf oranını veren modeldir; **asıl model**, hızlı ve yorumlanabilir L2 düzenlemeli lojistik regresyondur. Müşteriler tabakalı ve sabit tohumla %60 eğitim / %20 doğrulama / %20 test ayrıldı: {tr(r['train_n'])} / {tr(r['validation_n'])} / {tr(r['test_n'])} kişi. Tabakalama azınlık temsilini, müşteri bazında ayrım bölüm tekilliğini korur. Doğrulama eşik seçimine, test son ölçüme ayrıldı. Sınırlandırma, medyanla eksik doldurma, eksik göstergeleri ve ölçekleme yalnız eğitimde öğrenildi. Bu ayrım benzer müşterileri değerlendirir; gelecek yıl başarısını kanıtlamaz.

**Sızıntı kontrolü:** güncel `crm_musteri_durumu`, tarihsiz `son_iletisim_notu`, kimlik ve tarihsel sürümü bilinmeyen demografi modele alınmadı. Servis/geri bildirimler gözlemle, araçlar kesime kadar satın alınmış olanlarla sınırlandı; hedef işlemleri yalnız hedef değişkenine girdi. LLM etiketleri churn modelinde kullanılmadı. Garanti satın almada, anket puanı servis döneminde biliniyor varsayıldı. Anket kayıt zamanı bulunmadığından üretimde doğrulanmalıdır.

**Metrik gerekçesi:** ROC-AUC eşikten bağımsız sıralamayı, average precision azınlık terk sınıfındaki kesinlik–yakalama dengesini ölçer. Precision@%20 iletişim listesinin isabetini, recall@%20 bu kapasiteyle yakalanan terk oranını gösterir. Accuracy tek başına yanıltıcıdır: baseline **{pct(bl['accuracy'])} doğrulukla sıfır terk yakalar**; modelin {pct(metrics['accuracy'])} doğruluğu daha düşük olsa da terkleri ayırt eder.

Kapasite verilmediği için %20 varsayıldı. Doğrulamada seçilen **{tr(r['esik'],4)}** eşik testte ayarlanmadı: iletişim oranı {pct(metrics['esikte_iletisim_orani'])}, precision {pct(metrics['precision'])}, recall {pct(metrics['recall'])}. En riskli {int(__import__('math').ceil(.2*r['test_n']))} kişide precision **{pct(metrics['precision_at_20pct'])}**, recall **{pct(metrics['recall_at_20pct'])}**. Test ROC-AUC **{tr(metrics['roc_auc'],3)}** (%95 aralık {tr(r['test_auc_bootstrap_95'][0],3)}–{tr(r['test_auc_bootstrap_95'][1],3)}), average precision **{tr(metrics['average_precision'],3)}**; baseline karşılıkları **{tr(bl['roc_auc'],3)} ve {tr(bl['average_precision'],3)}**. [Model sonuçları](ciktilar/model_sonuclari.json).

**En önemli beş değişken**, testte karıştırıldığında ortalama AUC düşüşüyle sıralandı:

{importance}

[Önem dökümünde](ciktilar/degisken_onemleri.csv) 10 tekrarın değişkenliği bulunur. İlişkili özellikler önemi paylaşır; önem nedensellik değildir. AUC 0,95'i aşmadı, yine de tarih ve alan kontrolleri yapıldı. **Üretim sınırı:** tek kesim tarihli sentetik veri; sahiplik, fiyatlar ve davranış değiştiğinde başarı düşebilir. Sonraki kesimlerde dış doğrulama, kalibrasyon ve küçük kontrollü iletişim pilotu gerekir.

## 3. LLM yöntemi, ölçüm ve aksiyon

Tohum 42 ile rastgele 200 kayıt seçildi; 36 farklı metin Codex aracılığıyla LLM ile etiketlenip birebir eşleşmeyle aktarıldı. [İlk istem](kod/llm_istem.txt), [ham yanıt](kod/llm_sohbet_etiketleri.json), [200 etiket](ciktilar/llm_etiketleri.csv) korunur. Kod saklanan çıktıyı aktarır; kural tabanlı etiketleme yapmaz.

**İnsan altın seti:** 200 kayıttan, ilk taslak etiketleme için seçilmiş 40 kimlik dışlanıp kalan 160 içinden tohum 44 ile yeni 40 kayıt seçildi. {human_method} [altin_set.csv](ciktilar/altin_set.csv) bu dosyanın birebir kopyasıdır. Kimlik/metin ve bütünlük doğrulandı; otomatik taslakları insan referansı olarak kullanmadım. Konular kümeye çevrilir; boş/anlamsız yorumda boş küme geçerlidir.

**İlk insan ölçümü:** duygu **{v1['duygu_dogru']}/40, {pct(v1['duygu_accuracy'])}**, macro-F1 **{tr(v1['duygu_macro_f1'],3)}**; konu tam küme eşleşmesi **{v1['konu_dogru']}/40, {pct(v1['konu_exact_match'])}**, micro-F1 **{tr(v1['konu_micro_f1'],3)}**. Herhangi bir uyuşmazlık {v1['uyusmazlik_kaydi']} kayıtta var. [Sınıf metrikleri](ciktilar/llm_basari.json).

**Nerede yanılıyor?**

- **Karışık/çekimser duygu:** Karışık sınıfında yakalama {mixed['ilk']['dogru']}/{mixed['ilk']['n']} → {mixed['bonus']['dogru']}/{mixed['bonus']['n']}. 9071 (“Harika bir deneyimdi, sadece üç hafta bekledim.”) ve 9330 (“Mükemmel değildi ama beklentimin altında da kalmadı.”) için Karışık verdim; LLM iki turda da tek kutbu seçti. Notlarım alternatif yoruma da yer verdiği için bunlar kesin hata değil, duygu sınırı farkıdır.
- **Fazla konu etiketi:** 9024/9622'de genel “Servis iyi” övgüsünden İş kalitesi çıkarıldı; somut onarım anlatılmıyor. 9091/9136'da parça beklemesine Süre, 9300'de bilgilendirmemeye Personel eklendi. Son iki fark konu sınırlarıyla ilgilidir; açık içerik yalnız referansa uymak için silinmedi.
- **Kısa/boş metin:** 9451 (“?”) ve 9639 (boş) için ilk istem Diğer zorunluluğu getirdi; benim konu etiketim boş kümedir. Bu, anlamadan çok yönerge uyumsuzluğudur.

### Bonus: insan bulgularına dayalı değerlendirme

[Bonus istemi](kod/llm_istem_bonus.txt) boş yorum politikasını, genel övgü/somut iş sonucu ayrımını ve duygu kurallarını netleştirdi. Aynı 36 metin yeniden etiketlenip 200 kayda aktarıldı. Kullanılan istem ve ham yanıt değiştirilmedi. [Girdi](kod/llm_bonus_girdi.json), [ham yanıt](kod/llm_bonus_ham_yanit.json), [yöntem kaydı](ciktilar/bonus_cikarim_kaydi.json). Üç turun başlangıç/bonus sonuçları karşılaştırıldı; ara tur duygu %95, konu %87,5.

**Aynı insan setinde başlangıç → bonus:** duygu **{pct(v1['duygu_accuracy'])} → {pct(v2['duygu_accuracy'])}**, macro-F1 **{tr(v1['duygu_macro_f1'],3)} → {tr(v2['duygu_macro_f1'],3)}**; konu tam eşleşmesi **{pct(v1['konu_exact_match'])} → {pct(v2['konu_exact_match'])}**, micro-F1 **{tr(v1['konu_micro_f1'],3)} → {tr(v2['konu_micro_f1'],3)}**. Uyuşmazlık **{v1['uyusmazlik_kaydi']} → {v2['uyusmazlik_kaydi']}**; {len(bonus['duzelen_idler'])} kayıt düzeldi, {len(bonus['yeni_uyusmazlik_idler'])} yeni fark oluştu, {len(bonus['suren_uyusmazlik_idler'])} fark sürdü. [Karşılaştırma](ciktilar/bonus_once_sonra.json), [40 eşleşme ve notlar](ciktilar/bonus_once_sonra_kayitlar.csv).

Düzelen {len(bonus['duzelen_idler'])} kayıt {u['duzelen_metin_sayisi']} farklı metindir: 9024/9622 istemdeki örnekle, 9451/9639 boş/anlamsız metin kuralıyla açıklanır; kalan 9524 duygu yorumu değişimidir. Benzersiz metin düzeyinde (n={u['n']}) duygu **{u1['duygu_dogru']}/{u['n']} → {u2['duygu_dogru']}/{u['n']}**, herhangi bir uyuşmazlık **{u1['uyusmazlik']}/{u['n']} → {u2['uyusmazlik']}/{u['n']}**. İstemdeki otopark örneği altın setteki bir yorumun yeniden ifadesidir; sonuçlar aynı örneklere uyumu gösterir ve genelleme başarısını iyimser gösterebilir. [Ayrıntılar](ciktilar/insan_degerlendirme.md).

**Ölçüm sınırı:** 40 kayıtta 25 farklı metin ve tek insan etiketleyici vardır. İnsan etiketleri geliştirme sırasında modelin bağlamında bulunduğundan, sonuçlar **aynı set üzerinde yapılan bir geliştirme karşılaştırmasıdır**; bağımsız veya kör test değildir. Turlar arasında model sürümlerinin aynı olduğu doğrulanmadığından, iyileşmenin tamamı yalnızca yönerge değişimine bağlanamaz. Yeni metinlerdeki başarı ve ikinci etiketleyiciyle uyum ölçülmedi.

**Üç aksiyon**, ilk denemenin kesim öncesi olumsuz etiketleriyle seçilen, eşik üzerindeki üç test müşterisi için LLM ile üretildi:

{act}

103088'in metnine (9524) Karışık, ‘Olumsuza yakın’ notu verdim; aday başlangıç turunun Olumsuz etiketiyle seçildi. Bonus etiketleriyle aynı koşulları yalnız {q['aksiyon_uygun_musteri_sayisi']['bonus']} müşteri karşılar. Kod saklanmış LLM aksiyonlarını aktarır. [Aksiyon yönergesi](ciktilar/aksiyon_istem.txt) süreçte kullanılan kısıtların kaydıdır; özgün konuşmadaki istemin birebir metni doğrulanamadı.

[Kanıt metinleri ve aksiyonlar](ciktilar/llm_aksiyonlar.csv) tarihleri içerir; eski şikâyet güncel görüşmede doğrulanmalıdır. İzinli aksiyon önerileri: sorunu dinleme/doğrulama, mevcut randevu sürecine yardım, yetkili ekibe iletme. Yetkiler doğrulanmalı; LLM izinli aksiyonlardan seçmeli, cümle kontrollü şablondan üretilmelidir. Kampanya/indirim/hediye/ücretsiz hizmet vaatleri denetlenmeli; temsilci onayı alınmalıdır. Sözcük taraması yeterli güvence değildir; iletişim gönderilmedi.

## 4. Taslak raporun eleştirisi

Sayılar benim analiz tanımım içindir; taslağın kodu bulunmadığından belirsiz uygulamalarda riski belirttim.

| Hata / iddia | Neden yanlış veya riskli? | Doğrusu |
|---|---|---|
| “8.400 müşteri”; “32.770 müşteri satırı” | Tekil müşteri {tr(q['dosyalar']['musteriler']['temiz_satir'])}; servis satırı müşteri değildir. | Ayrı özetleri birleştir; analiz {tr(r['n'])} tekil müşteridir. |
| Ortalama doldurunca veri eksiksiz | Yanıtsızların görüşü bilinmez; yapay puan belirsizliği azaltır. | Yanıt oranını raporla; %21 ve 3,94 ham sayıları yaklaşık doğrudur. |
| %84 doğruluk “sektör üstü, üretime hazır” | Baseline {pct(bl['accuracy'])}; sektör kıyası kaynaksızdır. | AP ve kapasite metriklerini baseline ile karşılaştır; dış doğrulama yap. |
| CRM önemi “veri kalitesi göstergesi” | Kaybedildi {status['Kaybedildi']['churn']}/{status['Kaybedildi']['n']} terk; Aktif {status['Aktif']['churn']}/{tr(status['Aktif']['n'])} terk. “Araç satıldı/Başka servise geçti/İlgilenmiyor/Ulaşılamadı” notlarında {churn_lost}/{n_lost} terk; rutin notlarda (kampanya, hatırlatma, memnuniyet araması) {tr(return_contact)}/{tr(n_contact)} gelen. Güçlü sızıntı şüphesi. | Kesimde bilinebilirliği doğrulanmayan alanları çıkar; yüksek ilişkiyi kalite kanıtı sayma. |
| Rastgele %80/20 genellemeyi ölçer | Servis satırları bölünürse aynı müşteri iki bölümde bulunabilir; taslağın uygulaması bilinmiyor. | Müşteri bazında ayır; gelecek dönem için zamansal doğrulama yap. |
| AUC 0,99 güvenilir başarı | Vaka >0,95 için sızıntı incelemesi istiyor; AUC ile accuracy farklı ölçülerdir, beraberlikleri tek başına çelişki değildir. | Önce tarih/alan sızıntısını araştır; taslak modeli yeniden üretmeden güvenme. |
| Uç değerler etkilemiyor | Etki incelemesi gösterilmemiş; {qc['negatif_tutar']} negatif tutar, {qc['negatif_km']} negatif km var. | Geçersizleri temizle; pozitif uçların etkisini ayrıca değerlendir. |
| Maslak “en kötü”, hacim aktarılmalı | İzmir1 ile ham fark {tr(abs(maslak.ham_ortalama-izmir.ham_ortalama),3)}; bileşim ve belirsizlik ihmal edilmiş. | Benzer işleri karşılaştır; küçük fark tek başına ceza gerekçesi değildir. |
| Memnuniyet 3,71 / 3,98 | Benim gözlem/müşteri tanımımda {tr(groups.get_group(1).ort_memnuniyet.mean(),2)} / {tr(groups.get_group(0).ort_memnuniyet.mean(),2)}; tanım farklı olabilir. | Dönem, eksik politikası ve ağırlığı belirt; sayıları yeniden hesapla. |
| p=0,03 → hipotez %97 doğru | p-değeri hipotezin doğruluk olasılığı değildir; test hesabı bilinmiyor. | Sıfır hipotezi altında bu veya daha uç sonuç olasılığı olarak yorumla. |
| Puanı 0,3 artırmak terki %8 azaltır | Gözlemsel ilişki müdahale etkisini kanıtlamaz. | Etkiyi deney veya uygun nedensel tasarımla ölç. |

CRM tanısal sayımları [veri kalite dökümündedir](ciktilar/veri_kalite.json); bu alanlar modele girmedi.

## 5. Yapay zekâ kullanım günlüğü

**Araçlar ve görev paylaşımı:** Codex'e analiz akışını ve Python kodunu hazırlattım; başlangıç/bonus etiketlerini, taslak iddiaların incelemesini ve üç aksiyon önerisini LLM ile ürettim. Python/pandas/scikit-learn/SciPy hesaplamaları yürüttü; kontrol kodları da AI desteğiyle hazırlandı. 40 insan etiketini kendim verdim; otomatik taslakları referans yapmadım.

**İstem 1 — başlangıç etiketleme (birebir):**

> {first_prompt}

**İstem 2 — bonus:** [Tam istem](kod/llm_istem_bonus.txt), insan ölçümündeki konu sınırlarını ve boş yorum politikasını netleştirdi. İki istem [kullanım günlüğünde](ciktilar/llm_kullanim_gunlugu.txt) tam olarak korunur.

**Aracın yanıldığı örnek:** 9024/9622 “Servis iyi de otopark yok…” yorumuna LLM, Diğer yanında İş kalitesi ekledi. Somut onarım anlatılmadığından bu fazla etiketti. Kendim etiketlediğim setle karşılaştırma farkı gösterdi; metin incelemesi genel övgüden iş sonucu çıkarılması örüntüsünü ortaya koydu. İlk çıktı korundu; güncellenen yönergeyle fark giderildi.

**AI'ye devretmediğim iş:** 40 etiketi ve tereddüt notlarını kendim verdim; ölçüt AI'nin kendi çıktısı olamaz. İroniyi gözden geçirdim; etiketlerimi sonuca uydurmadım. Şirketin yetkilerini bilmediğimden aksiyon/kapasite onayını iş birimine bırakıyorum. [Bütünlük ve çalıştırma kontrolleri](ciktilar/kontrol_sonucu.txt).
'''
(P/'RAPOR.md').write_text(report)
print(f'Rapor ve iki görsel üretildi: {len(report.split())} kelime (boşlukla sayım).')
