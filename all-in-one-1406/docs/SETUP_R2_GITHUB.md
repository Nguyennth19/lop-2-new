# LOP2 — Cloudflare R2 + GitHub Actions protected setup

**Do not enter keys into ChatGPT, Git commits, Actions output or issues.** This document contains placeholder values only. The repository is currently public. Keep original SGK/VBT PDFs and question content private.

## A. Configure Cloudflare R2 using the owner's Cloudflare dashboard

1. Open https://dash.cloudflare.com/ -> **Storage & databases -> R2** and enable R2 if needed. Charges/plan authorization must come from the account owner.
2. Create a **private** bucket. Suggested bucket name: `lop2-source-private` (choose your own unique name). Do not attach an R2.dev public bucket URL or public custom domain.
3. Create a **bucket-scoped** R2 API token: Object Read & Write, restricted to this bucket, expiration appropriate for the campaign. Save Access Key ID and Secret Access Key *locally in a secure credential manager*.
4. Copy the S3 endpoint from the R2 dashboard, normally `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`. Jurisdiction-specific buckets use a different endpoint. Use region `auto`.
5. Do not create a public worker route or log credentials. Check the R2 lifecycle policy: avoid deletion of `campaigns/` checkpoint data until audit sign-off.

## B. Upload exactly five private inputs

Store them under `<PREFIX>/inputs/`, with PREFIX recommended as `lop2-private`:

| Object basename | SHA-256 verification |
|---|---|
| `SOURCE_1406.csv` | `20863df79b330b17921da4695d5023800d65915328081af811d8092a593a0f95` (frozen V1.0 snapshot) |
| `SGK_T1.pdf` | `cb8cb303294edc0be2f36a9507965b59345c0d53c296d610858e7454dfa8321e` |
| `VBT_T1.pdf` | `7c77820bb52a9f59b790180a16adc8231993768f59a16bb86084bb2f65f171cf` |
| `SGK_T2.pdf` | `044142f31fa94769a143dd029422ee74c49480ad9304e567cc8d97efa4c42f36` |
| `VBT_T2.pdf` | `9f3b4d9ff793e4280de7e72d1854a7492d77c88809c9bd9c2be4fa9af3b732c2` |

This source snapshot must include all 1,406 rows across all 21 BQA groups, and `SGK_B001_K1_E01` on SGK Tập 1 PDF page 7.

Using the AWS CLI **on the owner's trusted machine**, after configuring credentials securely as environment variables, the copy syntax is:

```bash
aws --endpoint-url "https://<ACCOUNT_ID>.r2.cloudflarestorage.com" \
  s3 cp ./SOURCE_1406.csv s3://<BUCKET>/lop2-private/inputs/SOURCE_1406.csv
aws --endpoint-url "https://<ACCOUNT_ID>.r2.cloudflarestorage.com" \
  s3 cp ./SGK_T1.pdf s3://<BUCKET>/lop2-private/inputs/SGK_T1.pdf
# Repeat for VBT_T1.pdf, SGK_T2.pdf and VBT_T2.pdf.
```

Never add these five inputs to GitHub's public repository or GitHub Actions public artifacts. The source files can be obtained from the owner's existing Google Drive archive; do not use placeholder/example PDFs.

## C. Protected GitHub Environment

Repository -> **Settings -> Environments** -> `lop2-private`. Restrict permitted deployment branches to `main` and configure a required reviewer where supported. Ensure only trusted collaborators can edit workflows and environment secrets. In Settings -> Secrets and variables -> Actions (or inside the protected Environment), add:

**Secrets:**
- `LOP2_S3_BUCKET` — private R2 bucket name
- `LOP2_S3_ACCESS_KEY_ID` — scoped R2 Access Key ID
- `LOP2_S3_SECRET_ACCESS_KEY` — scoped R2 Secret Access Key
- `OPENAI_API_KEY` — OpenAI API key that can use your chosen vision model

**Variables:**
- `LOP2_S3_ENDPOINT` = `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`
- `LOP2_S3_REGION` = `auto`
- `LOP2_S3_PREFIX` = `lop2-private`
- `LOP2_VISION_MODEL` = a model available in your account that supports image input and Structured Outputs
- `LOP2_ENABLE_FULL_RUN` = `NO` (keep locked until preflight and live canary both pass)

Do not disclose API keys or access tokens in issue comments, PR descriptions, chat messages, screen recordings or CI logs. Check API billing and the Cloudflare R2 usage dashboard before allowing a campaign.

## D. Three manual actions, then automatic full campaign

The workflow is ".github/workflows/lop2-all-in-one-production.yml". `workflow_dispatch` must be available from `main` — the draft PR is not an active production deployment.

1. **Preflight**: Actions -> LOP2 All-in-One 1406 -> Run workflow -> `mode=preflight`, `campaign=<new-stable-ID>`. Must verify: private input downloads, 1,406 rows, 21 BQA, four SHA-256 PDF hashes, remote checkpoint roundtrip, remote write/read/list/delete, and real model ID authentication.
2. **Canary**: Run workflow -> `mode=canary`, same campaign ID. Processes only `SGK_B001_K1_E01` from the original SGK page. A source-linked **machine draft** with student slots, original crop hash and `release_allowed=false` must be read back from R2; otherwise the gate remains closed.
3. **Full campaign**: After reviewing the preflight and canary results, deliberately set `LOP2_ENABLE_FULL_RUN=YES`. Run workflow -> `mode=run-all`, same campaign ID. The runner checks the remote canary marker and manifest/model lock first. Each job processes up to 35 items and auto-dispatches the next job until coverage completes or a hard safety limit triggers.

Canary success **does not** mean the question matches the original source independently, and does not imply N9 Engine browser pass, reviewer N10, or N12 release permission. All created questions remain drafts or coded exceptions.

**Stop conditions:** credentials missing; bucket write/read/list/delete failure; model authentication failure; source file hash conflict; altered manifest within same campaign; canary mismatch; authorization flag unset; infrastructure failures or quota exhaustion. Do not retry by reusing a different manifest under the same campaign ID.

## E. Do not merge by mistake

The repository is currently public. The source processor is implemented and tested locally/mock S3, but an *actual* live Cloudflare R2 account, keys, OpenAI model credentials, owner-approved billing, and source/canary review are **not yet connected**. Keep PR #3 draft until the account owner configures them and authorizes deployment to `main`.

Official docs: https://developers.cloudflare.com/r2/get-started/s3/ and https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions