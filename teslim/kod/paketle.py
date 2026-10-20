"""Yalnız güncel teslimi ve ham vaka girdilerini paketler."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[2]
output=ROOT/'teslim/aday_paketi.zip'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((ROOT/'teslim').rglob('*')):
  if p.is_file() and p!=output and not any(part.startswith('.') or part=='__pycache__' for part in p.relative_to(ROOT/'teslim').parts):
   z.write(p,p.relative_to(ROOT))
 for p in sorted((ROOT/'veri').glob('*.csv')):z.write(p,p.relative_to(ROOT))
 for name in ['VAKA.md','veri_sozlugu.md','analiz_raporu_taslak.md']:z.write(ROOT/name,name)
with zipfile.ZipFile(output) as z:assert z.testzip() is None
print('Güncel ZIP hazır:',output)
