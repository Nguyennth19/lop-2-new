#!/usr/bin/env python3
"""Non-generative live model-credential smoke test. This is not a vision QA test."""
import os
import sys

def main():
    token = os.getenv('OPENAI_API_KEY')
    model = os.getenv('LOP2_VISION_MODEL')
    if not token or not model:
        raise SystemExit('VISION_API_CREDENTIAL_OR_MODEL_MISSING')
    try:
        from openai import OpenAI
        client = OpenAI(api_key=token, timeout=30, max_retries=0)
        fetched = client.models.retrieve(model)
        if fetched.id != model:
            raise RuntimeError('MODEL_ID_MISMATCH')
    except Exception:
        # Do not write API error bodies or any sensitive headers to public CI logs.
        raise SystemExit('VISION_API_MODEL_ACCESS_CHECK_FAILED') from None
    print('VISION_API_MODEL_ACCESS_CHECK_SUCCEEDED (not a vision inference test)')

if __name__ == '__main__':
    main()