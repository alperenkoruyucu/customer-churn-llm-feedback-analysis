from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'teslim/ciktilar'
f=pd.read_csv(ROOT/'veri/geri_bildirimler.csv').sample(200,random_state=42).sort_values('geri_bildirim_id')
texts=f.metin.fillna('').unique().tolist()
labels=json.loads((Path(__file__).parent/'llm_sohbet_etiketleri.json').read_text())
assert texts==json.loads((Path(__file__).parent/"llm_girdi_metinleri.json").read_text()), "Ham metin veya örneklem değişti; saklanan LLM çıktısı geçerli değil"
assert len(texts)==len(labels)
allowed={'randevu','fiyat','süre','personel','iş_kalitesi','yedek_parça','temizlik','diğer'}
lookup={}
for t,(s,topics) in zip(texts,labels):
 assert s in {'Olumlu','Olumsuz','Karışık','Alakasız'} and topics and set(topics)<=allowed
 lookup[t]=(s,'|'.join(topics))
f['duygu']=[lookup[t][0] for t in f.metin.fillna('')];f['konular']=[lookup[t][1] for t in f.metin.fillna('')]
f.to_csv(OUT/'llm_etiketleri.csv',index=False)
pd.DataFrame([(t,*lookup[t]) for t in texts],columns=['metin','duygu','konular']).to_csv(OUT/'llm_metin_sozlugu.csv',index=False)
print('200 etiket; şema ve birebir eşleşme doğrulandı')
