"""
Siliun Panel — Admin UI (Streamlit), deployed on Render, embedded/linked from
the private Webflow page /siliun/panel.

Talks to the FastAPI backend (backend/main.py) over HTTPS using the
Authorization: Bearer <SILIUN_ADMIN_TOKEN> header. Configure via
Streamlit secrets (.streamlit/secrets.toml) or environment variables:
  API_BASE, SILIUN_ADMIN_TOKEN, ADMIN_ID
"""
import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Siliun Panel", page_icon="🧭", layout="wide")


def _cfg(key, default=""):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


API_BASE = _cfg("API_BASE", "http://localhost:8000")
ADMIN_ID = _cfg("ADMIN_ID", "admin")

if "admin_token" not in st.session_state:
    st.session_state.admin_token = _cfg("SILIUN_ADMIN_TOKEN", "")

with st.sidebar:
    st.title("🧭 Siliun Panel")
    st.caption(f"API: {API_BASE}")
    st.session_state.admin_token = st.text_input(
        "Admin token", value=st.session_state.admin_token, type="password",
        help="Debe coincidir con SILIUN_ADMIN_TOKEN del backend."
    )
    admin_id = st.text_input("Admin ID", value=ADMIN_ID)
    st.divider()
    st.caption("Módulos")


def headers():
    return {
        "Authorization": f"Bearer {st.session_state.admin_token}",
        "X-Admin-Id": admin_id,
    }


def api_get(path, **params):
    r = requests.get(f"{API_BASE}{path}", headers=headers(), params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def api_post(path, json=None):
    r = requests.post(f"{API_BASE}{path}", headers=headers(), json=json, timeout=15)
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(f"{r.status_code}: {detail}")
    return r.json()


tabs = st.tabs([
    "🧑 Estado del Usuario",
    "📡 Señal Simbólica",
    "🗝️ Acceso a Malakai",
    "⚙️ Automatizaciones",
    "🏛️ Templo Malakai",
    "💳 Economía",
    "🫂 Comunidad Troton",
])

# ---------------------------------------------------------------- Módulo 1
with tabs[0]:
    st.subheader("Estado del Usuario")

    col_id, col_load = st.columns([3, 1])
    user_id = col_id.text_input("User ID", value="u_12345", key="user_id_input")
    if col_load.button("Cargar", use_container_width=True):
        try:
            st.session_state["user"] = api_get(f"/admin/user/{user_id}")
        except Exception as e:
            st.error(f"No se pudo cargar el usuario: {e}")

    user = st.session_state.get("user")

    if user:
        g1, g2, g3 = st.columns(3)
        g1.metric("Claridad", user["clarity"])
        g2.metric("Ritmo", user["rhythm"])
        g3.metric("Resonancia", user["resonanceScore"])

        st.progress(min(max(user["resonanceScore"], 0) / 100, 1.0), text="Resonancia / 100")
        st.write(
            f"**user_state_ready:** {'✅ Listo' if user['user_state_ready'] else '⏳ No listo'}  "
            f"·  última verificación: `{user.get('last_state_check', '—')}`"
        )

        st.markdown("##### Ajustar y recalcular")
        c1, c2, c3, c4 = st.columns(4)
        new_clarity = c1.slider("Claridad", 0, 100, int(user["clarity"]))
        new_rhythm = c2.slider("Ritmo", 0, 100, int(user["rhythm"]))
        new_intention = c3.toggle("Intención", value=bool(user["intention"]))
        new_silence = c4.toggle("Silencio", value=bool(user["silence"]))

        if st.button("🔄 Recalcular estado", type="primary"):
            try:
                updated = api_post(f"/admin/user/{user_id}/state", {
                    "clarity": new_clarity,
                    "rhythm": new_rhythm,
                    "intention": int(new_intention),
                    "silence": new_silence,
                })
                st.session_state["user"] = updated
                st.success(f"resonanceScore = {updated['resonanceScore']} · user_state_ready = {updated['user_state_ready']}")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        st.markdown("##### Historial")
        history = user.get("stateHistory", [])
        if history:
            df = pd.DataFrame(history)
            df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
            st.line_chart(df.set_index("ts")[["clarity", "rhythm", "resonanceScore"]])
        else:
            st.caption("Sin historial todavía.")

        st.markdown("##### Nota administrativa")
        note = st.text_area("Nota", value=user.get("notes", ""), label_visibility="collapsed")
        if st.button("💾 Guardar nota"):
            try:
                st.session_state["user"] = api_post(f"/admin/user/{user_id}/note", {"note": note})
                st.success("Nota guardada")
            except Exception as e:
                st.error(str(e))

        st.markdown("##### Acciones críticas")
        if st.button("✅ Marcar como listo (user_state_ready = true)"):
            try:
                st.session_state["user"] = api_post(f"/admin/user/{user_id}/mark-ready")
                st.success("Usuario marcado como listo")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        with st.expander("🧾 Logs de auditoría (últimos 20)"):
            try:
                logs = api_get("/admin/audit/log", limit=20)
                if logs:
                    st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
                else:
                    st.caption("Sin actividad registrada todavía.")
            except Exception as e:
                st.error(str(e))
    else:
        st.info("Cargá un usuario para ver su estado.")

# ---------------------------------------------------------------- Módulo 2
with tabs[1]:
    st.subheader("Señal Simbólica")
    st.caption("Máximo 10 activaciones manuales por admin por día (aplicado en el backend).")
    if user:
        if st.button("📡 Activar señal"):
            try:
                res = api_post(f"/admin/user/{user['userId']}/trigger-signal")
                st.success("Señal activada")
                st.json(res["signal"])
            except Exception as e:
                st.error(str(e))
        st.markdown("##### Historial de señales")
        st.dataframe(pd.DataFrame(user.get("signals", [])), use_container_width=True, hide_index=True)
    else:
        st.info("Cargá un usuario en la pestaña anterior primero.")

# ---------------------------------------------------------------- Módulo 3
with tabs[2]:
    st.subheader("Acceso a Malakai")
    st.caption("Máximo 5 aperturas manuales por admin por día (aplicado en el backend).")
    if user:
        st.write(f"**Estado actual:** {'🟢 Abierto' if user.get('malakaiAccess') else '🔴 Cerrado'}")
        if st.button("🗝️ Abrir Malakai manualmente"):
            try:
                st.session_state["user"] = api_post(f"/admin/user/{user['userId']}/open-malakai")
                st.success("Malakai abierto para este usuario")
                st.rerun()
            except Exception as e:
                st.error(str(e))
        st.markdown("##### Caminos abiertos")
        st.write(user.get("pathsOpened", []) or "Ninguno todavía.")
    else:
        st.info("Cargá un usuario en la primera pestaña.")

# ---------------------------------------------------------------- Módulo 4
with tabs[3]:
    st.subheader("Automatizaciones")
    st.caption(
        "Sin endpoint dedicado en el backend — este módulo asume un escenario de Make "
        "que escucha los webhooks del backend (state update, mark-ready, signal, malakai) "
        "y notifica por Discord. Configurá DISCORD_WEBHOOK_URL en el backend para activarlo."
    )
    if user:
        st.markdown("##### Enviar mensaje de prueba")
        channel = st.selectbox("Canal", ["discord", "email"])
        body = st.text_area("Mensaje", value="Test desde Siliun Panel")
        if st.button("✉️ Enviar"):
            try:
                api_post(f"/admin/user/{user['userId']}/message", {"body": body, "channel": channel})
                st.success("Mensaje enviado")
            except Exception as e:
                st.error(str(e))
    else:
        st.info("Cargá un usuario en la primera pestaña.")

# ---------------------------------------------------------------- Módulo 5
with tabs[4]:
    st.subheader("Templo Malakai")
    st.caption("Vista de solo lectura sobre pathsOpened del usuario. Capas/runas específicas se definen en Webflow CMS.")
    if user:
        st.write("**Caminos abiertos:**", ", ".join(user.get("pathsOpened", [])) or "—")
        st.write("**Núcleo El Origen:**", "🔓 accesible" if user.get("user_state_ready") else "🔒 bloqueado (requiere user_state_ready)")
    else:
        st.info("Cargá un usuario en la primera pestaña.")

# ---------------------------------------------------------------- Módulo 6
with tabs[5]:
    st.subheader("Economía")
    st.caption("Datos estáticos de referencia — no hay endpoint de planes/precios definido en el backend todavía.")
    if user:
        st.write("**Plan actual:**", user.get("memberPlan", "—"))
    st.table(pd.DataFrame([
        {"Plan": "Founders Window", "Precio": "—", "Notas": "Ventana limitada de lanzamiento"},
        {"Plan": "Troton Pro", "Precio": "—", "Notas": "Plan estándar"},
    ]))

# ---------------------------------------------------------------- Módulo 7
with tabs[6]:
    st.subheader("Comunidad Troton")
    st.caption("Placeholder — círculos, roles, eventos y bots viven en Discord/Webflow; no hay endpoint backend todavía.")
    st.write("Círculos, roles, eventos y bots se gestionan hoy fuera del backend (Discord/Webflow).")
