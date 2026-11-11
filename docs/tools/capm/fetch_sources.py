"""Explicit source acquisition; never called by rendering or offline execution."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT/'logs/capm/sources'


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 FinEco academic teaching'})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read(), response.headers.get('Content-Type','')


def main():
    RUN.mkdir(parents=True, exist_ok=True)
    sources = {
        'factors.zip': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip',
        'industries.zip': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Industry_Portfolios_CSV.zip',
        'factor-description.html': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html',
        'industry-description.html': 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html',
        'ang-chen-w11903.pdf': 'https://www.nber.org/papers/w11903.pdf',
        'frazzini-pedersen-2014.pdf': 'https://research.cbs.dk/files/60082899/lasse_heje_pedersen_et_al_betting_against_beta_publishersversion.pdf',
        'fama-french-1992.pdf': 'https://home.cerge-ei.cz/petrz/GDN/Fama_French_92.pdf',
        'newey-manual.pdf': 'https://www.stata.com/manuals/tsnewey.pdf',
    }
    records=[]
    for name,url in sources.items():
        target=RUN/name
        try:
            if target.exists():
                body=target.read_bytes();content_type='previously acquired'
            else:
                body,content_type=fetch(url)
                if name.endswith('.zip'):assert body.startswith(b'PK')
                if name.endswith('.pdf'):assert body.startswith(b'%PDF-')
                target.write_bytes(body)
            records.append({'file':name,'url':url,'bytes':len(body),
                'sha256':hashlib.sha256(body).hexdigest(),'content_type':content_type,'status':'OK'})
        except Exception as e:
            records.append({'file':name,'url':url,'status':'FAILED','error':str(e)})
    papers={
        'Ang-Chen-2007':'10.1016/j.jempfin.2005.12.001',
        'Baker-Bradley-Wurgler-2011':'10.2469/faj.v67.n1.4',
        'Fama-French-1992':'10.1111/j.1540-6261.1992.tb04398.x',
        'Frazzini-Pedersen-2014':'10.1016/j.jfineco.2013.10.005',
        'Jensen-1968':'10.1111/j.1540-6261.1968.tb00815.x',
        'Sharpe-1964':'10.1111/j.1540-6261.1964.tb02865.x',
    }
    metadata={}
    for name,doi in papers.items():
        try:
            body,_=fetch('https://api.crossref.org/works/'+doi)
            m=json.loads(body)['message'];metadata[name]={k:m.get(k) for k in ['DOI','title','author','container-title','volume','issue','page','published','link']}
        except Exception as e:metadata[name]={'error':str(e),'doi':doi}
    report={'retrieved_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'downloads':records,'crossref':metadata,
        'paper_storage':'Private local reading copies only; not public chapter assets.'}
    (RUN/'acquisition.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'downloads':[{k:v for k,v in r.items() if k in ['file','status','bytes','error']} for r in records],
        'metadata':{k:v.get('title',v.get('error')) for k,v in metadata.items()}},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
