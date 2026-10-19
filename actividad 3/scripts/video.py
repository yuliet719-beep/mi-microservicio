"""Encode consecutive real browser captures at their measured relative timing."""
from pathlib import Path
import json
import subprocess
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
timeline = json.loads((ROOT / 'evidencias/video-timeline.json').read_text(encoding='utf-8'))
tmp = ROOT / 'tmp/video'; tmp.mkdir(parents=True, exist_ok=True)
concat = []
captions = []
elapsed = 0


def stamp(t):
    ms = int(t*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


segments=[]
for i, frame in enumerate(timeline):
    source=Path(frame['path'])
    if not source.is_absolute():
        source=ROOT/source
    if i+1 < len(timeline) and timeline[i+1]['scene']==frame['scene']:
        duration=max(.04,(timeline[i+1]['timestamp']-frame['timestamp'])/1000)
    else:
        duration=.3
    concat.extend([f"file '{source.as_posix()}'", f'duration {duration:.3f}'])
    if not segments or segments[-1]['scene'] != frame['scene']:
        segments.append({'scene':frame['scene'],'start':elapsed,'end':elapsed+duration})
    else:
        segments[-1]['end']=elapsed+duration
    elapsed += duration
concat.append(concat[-2])
(tmp/'frames.txt').write_text('\n'.join(concat),encoding='utf-8')
for i,s in enumerate(segments):
    captions.append(f"{i+1}\n{stamp(s['start'])} --> {stamp(s['end'])}\n{s['scene']} | Sandbox local; GCP/AWS pendientes.\n")
srt=ROOT/'Video_Demostracion_Local.srt';srt.write_text('\n'.join(captions),encoding='utf-8')
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ffmpeg,'-y','-f','concat','-safe','0','-i',str(tmp/'frames.txt'),
    '-i',str(srt),'-map','0:v','-map','1:0','-vf','scale=1706:876:force_original_aspect_ratio=decrease,pad=1706:876:(ow-iw)/2:(oh-ih)/2',
    '-r','15','-c:v','libx264','-preset','fast','-crf','24','-pix_fmt','yuv420p',
    '-c:s','mov_text','-movflags','+faststart',str(ROOT/'Video_Demostracion_Local.mp4')],check=True,
    stdout=subprocess.DEVNULL,stderr=(tmp/'encode.log').open('w'))
# Portable metadata: retain the timeline, but no machine-specific absolute paths.
for f in timeline:
    try:
        f['path']=Path(f['path']).relative_to(ROOT).as_posix()
    except ValueError:
        pass
(ROOT/'evidencias/video-timeline.json').write_text(json.dumps(timeline,indent=2,ensure_ascii=False),encoding='utf-8')
print(f'Real browser recording: {elapsed:.1f} seconds; {len(timeline)} frames; {len(segments)} scenes')
