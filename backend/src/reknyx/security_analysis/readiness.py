"""Public setup diagnostics. Never expose credentials or make provider requests."""
from .model_providers.groq import MODEL


def describe(settings):
    if settings.analysis_provider == 'deterministic':
        return {'reason_code':'local_review_ready','message':'Local deterministic evidence review is ready. No language model is called.'}
    if not settings.groq_api_key:
        return {'reason_code':'groq_key_missing','message':'Groq is selected, but its server API key is missing. No model request will be sent.'}
    if not settings.groq_free_plan_confirmed:
        return {'reason_code':'groq_free_plan_unconfirmed','message':'Confirm the Groq account is on the free plan in server configuration before using model review.'}
    if not settings.groq_synthetic_enabled:
        return {'reason_code':'groq_data_use_unconfirmed','message':'Synthetic evidence transmission to Groq has not been enabled in server configuration.'}
    return {'reason_code':'groq_configured','message':f'Groq {settings.groq_model} is configured for synthetic evidence review. Each request still requires eligible evidence and remaining model budget. Live provider verification is separate.'}
