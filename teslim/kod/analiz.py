from pathlib import Path
import json, hashlib, platform
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
threadpool_limits(limits=1)
from scipy import stats
from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score,average_precision_score,accuracy_score,precision_score,recall_score,f1_score,confusion_matrix
from sklearn.inspection import permutation_importance
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'teslim/ciktilar';OUT.mkdir(exist_ok=True)
START=pd.Timestamp('2022-01-01');CUT=pd.Timestamp('2025-06-30');END=pd.Timestamp('2026-06-30')
def save(d,n):d.to_csv(OUT/(n+'.csv'),index=False)
def dates(col):
 def parse(v):
  for fmt in ['%Y-%m-%d','%Y-%m-%d %H:%M:%S','%d/%m/%Y','%d.%m.%Y']:
   try:return pd.to_datetime(v,format=fmt,errors='raise')
   except (ValueError,TypeError):pass
  return pd.NaT
 return col.map(parse)
raw={n:pd.read_csv(ROOT/'veri'/f'{n}.csv') for n in ['musteriler','araclar','servis_kayitlari','geri_bildirimler']}
m,a,s,f=[raw[n].drop_duplicates().copy() for n in raw]
audit={'dosyalar':{},'kontroller':{}}
for n,key,d in zip(raw,['musteri_id','arac_id','kayit_id','geri_bildirim_id'],[m,a,s,f]):
 audit['dosyalar'][n]={'ham_satir':len(raw[n]),'tam_tekrar':int(raw[n].duplicated().sum()),'temiz_satir':len(d),'anahtar_tekrari':int(d[key].duplicated().sum()),'eksikler':raw[n].isna().sum().to_dict(),'sha256':hashlib.sha256((ROOT/'veri'/f'{n}.csv').read_bytes()).hexdigest()}
 assert d[key].is_unique
for d,cols in [(m,['ilk_temas_tarihi']),(a,['satin_alma_tarihi','garanti_bitis_tarihi']),(s,['servis_tarihi']),(f,['tarih'])]:
 for c in cols:
  d[c]=dates(d[c]);audit['kontroller'][c+'_gecersiz']=int(d[c].isna().sum())
for name,x,col,parent,pkey in [('arac_musteri',a,'musteri_id',m,'musteri_id'),('servis_arac',s,'arac_id',a,'arac_id'),('geribildirim_arac',f,'arac_id',a,'arac_id')]:
 audit['kontroller'][name+'_yetim']=int((~x[col].isin(parent[pkey])).sum())
assert all(v==0 for k,v in audit['kontroller'].items() if 'yetim' in k)
s=s.merge(a[['arac_id','musteri_id','satin_alma_tarihi']],on='arac_id',validate='many_to_one');f=f.merge(a[['arac_id','musteri_id','satin_alma_tarihi']],on='arac_id',validate='many_to_one')
audit['kontroller'].update({'negatif_tutar':int((s.tutar<0).sum()),'negatif_km':int((s.km<0).sum()),'gecersiz_puan':int((s.memnuniyet_puani.notna()&~s.memnuniyet_puani.between(1,5)).sum()),'satinalma_oncesi_servis':int((s.servis_tarihi<s.satin_alma_tarihi).sum()),'satinalma_oncesi_geribildirim':int((f.tarih<f.satin_alma_tarihi).sum()),'gecersiz_dogum':int((m.dogum_yili.notna()&~m.dogum_yili.between(1925,2007)).sum())})
s.loc[s.tutar<0,'tutar']=np.nan;s.loc[s.km<0,'km']=np.nan;s.loc[~s.memnuniyet_puani.between(1,5),'memnuniyet_puani']=np.nan
obs=s[s.servis_tarihi.between(START,CUT)].copy();target=s[s.servis_tarihi.gt(CUT)&s.servis_tarihi.le(END)]
pop=s.loc[s.servis_tarihi.lt(CUT),'musteri_id'].unique()
audit['kontroller']['yalniz_kesim_gunu_musteri']=len(set(obs.musteri_id)-set(pop))
audit['kontroller']['hedef_oncesi_yeni_arac_servisleri']=int((obs.satin_alma_tarihi>CUT).sum())
# Araç satın alma bilgisi kesim sonrasına aitse geçmiş özellik olarak kullanılamaz.
obs=obs[obs.satin_alma_tarihi.le(CUT)]
g=obs.groupby('musteri_id').agg(son_servis=('servis_tarihi','max'),frequency=('kayit_id','size'),monetary=('tutar',lambda x:x.sum(min_count=1)),ort_memnuniyet=('memnuniyet_puani','mean'),anket_yanit=('memnuniyet_puani','count'),ort_km=('km','mean'),ariza_orani=('servis_tipi',lambda x:x.eq('Arıza Onarım').mean()),merkez_sayisi=('servis_merkezi','nunique'))
g['recency_gun']=(CUT-g.pop('son_servis')).dt.days;g['anket_yanit_orani']=g.anket_yanit/g.frequency;g=g.drop(columns='anket_yanit')
known=a[a.satin_alma_tarihi.le(CUT)].copy();known['arac_yasi']=2025-known.model_yili;known['garanti_bitti']=(known.garanti_bitis_tarihi<CUT).astype(int)
v=known.groupby('musteri_id').agg(arac_sayisi=('arac_id','size'),ort_arac_yasi=('arac_yasi','mean'),garanti_bitti_orani=('garanti_bitti','mean'))
fo=f[f.tarih.between(START,CUT)&f.satin_alma_tarihi.le(CUT)&f.tarih.ge(f.satin_alma_tarihi)]
fg=fo.groupby('musteri_id').agg(geri_bildirim_sayisi=('geri_bildirim_id','size'))
base=pd.DataFrame({'musteri_id':sorted(pop)})
for d in [g,v,fg]:base=base.merge(d,on='musteri_id',how='left',validate='one_to_one')
base['geri_bildirim_sayisi']=base.geri_bildirim_sayisi.fillna(0);base['churn']=(~base.musteri_id.isin(target.musteri_id)).astype(int)
assert base.musteri_id.is_unique and len(base)==len(pop)
# Demografi de geçmiş sürümü doğrulanamadığından modele girmez; merkez bileşimi için betimsel kullanılır.
obs=obs.merge(m[['musteri_id','musteri_tipi']],on='musteri_id',validate='many_to_one')
features=[c for c in base if c not in ['musteri_id','churn']];X=base[features];y=base.churn
trainval,test=train_test_split(np.arange(len(base)),test_size=.2,random_state=42,stratify=y)
train,val=train_test_split(trainval,test_size=.25,random_state=43,stratify=y.iloc[trainval])
class QuantileClip(BaseEstimator,TransformerMixin):
 def fit(self,X,y=None):self.low_=np.nanquantile(X,.01,axis=0);self.high_=np.nanquantile(X,.99,axis=0);return self
 def transform(self,X):return np.clip(np.asarray(X),self.low_,self.high_)
class SafeLogistic(LogisticRegression):
 # Bu macOS ortamında BLAS matmul uyarıları görüldü; aynı toplamı einsum ile hesapla.
 def decision_function(self,X):
  return np.einsum('ij,j->i',np.asarray(X),self.coef_[0],optimize=False)+self.intercept_[0]
model=Pipeline([('clip',QuantileClip()),('impute',SimpleImputer(strategy='median',add_indicator=True)),('scale',StandardScaler()),('model',SafeLogistic(max_iter=2000,C=1,solver='liblinear',random_state=42))]);model.fit(X.iloc[train],y.iloc[train])
xt=model[:-1].transform(X.iloc[test]);linear=np.sum(xt*model[-1].coef_[0],axis=1)+model[-1].intercept_[0]
assert np.isfinite(xt).all() and np.isfinite(model[-1].coef_).all()
assert np.allclose(linear,model[-1].decision_function(xt),rtol=1e-12,atol=1e-12)
vp=model.predict_proba(X.iloc[val])[:,1];threshold=float(np.quantile(vp,.8))
baseline=DummyClassifier(strategy='prior').fit(X.iloc[train],y.iloc[train])
def metrics(p,yy,t):
 pred=p>=t;k=max(1,int(np.ceil(.2*len(yy))));idx=np.argsort(-p,kind='stable')[:k];yy=np.asarray(yy)
 return {'roc_auc':roc_auc_score(yy,p),'average_precision':average_precision_score(yy,p),'accuracy':accuracy_score(yy,pred),'precision':precision_score(yy,pred,zero_division=0),'recall':recall_score(yy,pred),'f1':f1_score(yy,pred),'precision_at_20pct':float(yy[idx].mean()),'recall_at_20pct':float(yy[idx].sum()/yy.sum()),'esikte_iletisim_orani':float(pred.mean()),'confusion_matrix':confusion_matrix(yy,pred).tolist()}
p=model.predict_proba(X.iloc[test])[:,1];assert np.isfinite(p).all();bp=baseline.predict_proba(X.iloc[test])[:,1]
res={'n':len(base),'churn_dagilimi':y.value_counts().to_dict(),'train_n':len(train),'validation_n':len(val),'test_n':len(test),'esik':threshold,'validation':metrics(vp,y.iloc[val],threshold),'test_model':metrics(p,y.iloc[test],threshold),'test_baseline':metrics(bp,y.iloc[test],.5),'baseline_top20_notu':'Eşit riskte müşteri ID sırası; sıralama becerisi yok.'}
rng=np.random.default_rng(44);aucs=[]
for _ in range(500):
 ix=rng.integers(0,len(test),len(test));yy=y.iloc[test].to_numpy()[ix]
 if len(np.unique(yy))==2:aucs.append(roc_auc_score(yy,p[ix]))
res['test_auc_bootstrap_95']=np.quantile(aucs,[.025,.975]).tolist()
imp=permutation_importance(model,X.iloc[test],y.iloc[test],scoring='roc_auc',n_repeats=10,random_state=42)
save(pd.DataFrame({'ozellik':features,'auc_azalis':imp.importances_mean,'tekrar_std':imp.importances_std}).sort_values('auc_azalis',ascending=False),'degisken_onemleri')
base['risk']=model.predict_proba(X)[:,1];base['bolum']='egitim';base.loc[val,'bolum']='dogrulama';base.loc[test,'bolum']='test';save(base,'musteri_analiz')
summary=base.groupby('churn')[['recency_gun','frequency','monetary','ort_memnuniyet']].agg(['mean','median','count']);summary.to_csv(OUT/'churn_bulgular.csv')
# Merkez: müşteri kümesi bootstrap; ham ortalamalar yalnızca yanıt verenleri temsil eder.
cent=[]
for center,d in obs.groupby('servis_merkezi'):
 z=d.groupby('musteri_id').memnuniyet_puani.agg(['sum','count']);z=z[z['count']>0];bs=[]
 for _ in range(500):
  zz=z.iloc[rng.integers(0,len(z),len(z))];bs.append(zz['sum'].sum()/zz['count'].sum())
 cent.append({'merkez':center,'islem':len(d),'musteri':d.musteri_id.nunique(),'yanit':d.memnuniyet_puani.count(),'yanit_orani':d.memnuniyet_puani.notna().mean(),'ham_ortalama':d.memnuniyet_puani.mean(),'ci_alt':np.quantile(bs,.025),'ci_ust':np.quantile(bs,.975),'kurumsal_orani':d.musteri_tipi.eq('Kurumsal').mean(),'ariza_orani':d.servis_tipi.eq('Arıza Onarım').mean()})
c=pd.DataFrame(cent)
# Ortak müşteri tipi × işlem tipi ağırlıkları, gözlemsel standardizasyon.
weights=obs.groupby(['musteri_tipi','servis_tipi']).size()/len(obs)
for i,row in c.iterrows():
 means=obs[obs.servis_merkezi.eq(row.merkez)].groupby(['musteri_tipi','servis_tipi']).memnuniyet_puani.mean().reindex(weights.index)
 c.loc[i,'standart_ortalama']=float((means*weights).sum()) if means.notna().all() else np.nan
save(c.sort_values('ham_ortalama'),'merkez_karsilastirma');save(obs.groupby(['servis_merkezi','musteri_tipi','servis_tipi']).agg(islem=('kayit_id','size'),yanit=('memnuniyet_puani','count'),ortalama=('memnuniyet_puani','mean')).reset_index(),'merkez_bilesim')
# Doğrudan çoktan çoğa birleşim satır sayısını, birleşimi bellekte kurmadan hesapla.
ns=raw['servis_kayitlari'].groupby('arac_id').size();nf=raw['geri_bildirimler'].groupby('arac_id').size()
audit['kontroller']['ham_servis_feedback_left_join_satir']=int((ns*nf.reindex(ns.index).fillna(1).clip(lower=1)).sum())
audit['kontroller']['ham_memnuniyet_eksik_orani']=float(raw['servis_kayitlari'].memnuniyet_puani.isna().mean());audit['kontroller']['ham_memnuniyet_ortalama']=float(raw['servis_kayitlari'].memnuniyet_puani.mean())
# Tarih bilgisi yalnızca tanısal; model girdileri açık izin listesi.
audit['ozellikler']=features;audit['ozellik_kesim_kontrolu']=bool(obs.servis_tarihi.le(CUT).all() and fo.tarih.le(CUT).all() and known.satin_alma_tarihi.le(CUT).all())
(OUT/'veri_kalite.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2,default=lambda x:int(x)))
(OUT/'model_sonuclari.json').write_text(json.dumps(res,ensure_ascii=False,indent=2,default=lambda x:int(x)))
# LLM olumsuz metinler: sadece kesim öncesi, bilinen araç, test müşterileri.
l=pd.read_csv(OUT/'llm_etiketleri.csv');lf=fo.merge(l[['geri_bildirim_id','duygu','konular']],on='geri_bildirim_id',validate='one_to_one');neg=lf[lf.duygu.eq('Olumsuz')].sort_values('tarih').drop_duplicates('musteri_id',keep='last')
candidates=base[base.bolum.eq('test')].merge(neg[['musteri_id','geri_bildirim_id','tarih','metin','konular']],on='musteri_id',validate='one_to_one').sort_values('risk',ascending=False);save(candidates.head(3),'aksiyon_adaylari')
# Tek müşteri başına ortalama puanla Welch testi: taslak testi yeniden üretmek değildir.
vals=[base.loc[base.churn.eq(k),'ort_memnuniyet'].dropna() for k in [0,1]];tt=stats.ttest_ind(*vals,equal_var=False)
res['musteri_puani_welch']={'p':float(tt.pvalue),'t':float(tt.statistic),'n0':len(vals[0]),'n1':len(vals[1])};(OUT/'model_sonuclari.json').write_text(json.dumps(res,ensure_ascii=False,indent=2))
# Güncel CRM alanlarıyla hedef ilişkisi: tanısal kanıt, model girdisi değildir.
crm_check=base[['musteri_id','churn']].merge(m[['musteri_id','crm_musteri_durumu','son_iletisim_notu']],on='musteri_id',validate='one_to_one')
audit['crm_hedef_tanisi']={col:{str(k):{'n':int(v['size']),'churn':int(v['sum'])} for k,v in crm_check.groupby(col).churn.agg(['size','sum']).to_dict('index').items()} for col in ['crm_musteri_durumu','son_iletisim_notu']}
# Kesim öncesi ve aidiyeti doğrulanan geri bildirimlerde aday sayısı.
audit['aksiyon_uygun_musteri_sayisi']={}
for version,filename in [('ilk','llm_etiketleri.csv'),('bonus','llm_etiketleri_bonus.csv')]:
 labels=pd.read_csv(OUT/filename,keep_default_na=False)
 eligible_feedback=fo.merge(labels[['geri_bildirim_id','duygu']],on='geri_bildirim_id',validate='one_to_one')
 eligible_customers=base[base.bolum.eq('test')&base.risk.ge(threshold)].merge(eligible_feedback[eligible_feedback.duygu.eq('Olumsuz')][['musteri_id']],on='musteri_id')
 audit['aksiyon_uygun_musteri_sayisi'][version]=int(eligible_customers.musteri_id.nunique())
(OUT/'veri_kalite.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2,default=lambda x:int(x)))
print(json.dumps(res,ensure_ascii=False,indent=2));print(c.to_string(index=False));print(summary.to_string());print(audit['kontroller'])
