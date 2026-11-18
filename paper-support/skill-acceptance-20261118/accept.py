from html.parser import HTMLParser
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import numpy as np

from make_cases import ROOT, PRIVATE, PUBLIC


class Mismatch(ValueError):
    """A concrete delivered-output mismatch."""


def read(path):
    return json.loads(Path(path).read_text())


def compare(actual, expected, label, atol=1e-7):
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise Mismatch(f'{label}: object required')
        for key, value in expected.items():
            if key not in actual:
                raise Mismatch(f'{label}.{key}: missing')
            compare(actual[key], value, f'{label}.{key}', atol)
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise Mismatch(f'{label}: expected list of length {len(expected)}')
        for i, (a, e) in enumerate(zip(actual, expected)):
            compare(a, e, f'{label}[{i}]', atol)
    elif type(expected) is float:
        if type(actual) not in (float, int) or not np.isclose(actual, expected, atol=atol, rtol=1e-6):
            raise Mismatch(f'{label}: numeric mismatch')
    elif type(expected) is int:
        if type(actual) not in (int, float) or actual != expected:
            raise Mismatch(f'{label}: exact number mismatch')
    elif type(actual) is not type(expected) or actual != expected:
        raise Mismatch(f'{label}: exact value mismatch')


def array(actual, expected, label, atol):
    if np.shape(actual) != np.shape(expected) or not np.allclose(actual, expected, atol=atol, rtol=1e-6):
        raise Mismatch(f'{label}: different shape or samples')


class ReportText(HTMLParser):
    def __init__(self, keys):
        super().__init__()
        self.keys = keys
        self.prepared = {}
        self.pending = None

    def handle_starttag(self, _tag, attrs):
        key = dict(attrs).get('id')
        if key in self.keys:
            if key in self.prepared:
                raise Mismatch(f'report repeats id {key}')
            self.pending = key
            self.prepared[key] = ''

    def handle_endtag(self, _tag):
        self.pending = None

    def handle_data(self, text):
        if self.pending:
            self.prepared[self.pending] += text


def parse_field(text, typ):
    text = text.strip()
    if typ is float or typ is int:
        try:
            return float(text)
        except ValueError as err:
            raise Mismatch('expected a printed number') from err
    return None if typ is type(None) and text == 'null' else text


def artifact_check(workspace, artifact, public, expected):
    import mne

    kind = artifact['kind']
    path = workspace / artifact['path']
    if not path.is_file() or path.stat().st_size == 0:
        raise Mismatch(f'{artifact["path"]}: missing or empty')
    if kind == 'epochs':
        output = mne.read_epochs(path, preload=True, verbose=False)
        compare(output.ch_names, public['channel_names'], 'epoch channels')
        array(output.get_data()*1e6, artifact['samples_uV'], 'epoched samples', 1e-6)
        array(output.times, expected['times_s'], 'epoch time axis', 1e-9)
        compare(output.events[:,0].tolist(), expected['retained_event_samples'], 'epoch event samples')
    elif kind == 'evoked':
        output = mne.read_evokeds(path, condition=None, verbose=False)
        if len(output) != 1:
            raise Mismatch('one evoked waveform is required')
        compare(output[0].ch_names, public['channel_names'], 'evoked channels')
        array(output[0].data*1e6, artifact['samples_uV'], 'evoked samples', 1e-6)
        array(output[0].times, artifact['times_s'], 'evoked time axis', 1e-8)
    elif kind == 'bids':
        from mne_bids import BIDSPath, read_raw_bids
        bp = BIDSPath(subject='01', task='check', datatype='eeg', root=workspace/'bids',
                      suffix='eeg', extension='.vhdr')
        restored = read_raw_bids(bp, verbose=False)
        compare(restored.ch_names, public['channel_names'], 'BIDS channel identities')
        compare(restored.get_channel_types(), public['types'], 'BIDS channel types')
        compare(restored.info['bads'], public['bads'], 'BIDS bad channels')
        compare(restored.info['sfreq'], public['sfreq'], 'BIDS sampling rate')
        array(restored.get_data()*1e6, public['data_uV'], 'BIDS round-trip samples', 1e-4)
        labels = {v:k for k,v in public['event_id'].items()}
        compare(restored.annotations.description.tolist(),
                [labels[r[2]] for r in public['events_original_samples']], 'BIDS annotations')
        compare(np.rint(restored.annotations.onset*restored.info['sfreq']).astype(int).tolist(),
                expected['relative_event_samples'], 'BIDS annotated sample identities')
        sidecar = read(path.with_suffix('.json'))
        compare(sidecar['EEGReference'], 'synthetic common reference', 'BIDS EEGReference')
        compare(sidecar['PowerLineFrequency'], public['line_freq'], 'BIDS line frequency')
        if not (workspace/'bids/dataset_description.json').is_file():
            raise Mismatch('missing BIDS dataset_description.json')
    elif kind == 'svg':
        root = ET.parse(path).getroot()
        plots = [child for node in root.iter() if node.attrib.get('id') == 'aea-data'
                 for child in node.iter() if child.tag.endswith('}path')]
        if len(plots) != 1:
            raise Mismatch('one actual SVG path with the declared artist id is required')
        coordinates = [float(x) for x in re.findall(
            r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?', plots[0].attrib['d'])]
        array(np.array(coordinates).reshape(-1,2), artifact['points_pt'], 'SVG plotted points', 1e-4)
        content = path.read_text()
        if any(public[key] not in content for key in ('x_label','y_label')):
            raise Mismatch('SVG missing one of the required axis labels')
    elif kind == 'methods':
        content = path.read_text()
        for k,v in expected.items():
            match = re.findall(rf'^\s*{re.escape(k)}\s*=\s*(.+?)\s*$', content, re.M)
            if len(match) != 1:
                raise Mismatch(f'methods.md missing or repeating {k}')
            compare(parse_field(match[0], type(v)), v, f'Methods {k}')
        paragraph = '\n'.join(l for l in content.splitlines() if '=' not in l and l.strip())
        if len(paragraph.split()) < 12:
            raise Mismatch('Methods paragraph is missing')
    elif kind == 'report':
        parser = ReportText(expected)
        parser.feed(path.read_text())
        for k,v in expected.items():
            if k not in parser.prepared:
                raise Mismatch(f'HTML missing field {k}')
            compare(parse_field(parser.prepared[k], type(v)),
                    round(v,3) if type(v) is float else v, f'HTML {k}')
        receipt = workspace/'REPRO_RECEIPT.md'
        if not receipt.is_file():
            raise Mismatch('reproduction receipt missing')
        text = receipt.read_text()
        if public['source_file'] not in text or not re.search(rf'\b{expected["seed"]}\b', text):
            raise Mismatch('reproduction receipt missing input provenance or actual seed')
    else:
        raise RuntimeError(f'unknown artifact check {kind}')


def verify(task_id, workspace):
    reference = read(PRIVATE / f'{task_id}.json')
    public = read(PUBLIC / f'{task_id}.json')['input']
    expected = reference['expected']
    try:
        compare(read(workspace/'result.json'), expected, 'result.json', reference['atol'])
        if reference['artifact']:
            artifact_check(workspace, reference['artifact'], public, expected)
    except (OSError, ValueError, TypeError, KeyError, IndexError, ET.ParseError, RuntimeError) as err:
        return {'passed':False,'reason':str(err)[:600]}
    return {'passed':True,'reason':'checked required result fields and named artifact, if requested'}


def review_delivery(task_id, out, workspace):
    check = verify(task_id, workspace)
    if check['passed']:
        if not (workspace/'analysis.py').is_file() or not (workspace/'analysis.py').stat().st_size:
            return {'passed':False,'reason':'analysis.py absent'}
        trace = out/'execution_trace.jsonl'
        used = trace.is_file() and any('analysis.py' in json.loads(l).get('code','')
                                      for l in trace.read_text().splitlines())
        if not used:
            return {'passed':False,'reason':'execution trace does not reference saved analysis.py'}
    return check
