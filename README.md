# Nature Daily Email Automation

This repository runs a cloud-hosted Nature daily email job with GitHub Actions.
It does not depend on your local computer or the Codex desktop app being open.

## What It Does

- Runs every day at 08:00 Beijing time.
- Searches Nature Portfolio for one recent computational/statistical article.
- Avoids articles already recorded in `sent_articles.json`.
- Uses the OpenAI Responses API with web search to generate the Chinese HTML email.
- Sends the email through Gmail SMTP.
- Commits the newly sent article record back to `sent_articles.json`.

## Required GitHub Secrets

Open the GitHub repository, then go to `Settings -> Secrets and variables -> Actions`.

Create these repository secrets:

- `OPENAI_API_KEY`: your OpenAI API key.
- `SMTP_USERNAME`: your Gmail address, for example `tommy020929@gmail.com`.
- `SMTP_PASSWORD`: your Gmail app password, not your normal Gmail password.

For Gmail, enable 2-step verification and create an App Password:
`Google Account -> Security -> 2-Step Verification -> App passwords`.

## Optional GitHub Variables

In `Settings -> Secrets and variables -> Actions -> Variables`, you can set:

- `EMAIL_TO`: recipient email. Defaults to `SMTP_USERNAME`.
- `EMAIL_FROM`: sender email. Defaults to `SMTP_USERNAME`.
- `OPENAI_MODEL`: defaults to `gpt-5`.
- `OPENAI_REASONING_EFFORT`: defaults to `medium`.
- `SMTP_HOST`: defaults to `smtp.gmail.com`.
- `SMTP_PORT`: defaults to `587`.

## Schedule

GitHub Actions cron uses UTC. The workflow uses:

```yaml
cron: "0 0 * * *"
```

That is 00:00 UTC, which is 08:00 in Asia/Shanghai.

## Manual Run

After pushing to GitHub, open the `Actions` tab, choose `Nature daily email`,
then click `Run workflow`.

## Local Dry Run

```powershell
$env:OPENAI_API_KEY="your_openai_key"
pip install -r requirements.txt
python scripts/nature_daily_email.py --dry-run
```

Dry run prints the generated JSON and does not send email or update
`sent_articles.json`.

## Notes

- Do not commit real API keys or Gmail passwords.
- If the job sends an email but the final commit step fails, update
  `sent_articles.json` manually or rerun after fixing repository permissions.
- The workflow needs `contents: write` permission so it can commit the updated
  deduplication record.
