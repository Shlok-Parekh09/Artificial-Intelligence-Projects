# What does ShikshaAI do 
# 🧠 ShikshaAI Agents

ShikshaAI is built as a modular pipeline of intelligent agents. Each agent has a single responsibility, clear inputs/outputs, and resilient fallback logic so the pipeline never fails silently. Together, they transform YouTube lectures into structured study packs.

---

## 🎧 TranscriptAgent — Audio Download + Transcription
Extracts audio from YouTube and produces a clean transcript using Whisper.  
- Downloads audio with `yt-dlp`, supporting cookies for restricted videos.  
- Falls back from `bestaudio` to `best` if needed.  
- Splits long audio into chunks for efficient Whisper inference.  
- Outputs: Transcript string.  

---

## 📝 SummarizationAgent — Multi-Provider Summary Generator
Condenses the transcript into structured, readable notes.  
- Uses fallback chain: **APIfy → Groq → Mistral**.  
- Produces consistent sections (Overview, Key Concepts, Methods, Takeaways).  
- Outputs: Summary string.  

---

## 🎯 FlashcardAgent — Active Recall Generator
Converts summaries into compact Q&A items.  
- Generates factual question-answer pairs.  
- Ensures coverage of all key concepts.  
- Outputs: Markdown list of flashcards.  

---

## 🧪 QuizAgent — Multiple-Choice Question Generator
Creates MCQs with rationales to test understanding.  
- Generates questions with 4–5 options.  
- Provides rationales for correct answers.  
- Balances easy, medium, and hard questions.  
- Outputs: Markdown quiz section.  

---

## 📦 ExportAgent — Markdown Packager
Combines all outputs into a single Markdown file.  
- Includes video URL, summary, flashcards, quiz, and transcript.  
- Saves as `ShikshaAI_Output_<video_id>.md`.  

---

## 🧭 Pipeline Orchestration
Runs the full pipeline end-to-end.  
- Reads video IDs from `config.yaml` (non-interactive).  
- Uses `ThreadPoolExecutor` for parallel processing.  
- Handles errors gracefully so one failure doesn’t block others.  

---

## 📊 Agent Summary Table

| Agent              | Role                          | Input            | Output             |
|--------------------|-------------------------------|------------------|--------------------|
| TranscriptAgent    | Audio download + transcription | YouTube URL      | Transcript string  |
| SummarizationAgent | Summarizes transcript          | Transcript       | Summary string     |
| FlashcardAgent     | Generates flashcards           | Summary          | Markdown Q&A list  |
| QuizAgent          | Creates MCQs with rationales   | Summary          | Markdown quiz      |
| ExportAgent        | Packages results               | All agent outputs| Markdown file      |

---

Each agent is modular, resilient, and designed for plug-and-play upgrades. You can swap providers, tweak formats, or extend functionality without breaking the pipeline.

# Steps to perform before running code
## 1. Generate all API keys first 
### a. APIfy API key
#### i. Login to the following website first ####
https://apify.com/?gfa3sd=advQiAqsitBhDlARIsAGMR1RixghUQjuWARa8LoLw9WNnE2i9HzhshGfsvbS3ok6UH048kqGIMaAlbLEAga3scB&fpr=3eoy4&gad_source=1&gad_campaignid=22728086574&gbraid=0AAAABAZRuvTvmu_29iN_uRLN1SNF9ZgYZ&gclid=CjwKCAiA86_JBhAIEiwA4i9Ju6s2eNHcPr9bk8D7s4RX2ekzLIqQ-aH2tKGXRZlQlfdqidllgsReGRoC1IgQAvD_BwE

#### ii. Go to Console ####
<img width="953" height="475" alt="image" src="https://github.com/user-attachments/assets/cfca41f7-cc8e-4ce6-9721-4ca5d1b2abaf" />

#### iii. Then go to settings ####
<img width="959" height="467" alt="image" src="https://github.com/user-attachments/assets/8b11f8d6-f5dc-440d-b518-7aeaaa530f6f" />

#### iv. Then go to API and Integrations ####
<img width="779" height="467" alt="image" src="https://github.com/user-attachments/assets/309d9361-f170-4007-866a-38236e5d0a68" />

Then generate your APIfy API key and use it in the code

### b. GROQ API key
#### i. Login to the following website ####
https://console.groq.com/keys

Then generate your GROQ API key and use it in the code

### c. Mistral API key
#### i. Login to following website ####
https://admin.mistral.ai/organization/api-keys

#### ii. Then go to create new key ####
<img width="959" height="467" alt="image" src="https://github.com/user-attachments/assets/084a2064-0ee4-48d9-944c-476971f1928f" />

#### iii. Then add do the following things : ####
<ol>
<li> Give a name to your API key </li>
<li> Add name of the organization </li>
<li> Add date of expiration of API </li>
</ol>

<img width="383" height="382" alt="image" src="https://github.com/user-attachments/assets/05b8171a-302a-4c42-856e-3147f2c4693a" />

Then generate your MISTRAL API key and use it in the code

# 2. Install the extension Get cookies.txt LOCALLY
<img width="959" height="470" alt="image" src="https://github.com/user-attachments/assets/b39c0901-0177-4dbc-9f44-391d4b104103" />

### ✅ What this extension does
It extracts all cookies from your browser for the current site and downloads them into cookies.txt. This allows external tools to reuse your login session without needing: 

<ul>  
<li> Username/password </li>
<li> 2FA </li>
<li> Captcha </li>
<li> Google login </li>
<li> YouTube account switching </li>
</ul> 

### ⭐ Why you need this for YouTube / yt-dlp
YouTube restricts many videos unless You are logged in such as :
<ul> 
<li> Age-restricted videos </li>
<li> Region-blocked videos </li>
<li> "Sign in to confirm your age" </li>
<li> Private/unlisted playlists </li>
<li> Premium quality formats (1080p/4K in some cases) </li>
<li> Members-only videos </li>
</ul>

yt-dlp cannot log in by itself. But if you give it your cookies.txt, it will behave as your logged-in browser.
