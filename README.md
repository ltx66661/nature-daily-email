# Nature Daily Email Automation

This repository runs a cloud-hosted Nature daily email job with GitHub Actions.
It does not depend on your local computer or the Codex desktop app being open.

## What It Does

- Runs every weekday at 10:00 Beijing time.
- Sends two non-duplicated emails in sequence: the main recipient list, then the Xu Xu list.
- Searches Nature Portfolio for recent computational/statistical articles.
- Avoids articles already recorded in `sent_articles.json`.
- Uses the Gemini API to generate the Chinese HTML email.
- Sends the email through Gmail SMTP.
- Commits the newly sent article record back to `sent_articles.json`.

## Required GitHub Secrets

Open the GitHub repository, then go to `Settings -> Secrets and variables -> Actions`.

Create these repository secrets:

- `GEMINI_API_KEY`: your Gemini API key.
- `SMTP_USERNAME`: your Gmail address, for example `tommy020929@gmail.com`.
- `SMTP_PASSWORD`: your Gmail app password, not your normal Gmail password.
- `EMAIL_CC`: comma-separated CC recipients.
- `EMAIL_BCC`: comma-separated BCC recipients.

For Gmail, enable 2-step verification and create an App Password:
`Google Account -> Security -> 2-Step Verification -> App passwords`.

## Optional GitHub Variables

In `Settings -> Secrets and variables -> Actions -> Variables`, you can set:

- `EMAIL_TO`: direct recipient email. Defaults to `SMTP_USERNAME`.
- `EMAIL_FROM`: sender email. Defaults to `SMTP_USERNAME`.
- `XU_XU_EMAIL`: optional override for the Xu Xu recipient. Defaults to `xu.xu02@xjtlu.edu.cn`.
- `GEMINI_MODEL`: defaults to `gemini-2.5-flash`.
- `GEMINI_MAX_OUTPUT_TOKENS`: defaults to `12000`.
- `SMTP_HOST`: defaults to `smtp.gmail.com`.
- `SMTP_PORT`: defaults to `587`.

## Schedule

GitHub Actions cron uses UTC. The workflow uses:

```yaml
cron: "0 2 * * 1-5"
```

That is 02:00 UTC Monday-Friday, which is 10:00 Monday-Friday in Asia/Shanghai.

## Manual Run

After pushing to GitHub, open the `Actions` tab, choose `Nature daily email`,
then click `Run workflow`.

## Local Dry Run

```powershell
$env:GEMINI_API_KEY="your_gemini_key"
pip install -r requirements.txt
python scripts/nature_daily_email.py --dry-run
```

Dry run prints the generated JSON and does not send email or update
`sent_articles.json`.

## Notes

- Do not commit real API keys or Gmail passwords.
- Both email scripts share `sent_articles.json`, so the second script sees the
  first script's article before choosing its own. If either script cannot find a
  non-duplicate article, it fails instead of sending a duplicate.
- If the job sends an email but the final commit step fails, update
  `sent_articles.json` manually or rerun after fixing repository permissions.
- The workflow needs `contents: write` permission so it can commit the updated
  deduplication record.
