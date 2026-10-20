"""Ham veri, insan referansı ve ilk sonuçların bütünlüğünü doğrular."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
TESLIM=ROOT/'teslim'
CIKTILAR=TESLIM/'ciktilar'
ALTIN=CIKTILAR/'altin_set.csv'
def butunluk_kontrolu():
 manifest=json.loads((CIKTILAR/'korunan_dosyalar_sha256.json').read_text())
 for path,digest in manifest.items():
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
 return len(manifest)
