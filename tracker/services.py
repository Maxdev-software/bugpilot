import json
import logging
import re
import urllib.request
import urllib.error

from django.conf import settings

logger = logging.getLogger('tracker')

ANALYSIS_PROMPT = """You are a senior software engineer performing automated bug triage.
Analyze the following error log and respond with a JSON object containing these exact keys:
- "summary": one sentence describing what happened
- "root_cause": one paragraph explaining the technical root cause
- "fix_suggestion": concrete steps to fix the issue (bullet points as plain text with newlines)
- "priority": one of "critical", "bug", "warning", "info" based on severity

Respond ONLY with valid JSON. No markdown, no code fences, no extra text.

Error details:
App: {app_name}
Environment: {environment}
Level: {level}
Message: {message}
Stacktrace:
{stacktrace}
"""


def analyse_error(*, app_name: str, environment: str, level: str, message: str, stacktrace: str) -> dict:
    if not settings.OPENROUTER_API_KEY:
        raise RuntimeError('OPENROUTER_API_KEY is not configured.')

    prompt = ANALYSIS_PROMPT.format(
        app_name=app_name,
        environment=environment,
        level=level,
        message=message,
        stacktrace=stacktrace or '(no stacktrace provided)',
    )

    payload = json.dumps({
        'model': settings.OPENROUTER_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.2,
        'max_tokens': 800,
    }).encode()

    req = urllib.request.Request(
        settings.OPENROUTER_BASE_URL,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
            'HTTP-Referer': 'https://bugpilot.internal',
            'X-Title': 'BugPilot',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'LLM API HTTP {exc.code}: {exc.read().decode()}') from exc
    except Exception as exc:
        raise RuntimeError(f'LLM API error: {exc}') from exc

    raw_text = body['choices'][0]['message']['content'].strip()

    raw_text = re.sub(r'^```json\s*', '', raw_text)
    raw_text = re.sub(r'```$', '', raw_text).strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'LLM returned invalid JSON: {exc}\nRaw: {raw_text[:300]}') from exc

    for key in ('summary', 'root_cause', 'fix_suggestion', 'priority'):
        if key not in result:
            result[key] = ''

    valid_priorities = {'critical', 'bug', 'warning', 'info'}
    if result.get('priority') not in valid_priorities:
        result['priority'] = _infer_priority_from_level(level)

    logger.info('AI analysis completed for %s [%s]: priority=%s', app_name, level, result['priority'])
    return result


def _infer_priority_from_level(level: str) -> str:
    mapping = {
        'CRITICAL': 'critical',
        'ERROR': 'bug',
        'WARNING': 'warning',
        'INFO': 'info',
        'DEBUG': 'info',
    }
    return mapping.get(level.upper(), 'bug')
