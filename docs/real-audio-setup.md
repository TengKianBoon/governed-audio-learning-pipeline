# Real Audio Setup

Use this after the mock pipeline works. This setup keeps raw learning files private while the public repo shows the architecture, OpenAI quality layer, and controls.

## Step 1 - Open The App Folder

```powershell
cd "C:\Leon G Drive\A Daily Routine\AI Learnings\enterprise-ai-learning-audio-app"
```

## Step 2 - Create A Private Local Config

```powershell
copy .\config\paths.local.example.yaml .\config\paths.local.yaml
notepad .\config\paths.local.yaml
```

This file is ignored by Git. It can safely contain private local paths.

## Step 3 - Find FFmpeg And FFprobe

Try this first:

```powershell
Get-ChildItem -Path "C:\Leon G Drive","C:\Users\User" -Filter ffmpeg.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20 FullName
Get-ChildItem -Path "C:\Leon G Drive","C:\Users\User" -Filter ffprobe.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20 FullName
```

If you find them, paste both full paths into `config\paths.local.yaml`.

Example:

```yaml
ffmpeg_path: "C:/Tools/ffmpeg/bin/ffmpeg.exe"
ffprobe_path: "C:/Tools/ffmpeg/bin/ffprobe.exe"
```

Do not change global PATH for this app.

## Step 4 - Create A Local Python Environment For Whisper

Use the bundled Codex Python to create a private `.venv` inside this app:

```powershell
& "C:\Users\User\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -U openai-whisper
```

Then keep this in `config\paths.local.yaml`, or leave `whisper_command` blank and the app will auto-detect `.venv\Scripts\whisper.exe`:

```yaml
whisper_command: ".venv/Scripts/whisper.exe"
whisper_model: "base"
translation_model: "base"
```

The first real run may download the Whisper model. That is normal.

## Step 5 - Set OpenAI API Key

Recommended for frequent use on your own secured Windows account:

```powershell
.\scripts\set-openai-key-user.ps1
```

This stores `OPENAI_API_KEY` as a Windows user-level environment variable. It is not stored in this repo, but it can be read by processes running as your Windows user, so use a dedicated OpenAI project key with spend limits.

Use this one-session method on shared machines or when you want maximum caution:

```powershell
$secureKey = Read-Host "Paste OpenAI API key" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($secureKey)
try {
  $env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringUni($ptr)
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeCoTaskMemUnicode($ptr)
}
Remove-Variable secureKey, ptr -ErrorAction SilentlyContinue
```

The app uses this for `gpt-5.4-mini` high-reasoning learning summaries. By default, it does not create a full English transcript for Chinese sources; it summarizes directly from the original transcript and writes the final learning summary in English. Mindmap updates stay local and zero-cost, using the refined summary and `mindmap_ingest.md`.

Only turn this on when you specifically need a full English transcript as an audit artifact:

```yaml
generate_full_english_transcript: true
```

To remove a saved key later:

```powershell
.\scripts\clear-openai-key-user.ps1
```

## Step 6 - Run Doctor

```powershell
.\run.ps1 doctor --create-sandbox
```

You want:

```text
ready_for_mock: true
ready_for_real_audio: true
ready_for_openai_quality: true
```

## Step 7 - Test One Real Recording Or Text Transcript

Put one short `.m4a` file or phone-generated `.txt` transcript in:

```text
C:\Leon G Drive\A Daily Routine\AI Learnings Audio App\incoming
```

Run:

```powershell
.\run.ps1 process --input "C:\Leon G Drive\A Daily Routine\AI Learnings Audio App\incoming\YOUR_FILE_NAME.m4a"
```

For a text transcript:

```powershell
.\run.ps1 process --input "C:\Leon G Drive\A Daily Routine\AI Learnings Audio App\incoming\YOUR_FILE_NAME.txt"
```

Review the output under:

```text
C:\Leon G Drive\A Daily Routine\AI Learnings Audio App\outputs_private\learnings
```

Only after review, run:

```powershell
.\run.ps1 publish --sanitize
```

For the operator workflow after setup, use `docs/operator-runbook.md`.
