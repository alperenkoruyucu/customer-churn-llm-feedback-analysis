"""Ana hesaplar, insan altın seti, bonus ve teslim bağlantılarını doğrular."""
import json,hashlib,re
from urllib.parse import unquote
from xml.etree import ElementTree
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score,precision_score,recall_score,roc_auc_score
from duzen import ROOT,TESLIM,CIKTILAR as O,ALTIN,butunluk_kontrolu
n=butunluk_kontrolu()
q=json.loads((O/'veri_kalite.json').read_text());r=json.loads((O/'model_sonuclari.json').read_text())
b=pd.read_csv(O/'musteri_analiz.csv');l=pd.read_csv(O/'llm_etiketleri.csv',keep_default_na=False)
a=pd.read_csv(O/'llm_aksiyonlar.csv');human=pd.read_csv(ALTIN,keep_default_na=False)
assert len(b)==r['n']==b.musteri_id.nunique()==3973
assert b.churn.value_counts().to_dict()=={int(k):v for k,v in r['churn_dagilimi'].items()}
assert np.isfinite(b.risk).all() and b.risk.between(0,1).all()
assert b.groupby('bolum').size().to_dict()=={'egitim':r['train_n'],'dogrulama':r['validation_n'],'test':r['test_n']}
t=b[b.bolum.eq('test')];pred=t.risk>=r['esik'];m=r['test_model']
for actual,saved in [(accuracy_score(t.churn,pred),m['accuracy']),(precision_score(t.churn,pred),m['precision']),(recall_score(t.churn,pred),m['recall']),(roc_auc_score(t.churn,t.risk),m['roc_auc'])]:assert np.isclose(actual,saved)
assert q['ozellik_kesim_kontrolu'] and not {'crm_musteri_durumu','son_iletisim_notu'}&set(q['ozellikler'])
assert len(a)==3 and a.musteri_id.is_unique and a.bolum.eq('test').all() and a.risk.ge(r['esik']).all()
assert pd.to_datetime(a.tarih).between('2022-01-01','2025-06-30').all()
assert l.set_index('geri_bildirim_id').loc[a.geri_bildirim_id,'duygu'].eq('Olumsuz').all()
for s in a.aksiyon:assert not any(x in s.lower() for x in ['%','indirim','ücretsiz','hediye','kampanya'])
assert (O/'calistirma_uyarilari.log').stat().st_size==0
v3=pd.read_csv(O/'llm_etiketleri_bonus.csv',keep_default_na=False)
assert len(l)==len(v3)==200 and l.geri_bildirim_id.is_unique and v3.geri_bildirim_id.is_unique
assert l[['geri_bildirim_id','metin']].equals(v3[['geri_bildirim_id','metin']])
assert len(human)==40 and human.geri_bildirim_id.is_unique
assert set(human.geri_bildirim_id)<=set(l.geri_bildirim_id)
source=json.loads((O/'insan_altin_set_kaynak.json').read_text())
assert hashlib.sha256(ALTIN.read_bytes()).hexdigest()==source['sha256']
user=ROOT/'yeni_altin_set_etiketli.csv'
if user.exists():assert ALTIN.read_bytes()==user.read_bytes()
new=json.loads((O/'bonus_once_sonra.json').read_text());rows=pd.read_csv(O/'bonus_once_sonra_kayitlar.csv')
for version,metrics in zip(['ilk','bonus'],new['denemeler']):
 assert rows['duygu_dogru_'+version].mean()==metrics['duygu_accuracy']
 assert rows['konu_dogru_'+version].mean()==metrics['konu_exact_match']
 assert int(rows['uyusmazlik_'+version].sum())==metrics['uyusmazlik_kaydi']
assert new['altin_set_sha256']==source['sha256']
words=len((TESLIM/'RAPOR.md').read_text().split());assert 1200<=words<=2000,words
links=0
for path in TESLIM.rglob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):
  if '://' not in link and not link.startswith('#'):
   assert (path.parent/unquote(link.split('#')[0])).is_file(),(path,link)
   links+=1
for name in ['churn_bulgular.svg','merkezler.svg']:
 svg=ElementTree.parse(O/name).getroot();assert svg.tag.endswith('svg') and svg.findall('.//{http://www.w3.org/2000/svg}text')
assert not (TESLIM/'tarihsel').exists()
message=f'GEÇTİ: {n} korunan dosya, 3973 tekil müşteri, zaman/başarı/aksiyon kontrolleri, 200 ilk ve bonus etiketi, 40 değişmeyen insan etiketi, {words} kelime, {links} yerel bağlantı, iki SVG. Bu ölçüm kör test değil geliştirme karşılaştırmasıdır.'
(O/'kontrol_sonucu.txt').write_text(message+'\n');print(message)
