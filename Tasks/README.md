# GenAI Internship Tasks — Mistral AI Edition

All 12 tasks are separate Python files and use the official `mistralai` Python SDK.

## Setup
Python 3.10+ recommended.

```bash
pip install -r requirements.txt
```

Set your Mistral API key from your Mistral account as an environment variable. Do not commit it.

Windows PowerShell:
```powershell
$env:MISTRAL_API_KEY="your_mistral_api_key_here"
python task_01_customer_support.py
```

macOS/Linux:
```bash
export MISTRAL_API_KEY="your_mistral_api_key_here"
python task_01_customer_support.py
```

Change the filename to run another task. Edit the example input at the bottom of each script to test your own data.

## Files
- `task_01_customer_support.py`
- `task_02_product_description.py`
- `task_03_email_classifier.py`
- `task_04_meeting_action_items.py`
- `task_05_social_media_generator.py`
- `task_06_code_explainer.py`
- `task_07_translator.py`
- `task_08_cover_letter.py`
- `task_09_content_moderation.py`
- `task_10_interview_questions.py`
- `task_11_review_sentiment.py`
- `task_12_quiz_generator.py`

## Model and temperatures
All scripts default to `mistral-small-latest`. Temperature is task-specific: 0.0–0.2 for classification/extraction/translation/quiz accuracy, 0.3 for support, 0.4–0.5 for interviews/cover letters, 0.7 for social posts, and 0.85 for creative product copy. Verify the chosen model and JSON response-format support in your Mistral account/documentation if you change model IDs.

## GitHub submission
```bash
git init
git add *.py README.md requirements.txt
git commit -m "Implement 12 GenAI internship tasks with Mistral AI"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Review all model-generated outputs before using them in customer support, hiring, moderation, or education. These scripts have been syntax-checked; live API responses require a valid Mistral API key and were not tested here.
