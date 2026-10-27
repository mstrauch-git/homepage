#!/usr/bin/env python3
"""Fetch only public ORCID Works into publications.json. Standard library only."""
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ORCID = '0000-0002-5291-5531'
ROOT = pathlib.Path(__file__).resolve().parents[1]
API = 'https://pub.orcid.org/v3.0'


def request_json(url, headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=35) as response:
        return json.load(response)


def value(obj):
    return (obj or {}).get('value') if isinstance(obj, dict) else None


def date_part(obj, key):
    return value((obj or {}).get(key))


def main():
    client_id = os.environ['ORCID_CLIENT_ID'].strip()
    client_secret = os.environ['ORCID_CLIENT_SECRET'].strip()
    token_data = urllib.parse.urlencode({'client_id': client_id, 'client_secret': client_secret,
                                         'grant_type': 'client_credentials', 'scope': '/read-public'}).encode()
    token = request_json('https://orcid.org/oauth/token', {'Accept': 'application/json',
                         'Content-Type': 'application/x-www-form-urlencoded'}, token_data)['access_token']
    headers = {'Accept': 'application/json', 'Authorization': 'Bearer ' + token}
    works = request_json(f'{API}/{ORCID}/works', headers)
    records = []
    seen = set()
    for group in works.get('group', []):
        summaries = group.get('work-summary') or []
        if not summaries:
            continue
        # One entry per ORCID grouping; prefer summary with richer metadata.
        summary = max(summaries, key=lambda s: sum(bool(s.get(k)) for k in ('publication-date','external-ids','journal-title','url')))
        put_code = summary.get('put-code')
        detail = {}
        if put_code is not None:
            try:
                detail = request_json(f'{API}/{ORCID}/work/{put_code}', headers)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
                print(f'Warning: work {put_code} detail unavailable: {exc}', file=sys.stderr)
        source = detail or summary
        title = value((source.get('title') or {}).get('title')) or value((summary.get('title') or {}).get('title'))
        if not title:
            continue
        date = source.get('publication-date') or summary.get('publication-date') or {}
        year = date_part(date, 'year')
        journal = value(source.get('journal-title')) or value(summary.get('journal-title'))
        identifiers = (source.get('external-ids') or summary.get('external-ids') or {}).get('external-id') or []
        doi = next((item.get('external-id-value') for item in identifiers if (item.get('external-id-type') or '').lower() == 'doi' and item.get('external-id-value')), None)
        doi = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', doi, flags=re.I).strip() if doi else None
        url = value(source.get('url')) or value(summary.get('url'))
        if doi:
            url = 'https://doi.org/' + urllib.parse.quote(doi, safe='/()-.;:')
        contributors = (source.get('contributors') or {}).get('contributor') or []
        authors = [value((person.get('credit-name') or {})) for person in contributors]
        authors = [a for a in authors if a]
        key = ('doi:' + doi.lower()) if doi else ('title:' + re.sub(r'\W+', '', title.casefold()))
        if key in seen:
            continue
        seen.add(key)
        records.append({'title': title, 'year': year, 'journal': journal,
                        'authors': authors, 'type': source.get('type') or summary.get('type'),
                        'doi': doi, 'url': url})
    records.sort(key=lambda r: (int(r['year']) if str(r['year'] or '').isdigit() else 0, r['title'].casefold()), reverse=True)
    # Never replace a successful snapshot with an unexpectedly empty result.
    if not records:
        raise RuntimeError('ORCID returned no usable public Works; existing publications.json left unchanged')
    output = {'orcid': ORCID, 'updated': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d'), 'works': records}
    target = ROOT / 'publications.json'
    temp = target.with_suffix('.json.tmp')
    temp.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(target)
    print(f'Wrote {len(records)} works to {target}')


if __name__ == '__main__':
    main()
