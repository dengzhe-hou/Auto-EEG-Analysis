"""Re-run the deterministic checks on published first deliveries without model access."""
from collections import Counter
import csv
import json
from pathlib import Path
import tempfile
import zipfile

from accept import read, review_delivery

ROOT=Path(__file__).resolve().parent


def rows(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def replay(name):
    folder=ROOT/name
    sessions=rows(folder/'SESSION_RESULTS.csv')
    schedules=read(ROOT/'SCHEDULE.json')
    assert len(sessions)==len({r['session'] for r in sessions})==len(schedules)==198
    assert all((r['session'],r['task'],r['skill'],int(r['rep']))==
               (s['session'],s['task'],s['skill'],s['rep']) for r,s in zip(sessions,schedules))
    count=Counter()
    with tempfile.TemporaryDirectory(prefix='aea-archived-') as tmp:
        path=Path(tmp)
        with zipfile.ZipFile(folder/'first-deliveries.zip') as archive:
            assert {p.split('/')[0] for p in archive.namelist()}=={r['session'] for r in sessions}
            archive.extractall(path)
        for row in sessions:
            origin=path/row['session']
            recorded=read(origin/'CHECK.json')
            first=read(origin/'FIRST_RESULT.json')
            assert first['status']==row['status']
            if first['status']=='submitted':
                checked=review_delivery(row['task'],origin,origin/'workspace')
                assert checked['passed']==recorded['passed'],(row['session'],checked,recorded)
            else:
                assert first['status']=='failed' and not recorded['passed'],first
            assert row['passed']==str(recorded['passed'])
            count[(row['skill'],'passed' if recorded['passed'] else 'failed')]+=1
    table=rows(folder/'PER_SKILL.csv')
    for row in table:
        assert row['assigned']==row['checked']=='9'
        assert count[(row['skill'],'passed')]==int(row['passed'])
        assert count[(row['skill'],'failed')]==int(row['failed'])
    total=sum(count[(r['skill'],'passed')] for r in table)
    independent=read(folder/'INDEPENDENT_AGGREGATE_CHECK.json')
    assert total==independent['passed_deliveries'] and len(table)==22
    return {'checked':sum(count.values()),'accepted':total,'skills':len(table)}


if __name__=='__main__':
    print(json.dumps({name:replay(name) for name in ('original','retest')},indent=2))
