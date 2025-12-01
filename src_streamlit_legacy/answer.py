from app.runtime import run_with_timeout


def get_answer_safe(call_model_sync, format_sync, query:str, t_model=45, t_format=10) -> str:
    ok, raw = run_with_timeout(lambda: call_model_sync(query), t_model)
    if not ok: return str(raw)
    ok2, pretty = run_with_timeout(lambda: format_sync(raw), t_format)
    return pretty if ok2 else ("⚠️ Formatting took too long; showing raw text.\n\n" + str(raw))
