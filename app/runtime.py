import time, traceback, concurrent.futures

_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

def run_with_timeout(fn, timeout_s):
    fut = _pool.submit(fn)
    try:
        return True, fut.result(timeout=timeout_s)
    except concurrent.futures.TimeoutError:
        fut.cancel()
        return False, "⚠️ Timeout: operation took too long."
    except Exception as e:
        return False, f"⚠️ Error: {e}\n{traceback.format_exc()}"

def init_watchdog(ss):
    for k,v in {"_last_rerun_ts":0.0, "_rerun_window":[], "_crash":None}.items():
        if k not in ss: ss[k] = v

def watchdog_ping(ss):
    now = time.time()
    win = ss["_rerun_window"]; win.append(now)
    ss["_rerun_window"] = [t for t in win if now - t <= 3.0]
    if len(ss["_rerun_window"]) > 12:  # >4 reruns/sec for 3s
        ss["_crash"] = "Detected rerun loop (>12 reruns in 3s). A flag or callback toggles every render."

def safe_top(st, render_fn):
    init_watchdog(st.session_state); watchdog_ping(st.session_state)
    try:
        render_fn()
    except Exception as e:
        import io, traceback
        buf = io.StringIO(); traceback.print_exc(file=buf)
        st.session_state["_crash"] = buf.getvalue()
        st.error("⚠️ The app hit an exception but stayed alive. See details below.")
    finally:
        if st.session_state.get("_crash"):
            with st.expander("Debug details", expanded=False):
                st.code(st.session_state["_crash"])
