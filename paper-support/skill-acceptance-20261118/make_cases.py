
from collections import Counter
from itertools import permutations, product
import json
from pathlib import Path
import re

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'inputs'
PRIVATE = ROOT / 'references'
SNAPSHOT = ROOT / 'snapshot'
CHANNELS = ['Fz', 'Cz', 'Pz']
tasks = []


def json_value(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    raise TypeError(type(obj))


def save(path, obj):
    path.write_text(json.dumps(obj, default=json_value, allow_nan=False, indent=2) + '\n')


def case(skill, name, description, data, expected, artifact=None, atol=1e-7):
    task = {'id': skill + '-' + name, 'skill': 'eeg-' + skill, 'operation': name,
            'request': description, 'fields': list(expected)}
    if artifact:
        task['artifact'] = artifact['path']
    tasks.append(task)
    save(PUBLIC / (task['id'] + '.json'), {'task': task, 'input': data})
    save(PRIVATE / (task['id'] + '.json'),
         {'expected': expected, 'atol': atol, 'artifact': artifact})


def audit_cases():
    settings = {'roi': ['Cz', 'Pz'], 'window_ms': [200, 300], 'contrast': 'target-standard',
                'observation_unit': 'subject', 'unit': 'uV', 'correction': 'holm'}
    for name, overrides, issues in [
        ('matched', {}, []),
        ('window', {'window_ms': [220, 300]}, ['window_ms']),
        ('unit-of-analysis', {'observation_unit': 'trial', 'unit': 'V'}, ['observation_unit', 'unit'])
    ]:
        plan = {'analysis_plan': settings, 'execution_receipt': {**settings, **overrides}}
        case('audit', name, 'Act as the assigned independent reviewer of this supplied analysis record. '
             'Check the six frozen plan fields against the execution receipt. In result.json return '
             'verdict ("pass" or "fail") and issues (sorted list of mismatched field names). '
             'This is a bounded audit of agreement on these fields.',
             plan, {'verdict': 'fail' if issues else 'pass', 'issues': issues})


def behavior_cases():
    trial = [11, 12, 13, 14, 15, 16]
    case('behavior', 'correct-trial-rt',
         'Summarize accuracy over all trials and mean RT in ms over correct trials only, in order A, B. '
         'Report accuracy, mean_rt_ms, and retained_rt_trials as lists.',
         {'condition': ['A', 'B', 'A', 'B', 'A', 'B'], 'correct': [True, True, False, True, True, False],
          'rt_ms': [325, 450, 250, 410, 365, 505]},
         {'accuracy': [2/3, 2/3], 'mean_rt_ms': [345., 430.], 'retained_rt_trials': [2, 2]})
    case('behavior', 'response-assignment',
         'Assign each stimulus the first still-unused response in [100, 350) ms after onset within its block. '
         'Process stimuli in input order. Return rt_ms as a list with null for missed trials and unused_response_ids sorted.',
         {'stimulus_ms': [10, 420, 550, 1010], 'stimulus_blocks': ['a', 'a', 'a', 'b'],
          'response_ms': [170, 670, 1190, 1250], 'response_blocks': ['a', 'a', 'b', 'b'],
          'response_ids': [1, 2, 3, 4]},
         {'rt_ms': [160, 250, None, 180], 'unused_response_ids': [4]})
    case('behavior', 'identity-join',
         'Join EEG and behavior strictly on the trial ID, retaining EEG row order and reporting unmatched '
         'behavior IDs. On the matched trials from one subject fit OLS RT in ms against EEG in uV with an '
         'intercept. Return trial_ids, missing_on_eeg, and slope_ms_per_uV.',
         {'eeg_trial_ids': [11, 13, 16, 15], 'eeg_uV': [1, 4, 3, 2],
          'behavior_trial_ids': trial[::-1], 'rt_ms': [360, 320, 509, 400, 700, 280]},
         {'trial_ids': [11, 13, 16, 15], 'missing_on_eeg': [12, 14], 'slope_ms_per_uV': 40.})


def bids_cases():
    for name, channels, sigs, events, bads, offset in [
        ('signals', ['Fz', 'Cz'], [7, 11], [113, 256, 381], [], 0),
        ('channel-status', ['Cz', 'VEOG', 'Fz'], [8, 2, 13], [87, 301, 402], ['Fz'], 0),
        ('sample-origin', ['Pz', 'Cz'], [5, 12], [117, 270, 439], [], 900)
    ]:
        sfreq = 128
        data = [15*np.sin(2*np.pi*f*np.arange(512)/sfreq+.2) for f in sigs]
        event_rows = [[e+offset, 0, 4 if i % 2 == 0 else 9] for i, e in enumerate(events)]
        inp = {'channel_names': channels, 'types': ['eog' if x == 'VEOG' else 'eeg' for x in channels],
               'sfreq': sfreq, 'data_uV': data, 'bads': bads, 'first_samp': offset,
               'events_original_samples': event_rows, 'event_id': {'target': 4, 'standard': 9},
               'line_freq': 50}
        case('bids', name, 'Build an MNE Raw from the input, converting uV to V and preserving channel types, '
             'bad status and first_samp. Write EEG-BIDS in BrainVision format with mne-bids under bids/, '
             'subject 01, task check, no session or run. Preserve the supplied event semantics and sample identities. '
             'Set synthetic EEG reference to "synthetic common reference" and line_freq as supplied. '
             'Read back and report relative_event_samples (relative to first saved sample), bad_channels, and sfreq.',
             inp, {'relative_event_samples': events, 'bad_channels': bads, 'sfreq': sfreq},
             {'kind': 'bids', 'path': 'bids/sub-01/eeg/sub-01_task-check_eeg.vhdr'})


def entropy_cases():
    x = np.random.default_rng(91512).choice([-.8, -.2, .3, .8, 1.4], size=47).astype(float)
    case('complexity', 'sampen',
         'Calculate standard sample entropy for the supplied single-channel series, m=2, threshold r=0.45 '
         'in the same units, Chebyshev strict distance < r. For both lengths use the same starting positions '
         'that permit length m+1; count unique unordered pairs and exclude self-matches. Report counts_m, '
         'counts_m_plus_1, and sample_entropy using natural logs.',
         {'series': x, 'm': 2, 'r': .45},
         (lambda a,b: {'counts_m': a, 'counts_m_plus_1': b, 'sample_entropy': -np.log(b/a)})(
             *[sum(max(abs(x[i+k]-x[j+k]) for k in range(m)) < .45
                   for i in range(45) for j in range(i+1,45)) for m in (2,3)]))
    x = np.random.default_rng(415).permutation(41)
    counts = Counter(tuple(np.argsort(x[i:i+3])) for i in range(len(x)-2))
    case('complexity', 'permutation-entropy',
         'For order 3, delay 1, calculate the normalized permutation entropy of this single channel. '
         'Report pattern_counts as counts in lexicographic order of the six permutations of [0,1,2], '
         'and normalized_perm_entropy with normalization log(3!).',
         {'series': x}, {'pattern_counts': [counts[p] for p in permutations(range(3))],
             'normalized_perm_entropy': -sum((v/sum(counts.values()))*np.log(v/sum(counts.values()))
                 for v in counts.values())/np.log(6)})
    x = np.random.default_rng(180).normal(size=29)
    def phi(m):
        arr = np.lib.stride_tricks.sliding_window_view(x, m)
        p = np.mean(np.max(np.abs(arr[:,None,:]-arr[None,:,:]),axis=-1) < .65,axis=1)
        return np.log(p).mean()
    case('complexity', 'approximate-entropy',
         'Calculate approximate entropy at m=2 using Chebyshev strict distance < 0.65 and self-matches. '
         'For each embedding length use all fitting windows and take the mean log neighbor fraction. '
         'Report phi_m, phi_m_plus_1, and approximate_entropy.', {'series': x, 'm': 2, 'r': .65},
         {'phi_m': phi(2), 'phi_m_plus_1': phi(3), 'approximate_entropy': phi(2)-phi(3)})


def connectivity_cases():
    x = np.vstack(([1, 4, 5, 2, 8, 4], [4, -2, -3, 0, -7, -2], [2, 0, 4, 1, 8, 0]))
    case('connectivity', 'pearson',
         'Compute the off-diagonal Pearson correlations for the pairs Fz-Cz, Fz-Pz, Cz-Pz in that order '
         'and report edges. Use the whole supplied continuous signal with no preprocessing.',
         {'channels': CHANNELS, 'signal': x}, {'edges': np.corrcoef(x)[(0,0,1),(1,2,2)]})
    a = [.1,.9,1.8,1.4,2.,2.4,1.1]
    b = [.2,0.,2.1,1.4,1.3,3.,2.]
    case('connectivity', 'plv',
         'Calculate temporal PLV of two channels from the provided narrowband phase arrays in radians. '
         'Return plv and n_samples. The phase extraction has already been performed.',
         {'phase_a': a, 'phase_b': b},
         {'plv': abs(sum(np.exp(1j*(p-q)) for p,q in zip(a,b)))/len(a), 'n_samples': len(a)})
    x = [1.3, 0.7, -0.5, 2.2, -0.1, 0.9]
    n = len(x)
    case('connectivity', 'debiased-wpli2',
         'Use trial-level imaginary cross-spectrum samples at one frequency and one edge. '
         'Return ordinary wpli and debiased squared wpli2. Use the debiased moment formula with '
         'self-products removed in both numerator and denominator.',
         {'imaginary_cross_spectrum': x},
         {'wpli': abs(sum(x))/sum(map(abs,x)),
          'wpli2': sum(x[i]*x[j] for i in range(n) for j in range(i+1,n)) /
                   sum(abs(x[i]*x[j]) for i in range(n) for j in range(i+1,n))})


def decoding_cases():
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    for name, variant in [('held-out-subjects', 0), ('held-out-blocks', 1), ('balanced-null', 2)]:
        rng = np.random.default_rng(2711+variant)
        groups = np.repeat(np.arange(4), 6)
        y = np.tile([0,0,0,1,1,1], 4)
        X = rng.normal(0, .3, size=(24,3,5))
        if variant<2:
            X[y==1,:,2:4] += 1.4
            if variant==1:
                X[y==0,:,4] += .8
        # Same specified estimator; independent explicit leave-one-group-out fit loop.
        preds = np.zeros((len(y), X.shape[2]), int)
        for k in range(X.shape[2]):
            for g in np.unique(groups):
                test = groups == g
                classifier = make_pipeline(StandardScaler(), LogisticRegression(
                    C=1, solver='liblinear', random_state=42, max_iter=1000))
                preds[test,k] = classifier.fit(X[~test,:,k], y[~test]).predict(X[test,:,k])
        case('decoding', name, 'Perform time-resolved decoding with one whole group held out at a time. '
             'At each time sample independently, fit StandardScaler inside each fold followed by '
             'LogisticRegression(C=1, solver="liblinear", random_state=42, max_iter=1000). '
             'Return predictions in original row order (trial by time), accuracy at each time and chance_accuracy. '
             'These are engineering fixtures; inferential testing is outside this assigned operation.',
             {'features': X, 'labels': y, 'groups': groups}, {'predictions': preds,
                 'accuracy': (preds==y[:,None]).mean(axis=0), 'chance_accuracy': .5})


def epoch_cases():
    for name,i in [('event-lock',0),('baseline',1),('trial-rejection',2)]:
        sfreq=100
        x = np.vstack([np.sin(np.arange(160)*.19), 3*np.cos(np.arange(160)*.08)])
        centers = np.array([35, 75, 114])
        t = np.arange(-10, 21)
        if i == 2:
            x[0,75+2] = 150
        kept = [0, 2] if i == 2 else [0,1,2]
        arr = np.array([x[:, centers[k]+t] for k in kept])
        if i == 1:
            arr = arr - arr[:,:,:11].mean(axis=2, keepdims=True)
        baseline = [-.10, 0] if i==1 else None
        gate = 75 if i==2 else None
        case('epoch',name, 'Using MNE, create epochs from the source EEG in uV (convert to V), '
             'with events on the supplied raw sample grid, the indicated inclusive time limits and baseline. '
             'If reject_peak_to_peak_uV is supplied, apply it to EEG channels only. Save epochs to check-epo.fif. '
             'Return retained_event_samples, times_s and n_dropped.',
             {'raw_uV': x,'channel_names':['Fz','Cz'],'sfreq':sfreq, 'events':[[int(c),0,1] for c in centers],
              'event_id':{'stimulus':1}, 'tmin':-.10,'tmax':.20,'baseline':baseline,'reject_peak_to_peak_uV':gate},
             {'retained_event_samples': centers[kept], 'times_s':t/sfreq, 'n_dropped':3-len(kept)},
             {'kind':'epochs','path':'check-epo.fif','samples_uV':arr})


def erp_cases():
    for name,i in [('condition-mean',0),('signed-difference',1),('fixed-window-roi',2)]:
        t = np.arange(-20,81)/100.
        labels = ['A','B','A','B','B']
        a = np.random.default_rng(32+i).normal(0, .35, size=(5,3,len(t)))
        a[np.array(labels)=='B',:,30:51] += (i+1) * np.array([1.,2.,3.])[:,None]
        e = a[[0,2]].mean(axis=0) if i==0 else a[[1,3,4]].mean(axis=0)-a[[0,2]].mean(axis=0)
        mask = (t>=.1)&(t<=.3)
        how = 'condition A mean' if i==0 else 'condition B minus condition A'
        case('erp',name, f'Build MNE epochs using the supplied clean epoch arrays, with no additional processing. '
             f'Calculate the {how} evoked waveform for all three channels. Save a single evoked to check-ave.fif. '
             'Return roi_mean_uV (equal weight over Cz/Pz and inclusive 0.1–0.3 s), '
             'n_window_samples, and n_condition_trials as [count A, count B].',
             {'epochs_uV':a,'labels':labels,'channel_names':CHANNELS,'sfreq':100,'tmin':-.2},
             {'roi_mean_uV': e[1:][:,mask].mean(), 'n_window_samples': 21,'n_condition_trials':[2,3]},
             {'kind':'evoked','path':'check-ave.fif','samples_uV':e,'times_s':t})


def figure_cases():
    for name, i, lab in [('erp-wave',0,'Amplitude (uV)'), ('delta-wave',1,'Difference (uV)'),
                          ('spectrum',2,'Power (uV^2/Hz)')]:
        x = np.arange(5.)
        y = np.array([.2, .6, 1.1, .9, .3]) * (1 if i==0 else -1 if i==1 else 2)
        unit = 'Time (s)' if i<2 else 'Frequency (Hz)'
        # SVG points use a fixed physical figure size and axes box specified publicly.
        coords = np.column_stack((288*(.2+.6*(x+1)/6), 216*(.8-.6*(y+3)/6)))
        case('figure',name, 'Render the supplied data as a line in Matplotlib, using figsize=(4,3), '
             'fig.add_axes([.2,.2,.6,.6]), xlim=(-1,5), ylim=(-3,3), and the supplied axis labels. '
             'Set line gid="aea-data". Save fig.svg without tight crop, so the actual SVG data path can be read back. '
             'Return n_points and x_label and y_label.',
             {'x':x,'y':y,'x_label':unit,'y_label':lab},
             {'n_points':5,'x_label':unit,'y_label':lab},
             {'kind':'svg','path':'fig.svg','points_pt':coords})


def group_cases():
    a=np.array([1.,6.,3.,2.,3.,4.,3.5])
    b=np.array([.7,1.,2.,2.6,4.6])
    x=np.array([2.,1.,3.,4.,2.,5.])
    y=np.array([1.2,.8,3.5,2.6,1.,3.8])
    designs=[
        ('welch-two-group','two-sided independent Welch t test',{'group_a':a,'group_b':b},
         stats.ttest_ind(a,b,equal_var=False),[len(a),len(b)]),
        ('paired-subjects','two-sided paired t test on A minus B',{'A':x, 'B':y},
         stats.ttest_1samp(x-y,0),[len(x),len(y)]),
        ('one-way-f','one-way between-subject ANOVA',{'groups':[a,b,[.9,2.2,2.3,1.8,1.3]]},
         stats.f_oneway(a,b,[.9,2.2,2.3,1.8,1.3]),[7,5,5])]
    for name,method,inp,res,n in designs:
        case('group-compare',name, 'Test independent participant-level summaries using '+method+
             '. Return statistic, p_value and n_per_group in input order. Each element is one participant value. '
             'Check the specified test path and unit of analysis; no cluster inference is assigned.',
             inp, {'statistic':res.statistic,'p_value':res.pvalue,'n_per_group':n})


def ica_cases():
    rng=np.random.default_rng(860)
    sources=rng.normal(size=(3,40))
    sources-=sources.mean(axis=1,keepdims=True)
    mixing=np.array([[1.,.2,.1], [.2,1.3,.4], [.3,.24,1.15]])
    x=mixing@sources
    for name,exclude in [('replay-none',[]),('remove-one',[0]),('remove-two',[1,2])]:
        keep=[j for j in range(3) if j not in exclude]
        case('ica',name, 'Apply the supplied fixed full-rank ICA decomposition to these centered data. '
             'Use the matching saved unmixing/mixing pair, zero only the approved component indices and '
             'reconstruct. Do not refit. Return cleaned_uV (channel by sample) and applied_exclusions.',
             {'channel_data_uV':x,'unmixing':np.linalg.inv(mixing),'mixing':mixing,'approved_exclusions':exclude},
             {'cleaned_uV':mixing[:,keep]@sources[keep],'applied_exclusions':exclude})


def methods_cases():
    for name,i in [('acquisition',0),('epoching',1),('retained-and-seed',2)]:
        acq={'sampling_hz':250,'reference': 'FCz' if i==0 else None}
        ex={'n_trials':20+i,'n_excluded':3+i*2,'executed_seed':73+i,'planned_seed':14,
            'epoch_start_sample':-25-i*5,'epoch_end_sample':150+i*10,'band_hz':[.2, 35]}
        vals={'sampling_hz':250,'reference':acq['reference'] or 'not recorded',
              'retained_trials':ex['n_trials']-ex['n_excluded'],'seed':ex['executed_seed'],
              'epoch_start_s':ex['epoch_start_sample']/250,'epoch_end_s':ex['epoch_end_sample']/250}
        case('methods-text',name, 'Draft a concise, truthful Methods paragraph from the acquisition '
             'and executed-stage records. Save methods.md with the paragraph plus one machine-readable line '
             "of the form field = value for each requested result field. Use 'not recorded' for absent reference. "
             'Report actual retained trial count, executed seed, and epoch times in s. Save the same field '
             'values as result.json.',
             {'acquisition':acq,'execution':ex}, vals,
             {'kind':'methods','path':'methods.md'})


def microstate_cases():
    labels=[0,0,0,1,1,2,2,2,0,2,-1,-1,1,0,0,1,2]
    c=np.zeros((3,3),int)
    for a,b in zip(labels[:-1], labels[1:]):
        if a>=0 and b>=0 and a!=b:
            c[a,b]+=1
    case('microstate','transitions', 'Calculate the observed transition count and row-normalized probability '
         'matrices for labels 0–2. Skip adjacent repeats and all pairs touching -1, with no bridging gaps. '
         'Report counts and probabilities (source row, destination column).',
         {'labels':labels}, {'counts':c,'probabilities':c/c.sum(1,keepdims=True)})
    case('microstate','coverage', 'Compute each state coverage as percent of labeled samples, in order 0,1,2. '
         'Return coverage_pct and n_labeled.', {'labels':labels},
         {'coverage_pct':[100*labels.count(k)/15 for k in range(3)],'n_labeled':15})
    t=np.array([9.,3.,4.,1.,2.,3.,7.,4.])
    s=np.array([.9,.8,.6,.7,.23,.4,.8,.52])
    lab=np.array([0,0,1,1,-1,2,2,2])
    vals=s*s*t*t
    case('microstate','gev', 'Calculate the per-state GEV and total GEV from the supplied spatial '
         'correlation to each sample assigned state and GFP, using GFP-squared weighting. Denominator '
         'includes all sample powers, with no numerator contribution from unlabeled samples. '
         'Return gev_by_state in order 0,1,2 and gev_total as fractions.',
         {'label':lab,'gfp':t,'corr':s}, {'gev_by_state':[sum(vals[lab==k])/sum(t*t) for k in range(3)],
            'gev_total':sum(vals[lab>=0])/sum(t*t)})


def pipeline_cases():
    graph={'preprocess':[],'epoch':['preprocess'],'erp':['epoch'],'spectral':['preprocess'],'report':['erp','spectral']}
    for name,statuses,reuses,runnable,blocked in [
        ('start',{},[],['preprocess'],['epoch','erp','report','spectral']),
        ('resume',{'preprocess':'passed','epoch':'passed'},['epoch','preprocess'],['erp','spectral'],['report']),
        ('blocked-stage',{'preprocess':'passed','epoch':'failed'},['preprocess'],['spectral'],['epoch','erp','report'])
    ]:
        case('pipeline',name,'Produce the execution decision for this declared stage graph and saved '
             'status receipts. Reuse only passed stages, start only pending stages whose direct dependencies passed, '
             'and put failed and dependency-blocked stages in blocked. A failed stage awaits review in this plan. '
             'Return sorted lists reused, runnable, blocked. Only the next execution decision is requested.',
             {'dependencies':graph,'status':statuses}, {'reused':reuses,'runnable':runnable,'blocked':blocked})


def preprocess_cases():
    t=np.arange(400)/100.
    x=np.array([3*np.sin(2*np.pi*5*t), 4*np.cos(2*np.pi*8*t), 6*np.sin(2*np.pi*13*t+.4), np.cos(t)])
    base = {'raw_uV':x,'names':['Fz','Cz','Pz','VEOG'],'types':['eeg','eeg','eeg','eog'],'sfreq':100}
    case('preprocess','reference','Apply average reference to EEG only with no projection or optional filtering. '
         'Keep EOG unchanged. Report full samples_uV in original row order and channel_names.',
         base, {'samples_uV':np.r_[x[:3]-x[:3].mean(0), x[3:]],'channel_names':base['names']})
    case('preprocess','channels-and-crop','Select channels in requested order and crop by half-open sample '
         'interval [45, 123) of the original recording. Report samples_uV and channel_names without any other processing.',
         {**base,'pick':['Pz','Fz'],'samples':[45,123]},
         {'samples_uV':x[[2,0],45:123],'channel_names':['Pz','Fz']})
    t2=np.arange(200)/50.
    case('preprocess','resample-events','Resample the three EEG channels to 50 Hz using MNE resample, '
         'method fft, npad=0, boxcar window and jointly supplied events. All events are on both grids. '
         'Report new_sfreq, relative_event_samples, and samples_uV without another preprocessing step.',
         {**base,'raw_uV':x[:3],'names':base['names'][:3],'types':base['types'][:3],
          'new_sfreq':50,'events':[[40,0,1],[188,0,2],[212,0,1]]},
         {'new_sfreq':50,'relative_event_samples':[20,94,106],'samples_uV':
          [3*np.sin(2*np.pi*5*t2),4*np.cos(2*np.pi*8*t2),6*np.sin(2*np.pi*13*t2+.4)]})


def qc_cases():
    t = np.arange(1000)/1000.
    for name,i in [('clean',0),('constant-channel',1),('rapid-step',2)]:
        x = np.array([20*np.sin(2*np.pi*9*t), 13*np.cos(2*np.pi*5*t+.1)])
        if i==1:
            x[1,:]=2
        if i==2:
            x[0,350:355]=[180,-180,180,-180,180]
        case('qc',name, 'Evaluate the AEA amplitude QC rule on two EEG channels. Convert uV to V for '
             'the amplitude helper. Report sorted constant_channels and rapid_change_channels by their '
             'segment names, and bad_channel_candidates using the declared 5% duration criterion. '
             'Run QC on the original samples without applying cleaning or annotation changes.',
             {'signal_uV':x,'channel_names':['Fz','Cz'],'sfreq':1000},
             {'constant_channels':['Cz'] if i==1 else [],'rapid_change_channels':['Fz'] if i==2 else [],
              'bad_channel_candidates':['Cz'] if i==1 else []})


def recipe_cases():
    for i,name in enumerate(['meets-minimum','missing-marker','insufficient-trials']):
        markers={'stimulus/related':44,'stimulus/unrelated':43}
        if i==1:
            del markers['stimulus/unrelated']
        if i==2:
            markers['stimulus/unrelated']=17
        case('recipe',name, 'Check applicability of the AEA n400-semantic recipe from its frozen '
             'RECIPE.md header. Verify the supplied post-rejection counts, required markers, sampling rate, '
             'and channel count. Return eligible, missing_markers (sorted), insufficient_present_markers '
             '(sorted), and recipe_version. This is the recipe preflight operation.',
             {'recipe':'n400-semantic','channel_count':32,'sfreq':256,'marker_counts':markers},
             {'eligible':i==0,'missing_markers':['stimulus/unrelated'] if i==1 else [],
              'insufficient_present_markers':['stimulus/unrelated'] if i==2 else [],
              'recipe_version':'v0.1.0'})


def report_cases():
    for i,name in enumerate(['recorded-summary','include-missing','read-executed-seed']):
        produced={'roi_mean_uV':-1.725+i*.13,'n_trials':43+i,
                  'status':'unavailable' if i==1 else 'available','seed':31+i}
        if i==1:
            produced['roi_mean_uV']=None
        case('report',name,'Write report.html and REPRO_RECEIPT.md from the supplied executed-stage record. '
             'Use an HTML element with id matching each required key and its value as plain text '
             '(use "null" for missing value); round continuous values to 3 decimals in HTML only. '
             'Include the literal source artifact filename and executed seed in the reproducibility receipt. '
             'Return result.json with the same four facts at full precision.',
             {'executed_stage':produced,'source_file':'request.json','planned_seed':7},
             produced, {'kind':'report','path':'report.html'})


def source_cases():
    for name,i in [('ridge-inverse',0),('noise-normalized',1),('strong-regularization',2)]:
        G=np.array([[1.,.2],[.4,1.5],[-1.4,-1.7]])
        C=.2*np.eye(len(G))
        x=G@np.array([[2.,1.,4.,3.],[3.,2.,.2,-.6]])
        lam=[.25,.2,1.3][i]
        # Direct source-space least squares on the fixed gain; independent of sensor-space form.
        K=np.linalg.solve(G.T@G+lam*.2*np.eye(2),G.T)
        J=K@x
        if i==1:
            J=J/np.sqrt(np.diag(K@C@K.T))[:,None]
        case('source',name,'Use this fixed-orientation, referenced, supplied lead field and sensor covariance. '
             'Compute the identity-source-prior minimum-norm inverse with K=G.T @ inv(G@G.T + lambda2*C). '
             'Divide each source row by sqrt(diag(K@C@K.T)) only if normalize_noise is true. '
             'Report source_estimates and normalized (boolean).',
             {'gain':G,'noise_cov':C,'sensor_data':x,'lambda2':lam,'normalize_noise':i==1},
             {'source_estimates':J,'normalized':i==1})


def spectrum_cases():
    sf=128
    t=np.arange(384)/sf
    x=(.7*np.sin(2*np.pi*5*t) + 1.6*np.cos(2*np.pi*11*t+.3) + .9*np.sin(2*np.pi*22*t))
    # Explicit DFT, periodic Hann, equal-length tapered segments and mean removal.
    n=128
    k=np.arange(n)
    win=.5-.5*np.cos(2*np.pi*k/n)
    dft=np.exp(-2j*np.pi*np.outer(np.arange(n//2+1),k)/n)
    seg=np.array([x[i:i+n]-x[i:i+n].mean() for i in range(0,len(x)-n+1,64)])
    power=(abs((seg*win)@dft.T)**2).mean(0)/(sf*sum(win*win))
    power[1:-1]*=2
    inp={'data_uV':x,'sfreq':sf,'n_per_seg':n,'n_fft':n,'n_overlap':64}
    for name,desc,exp in [
        ('welch-band-power','Return alpha_power_uV2 as sum of PSD bins from 8 through 12 Hz inclusive times df.',
         {'alpha_power_uV2':sum(power[8:13])}),
        ('peak-frequency','Return alpha_peak_hz from the maximum bin in [8,12] Hz and its psd_uV2_per_hz.',
         {'alpha_peak_hz':11,'psd_uV2_per_hz':power[11]}),
        ('relative-power','Return beta_fraction from sum of PSD bins in [15,30] Hz divided by sum in [2,40] Hz.',
         {'beta_fraction':sum(power[15:31])/sum(power[2:41])})
    ]:
        case('spectral',name,'Compute one-sided mean Welch PSD in uV^2/Hz using periodic Hann, '
             'segment demeaning and explicit n_fft, n_per_seg and overlap. '+desc,inp,exp)


def stats_cases():
    x=np.array([.7,1.2,-.1,1.1,2.3,1.8])
    z=(x-x.mean())**2
    sd=np.sqrt(z.sum()/(len(x)-1))
    t=x.mean()*np.sqrt(len(x))/sd
    case('stats','one-sample-t','Test the six supplied participant contrasts against zero using a two-sided '
         'one-sample t test. Report t, df and p_two_sided. Keep the participant as the observation unit.',
         {'contrasts':x}, {'t':t,'df':5,'p_two_sided':2*stats.t.sf(abs(t),5)})
    case('stats','paired-effect','For the paired participant contrasts, compute Cohen dz with ddof=1, '
         'mean_difference and the two-sided 95% t interval ci95 on the mean.',
         {'contrasts':x}, {'dz':x.mean()/sd, 'mean_difference':x.mean(),
              'ci95':x.mean()+np.array([-1,1])*stats.t.ppf(.975,5)*sd/np.sqrt(len(x))})
    x=np.array([1,6,3,-1,2])
    p=np.mean([abs(sum(v*s for v,s in zip(x,signs)))>=abs(sum(x)) for signs in product([-1,1],repeat=5)])
    case('stats','exact-sign-flip','For the five participant contrasts, calculate the exact two-sided sign-flip '
         'test using the absolute mean as statistic. Include all 2^5 patterns including the observed, '
         'ties count as extreme, no added pseudocount. Report observed_abs_mean, n_patterns, and p_exact.',
         {'contrasts':x}, {'observed_abs_mean':abs(x.mean()),'n_patterns':32,'p_exact':p})


def tfr_cases():
    sf=128
    t=np.arange(384)/sf-1
    X=np.random.default_rng(318).normal(0,.35,size=(4,2,len(t)))
    X += np.array([[.7],[1.3]]) * np.sin(2*np.pi*10*t+.3)
    for name,i in [('morlet-power',0),('morlet-itc',1),('baseline-logratio',2)]:
        freq,ncycles=10,5
        sigma=ncycles/(2*np.pi*freq)
        half=int(np.ceil(5*sigma*sf))-1
        w=np.arange(-half,half+1)/sf
        wave=(np.exp(2j*np.pi*freq*w)-np.exp(-ncycles*ncycles/2))*np.exp(-w*w/(2*sigma*sigma))
        wave*=np.sqrt(2/sum(abs(wave)**2))
        coeff=np.array([[np.convolve(v,wave,mode='same') for v in row] for row in X])
        power=np.mean(abs(coeff)**2,axis=0)
        values=[power, abs(np.mean(coeff/abs(coeff),axis=0)),
                np.log10(power/power[:,(t>=-.5)&(t<=-.125)].mean(axis=1,keepdims=True))][i]
        pos=np.array([144,156,180,220,270])
        desc=['average power in uV^2', 'ITC from the complex trial coefficients', 'log10(power / mean baseline power) with inclusive baseline [-0.5,-0.125] s'][i]
        case('tfr',name,'Compute zero-mean Morlet at 10 Hz, 5 cycles, decim=1, from the supplied epoched '
             'signals with tmin=-1 s. No other preprocessing. Return values equal to '+desc+
             ' for each channel at the given zero-based sample_indices, and times_s at those sample indices.',
             {'epochs_uV':X,'sfreq':sf,'tmin':-1,'sample_indices':pos,'channels':['Fz','Cz']},
             {'values':values[:,pos], 'times_s':t[pos]})


if __name__ == '__main__':
    PUBLIC.mkdir()
    PRIVATE.mkdir()
    for name in ['audit','behavior','bids','entropy','connectivity','decoding','epoch','erp','figure','group',
                 'ica','methods','microstate','pipeline','preprocess','qc','recipe','report','source','spectrum','stats','tfr']:
        globals()[name+'_cases']()
    counts=Counter(task['skill'] for task in tasks)
    assert counts==Counter({p.parent.name:3 for p in SNAPSHOT.glob('skills/eeg-*/SKILL.md')}),counts
    assert len(tasks)==66 and len({t['id'] for t in tasks})==66
    save(ROOT/'TASKS.json',tasks)
    # Interleave skills inside each repetition so that partial execution remains easy to audit.
    schedule=[{'task':t['id'],'skill':t['skill'],'rep':rep,'session':f"skills66__{t['id']}__rep{rep}"}
              for rep in (1,2,3) for t in sorted(tasks,key=lambda t:(t['id'].split('-')[-1],t['skill']))]
    save(ROOT/'SCHEDULE.json',schedule)
