"""İlk LLM ve insan bulgularına dayalı bonusu aynı 40 insan etiketiyle ölçer."""
import hashlib,json,re
import numpy as np
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import accuracy_score,f1_score,classification_report
from duzen import TESLIM,CIKTILAR as O,ALTIN,butunluk_kontrolu
butunluk_kontrolu()
g=pd.read_csv(ALTIN,keep_default_na=False)
selected=json.loads((O/'insan_ornekleme_kaydi.json').read_text())
assert len(g)==40 and g.geri_bildirim_id.is_unique
assert set(g.geri_bildirim_id)==set(selected['yeni_kimlikler'])
s=pd.read_csv(O/'llm_orneklem.csv',keep_default_na=False)
pool=s[~s.geri_bildirim_id.isin(selected['dislanan_onceki_kimlik'])].sort_values('geri_bildirim_id')
assert set(pool.sample(40,random_state=44).geri_bildirim_id)==set(g.geri_bildirim_id)
inputs=json.loads((TESLIM/'kod/llm_bonus_girdi.json').read_text())
raw=json.loads((TESLIM/'kod/llm_bonus_ham_yanit.json').read_text())
assert [x['i'] for x in inputs]==[x['i'] for x in raw]==list(range(36))
assert [x['metin'] for x in inputs]==json.loads((TESLIM/'kod/llm_girdi_metinleri.json').read_text())
topics=['randevu','fiyat','süre','personel','iş_kalitesi','yedek_parça','temizlik','diğer']
sentiments=['Olumlu','Olumsuz','Karışık','Alakasız']
for x in raw:
 assert set(x)=={'i','duygu','konular'} and x['duygu'] in sentiments
 assert isinstance(x['konular'],list) and set(x['konular'])<=set(topics)
 assert len(x['konular'])==len(set(x['konular']))
lookup={x['metin']:y for x,y in zip(inputs,raw)}
bonus=s.copy()
bonus['duygu']=[lookup[t]['duygu'] for t in s.metin]
bonus['konular']=['|'.join(lookup[t]['konular']) for t in s.metin]
bonus.to_csv(O/'llm_etiketleri_bonus.csv',index=False)
def topic_set(text):
 values=[v.strip() for v in re.split(r'[,|]',text) if v.strip()]
 assert set(values)<=set(topics) and len(values)==len(set(values))
 return set(values)
assert g.duygu.isin(sentiments).all()
mlb=MultiLabelBinarizer(classes=topics)
truth=mlb.fit_transform(g.konular.map(topic_set))
rows=g.copy();summary=[]
for version,filename in [('ilk','llm_etiketleri.csv'),('bonus','llm_etiketleri_bonus.csv')]:
 llm=pd.read_csv(O/filename,keep_default_na=False)
 assert len(llm)==200 and llm.geri_bildirim_id.is_unique
 match=g[['geri_bildirim_id','metin']].merge(llm,on='geri_bildirim_id',how='left',suffixes=('_insan',''),validate='one_to_one',indicator=True)
 assert match['_merge'].eq('both').all() and match.metin.eq(match.metin_insan).all()
 pred=mlb.transform(match.konular.map(topic_set))
 rows['duygu_'+version]=match.duygu;rows['konular_'+version]=match.konular
 rows['duygu_dogru_'+version]=g.duygu.eq(match.duygu)
 rows['konu_dogru_'+version]=(truth==pred).all(axis=1)
 rows['uyusmazlik_'+version]=~rows['duygu_dogru_'+version]|~rows['konu_dogru_'+version]
 metrics=dict(deneme=version,n=40,duygu_dogru=int(rows['duygu_dogru_'+version].sum()),konu_dogru=int(rows['konu_dogru_'+version].sum()),duygu_accuracy=accuracy_score(g.duygu,match.duygu),duygu_macro_f1=f1_score(g.duygu,match.duygu,labels=sentiments,average='macro',zero_division=0),konu_exact_match=accuracy_score(truth,pred),konu_micro_f1=f1_score(truth,pred,average='micro',zero_division=0),uyusmazlik_kaydi=int(rows['uyusmazlik_'+version].sum()))
 summary.append(metrics)
 detail=dict(metrics,duygu_siniflar=classification_report(g.duygu,match.duygu,labels=sentiments,output_dict=True,zero_division=0),konu_siniflar=classification_report(truth,pred,target_names=topics,output_dict=True,zero_division=0))
 (O/('llm_basari.json' if version=='ilk' else 'bonus_basari.json')).write_text(json.dumps(detail,ensure_ascii=False,indent=2))
rows['degisim']=np.select([rows.uyusmazlik_ilk&~rows.uyusmazlik_bonus,~rows.uyusmazlik_ilk&rows.uyusmazlik_bonus,rows.uyusmazlik_ilk&rows.uyusmazlik_bonus],['duzeldi','yeni_uyusmazlik','suruyor'],default='iki_deneme_de_dogru')
rows.to_csv(O/'bonus_once_sonra_kayitlar.csv',index=False)
rows[rows.degisim.ne('iki_deneme_de_dogru')].to_csv(O/'llm_uyusmazliklar.csv',index=False)
pd.DataFrame(summary).to_csv(O/'bonus_once_sonra_metrikler.csv',index=False)
result=dict(denemeler=summary,duzelen_idler=rows.loc[rows.degisim.eq('duzeldi'),'geri_bildirim_id'].tolist(),yeni_uyusmazlik_idler=rows.loc[rows.degisim.eq('yeni_uyusmazlik'),'geri_bildirim_id'].tolist(),suren_uyusmazlik_idler=rows.loc[rows.degisim.eq('suruyor'),'geri_bildirim_id'].tolist(),altin_set_sha256=hashlib.sha256(ALTIN.read_bytes()).hexdigest())
# Tekrarlı metinlerin ağırlığını ayrıca göster; 40 kayıt bağımsız 40 metin değildir.
for text,group in rows.groupby('metin',dropna=False):
 assert group.duygu.nunique()==1 and len({tuple(sorted(topic_set(x))) for x in group.konular})==1
unique_rows=rows.drop_duplicates('metin')
result['benzersiz_metin']={'n':len(unique_rows),'duzelen_metin_sayisi':int(unique_rows.degisim.eq('duzeldi').sum()),'denemeler':[{'deneme':version,'duygu_dogru':int(unique_rows['duygu_dogru_'+version].sum()),'konu_dogru':int(unique_rows['konu_dogru_'+version].sum()),'uyusmazlik':int(unique_rows['uyusmazlik_'+version].sum())} for version in ['ilk','bonus']]}
result['karisik_sinifi']={version:{'n':int(rows.duygu.eq('Karışık').sum()),'dogru':int((rows.duygu.eq('Karışık')&rows['duygu_dogru_'+version]).sum())} for version in ['ilk','bonus']}
(O/'bonus_once_sonra.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
butunluk_kontrolu();print(json.dumps(result,ensure_ascii=False,indent=2))
