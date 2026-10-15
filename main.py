import os, json, time, subprocess, requests
from pathlib import Path
from datetime import datetime

OUT = Path('output')
OUT.mkdir(exist_ok=True)
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
REPLICATE_API_TOKEN = os.environ['REPLICATE_API_TOKEN']


def openai_chat(prompt):
    r = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'gpt-4o-mini', 'temperature': 0.9,
              'messages': [
                  {'role': 'system', 'content': 'You are a professional Hindi horror and suspense Shorts writer. Return only valid JSON, no markdown.'},
                  {'role': 'user', 'content': prompt}
              ]}, timeout=90)
    r.raise_for_status()
    content = r.json()['choices'][0]['message']['content'].strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    return json.loads(content)


def create_story():
    prompt = '''Create one original Hindi horror/suspense YouTube Short. Return JSON with keys: title (Hindi, catchy, <=70 chars), description (Hindi, 2 sentences and include #Shorts), tags (array of 5-8 strings, no #), narration (Hindi voiceover of about 25-35 words, clear beginning and twist), visual_prompt (English cinematic text-to-video prompt). The visual prompt must describe a vertical 9:16 realistic Indian horror scene, one continuous shot, eerie night lighting, no text/subtitles/logos, no gore, and must match narration. Story should be original and suitable for a general audience. Do not claim it is a true story.'''
    data = openai_chat(prompt)
    for key in ('title', 'description', 'tags', 'narration', 'visual_prompt'):
        if key not in data:
            raise ValueError(f'Missing story field: {key}')
    return data


def replicate_video(prompt, destination):
    # Official Replicate model: prunaai/p-video-2-pro. Model schema can change; check the model page if needed.
    url = 'https://api.replicate.com/v1/models/prunaai/p-video-2-pro/predictions'
    headers = {'Authorization': f'Token {REPLICATE_API_TOKEN}', 'Content-Type': 'application/json', 'Prefer': 'wait=60'}
    payload = {'input': {
        'prompt': prompt,
        'duration': 15,
        'resolution': '768p',
        'aspect_ratio': '9:16',
        'mode': 'speed',
        'prompt_upsampler': 'turbo'
    }}
    r = requests.post(url, headers=headers, json=payload, timeout=90)
    if r.status_code >= 400:
        raise RuntimeError(f'Replicate error {r.status_code}: {r.text[:1200]}')
    pred = r.json()
    poll_url = pred.get('urls', {}).get('get')
    deadline = time.time() + 900
    while pred.get('status') not in ('succeeded', 'failed', 'canceled'):
        if time.time() > deadline:
            raise TimeoutError('Replicate video generation took longer than 15 minutes.')
        if not poll_url:
            raise RuntimeError(f'Replicate did not return a polling URL: {pred}')
        time.sleep(5)
        check = requests.get(poll_url, headers={'Authorization': f'Token {REPLICATE_API_TOKEN}'}, timeout=60)
        check.raise_for_status()
        pred = check.json()
    if pred.get('status') != 'succeeded':
        raise RuntimeError(f'Replicate generation {pred.get("status")}: {pred.get("error", "Unknown error")}')
    output = pred.get('output')
    video_url = output if isinstance(output, str) else (output[0] if isinstance(output, list) and output else None)
    if not isinstance(video_url, str) or not video_url.startswith('http'):
        raise RuntimeError(f'Unexpected Replicate output format: {output}')
    video = requests.get(video_url, timeout=180)
    video.raise_for_status()
    destination.write_bytes(video.content)


def create_voiceover(text, destination):
    r = requests.post(
        'https://api.openai.com/v1/audio/speech',
        headers={'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'tts-1', 'voice': 'alloy', 'input': text, 'response_format': 'mp3', 'speed': 1.05},
        timeout=120)
    r.raise_for_status()
    destination.write_bytes(r.content)


def add_voice(video_path, audio_path, final_path):
    # Keeps the generated video vertical; trims to whichever stream ends first.
    cmd = ['ffmpeg', '-y', '-i', str(video_path), '-i', str(audio_path), '-map', '0:v:0', '-map', '1:a:0',
           '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', str(final_path)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError('FFmpeg audio merge failed: ' + p.stderr[-1800:])


def upload_to_youtube(video_path, story):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = Credentials(
        token=None,
        refresh_token=os.environ['YOUTUBE_REFRESH_TOKEN'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.environ['YOUTUBE_CLIENT_ID'],
        client_secret=os.environ['YOUTUBE_CLIENT_SECRET'],
        scopes=['https://www.googleapis.com/auth/youtube.upload']
    )
    creds.refresh(Request())
    youtube = build('youtube', 'v3', credentials=creds, cache_discovery=False)
    privacy = os.getenv('VIDEO_PRIVACY', 'private')
    body = {'snippet': {
        'title': story['title'][:100],
        'description': (story['description'] + '\n\nNarration: ' + story['narration'] + '\n\nAI-assisted fictional horror story.').strip()[:5000],
        'tags': [str(t)[:100] for t in story.get('tags', [])][:15],
        'categoryId': '24',
        'defaultLanguage': 'hi'
    }, 'status': {'privacyStatus': privacy, 'selfDeclaredMadeForKids': False}}
    request = youtube.videos().insert(part='snippet,status', body=body,
        media_body=MediaFileUpload(str(video_path), mimetype='video/mp4', resumable=True))
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f'YouTube upload: {int(status.progress() * 100)}%')
    print('YouTube video uploaded:', 'https://www.youtube.com/watch?v=' + response['id'])


def main():
    print('Starting Hindi horror Shorts automation...')
    story = create_story()
    print('Story:', story['title'])
    raw_video = OUT / 'generated_video.mp4'
    voice = OUT / 'voiceover.mp3'
    final_video = OUT / 'youtube_short.mp4'
    replicate_video(story['visual_prompt'], raw_video)
    create_voiceover(story['narration'], voice)
    add_voice(raw_video, voice, final_video)
    Path('output/story.json').write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding='utf-8')
    upload_to_youtube(final_video, story)
    print('Done:', datetime.utcnow().isoformat() + 'Z')

if __name__ == '__main__':
    main()
