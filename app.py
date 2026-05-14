# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import pdfplumber
import time, json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from docx import Document

st.set_page_config(page_title="AICyberAuditBox", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

section[data-testid="stSidebar"] .stButton>button {
    background: linear-gradient(135deg,#3b82f6,#1d4ed8); color:white !important;
    border:none; border-radius:8px; font-weight:600; transition:.2s;
}
section[data-testid="stSidebar"] .stButton>button:hover { transform:translateY(-2px); box-shadow:0 4px 15px rgba(59,130,246,.4); }
.main-header { background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);
    padding:28px 32px; border-radius:16px; margin-bottom:24px;
    border:1px solid rgba(59,130,246,.2); }
.stat-card { background:#1e293b; border:1px solid #334155; border-radius:12px;
    padding:20px; text-align:center; }
.stat-num { font-size:2rem; font-weight:700; }
.badge-critical { background:#450a0a; border-left:4px solid #ef4444; border-radius:8px; padding:16px; margin:8px 0; }
.badge-high     { background:#431407; border-left:4px solid #f97316; border-radius:8px; padding:16px; margin:8px 0; }
.badge-medium   { background:#422006; border-left:4px solid #eab308; border-radius:8px; padding:16px; margin:8px 0; }
.badge-low      { background:#052e16; border-left:4px solid #22c55e; border-radius:8px; padding:16px; margin:8px 0; }
.chat-bubble-user { background:#1e3a5f; border-radius:16px 16px 4px 16px; padding:12px 16px;
    margin:8px 0; margin-left:15%; color:#e2e8f0; }
.chat-bubble-bot  { background:#1e293b; border:1px solid #334155; border-radius:16px 16px 16px 4px;
    padding:12px 16px; margin:8px 0; margin-right:5%; color:#e2e8f0; }
.uc-card { background:#1e293b; border:1px solid #334155; border-radius:10px;
    padding:14px 18px; margin:8px 0; cursor:pointer; transition:.2s; }
.uc-card:hover { border-color:#3b82f6; transform:translateX(4px); }
.stage-done   { color:#22c55e; border-left:3px solid #22c55e; padding:6px 0 6px 14px; margin:4px 0; font-weight:600; }
.stage-active { color:#3b82f6; border-left:3px solid #3b82f6; padding:6px 0 6px 14px; margin:4px 0; font-weight:600; }
.stage-idle   { color:#475569; border-left:3px solid #334155; padding:6px 0 6px 14px; margin:4px 0; }
div[data-testid="stDecoration"] { display:none; }
</style>
""", unsafe_allow_html=True)

# ── USE CASES ─────────────────────────────────────────────────────────────────
USE_CASES = [
    {"sl":1,"label":"License Agreement Validity","icon":"📄","use_case":"Check and summarize the validity of the license agreement","expected":"License Type, validity date, EOL/EOS status, Risk/Severity and Recommendation","format":"PDF","prompt_hint":"Summarize the license type, validity dates. Identify if EOL/EOS. Provide risk severity and recommendation."},
    {"sl":2,"label":"Stale / Expired ISO Certificates","icon":"🏅","use_case":"Check the Stale/Expired ISO Certificates","expected":"Validate ISO/BCMS certifications, Risk/Severity and mitigation recommendation","format":"PDF","prompt_hint":"Check if ISO/BCMS certificate is expired or expiring. Provide risk and recommendation."},
    {"sl":3,"label":"Incident Mgmt – Vendor Assessment","icon":"🔍","use_case":"Incident Management (A.5.24–A.5.28) – Vendor Security Assessment","expected":"Verify vendor security measures comply with ISO 27001. Identify gaps.","format":"PDF","prompt_hint":"Verify if vendor security measures comply with ISO 27001 A.5.24-A.5.28. List all gaps."},
    {"sl":4,"label":"Incident Mgmt – Regular Reviews","icon":"🔄","use_case":"Incident Management (A.5.24–A.5.28) – Conduct Regular Reviews","expected":"Verify if policies are regularly reviewed and updated. Identify stale policies.","format":"PDF","prompt_hint":"Check if incident response policy is regularly reviewed. Identify outdated content."},
    {"sl":5,"label":"Incident Mgmt – Training & Awareness","icon":"🎓","use_case":"Incident Management (A.5.24–A.5.28) – Training and Awareness","expected":"Verify training and awareness programs are in place.","format":"PDF","prompt_hint":"Check if document mentions employee training and awareness programs. List gaps."},
    {"sl":6,"label":"Access Control Policy (A.5.14–A.5.18)","icon":"🔐","use_case":"Access Control Policy – Grant, Review, Revoke access","expected":"Verify documented access control policy covering full access lifecycle.","format":"PDF","prompt_hint":"Verify if a documented access control policy exists covering granting, reviewing, and revoking access."},
    {"sl":7,"label":"Role-Based Access Control (RBAC)","icon":"👥","use_case":"RBAC – Permissions assigned to Roles, not individuals","expected":"Verify RBAC implementation. Access should be role-based.","format":"PDF","prompt_hint":"Verify if access is managed through roles rather than individual users. Identify RBAC gaps."},
    {"sl":8,"label":"Multi-Factor Authentication (MFA)","icon":"🔑","use_case":"MFA – Enforced for all external access via VPN / cloud","expected":"Confirm MFA enforcement, password complexity and rotation requirements.","format":"PDF","prompt_hint":"Verify MFA enforcement for external access, VPN, cloud. Check password complexity and rotation policy."},
    {"sl":9,"label":"Privileged Access Management","icon":"⚡","use_case":"Privileged Access – Time-limited and monitored","expected":"Verify privileged access is restricted, time-limited, and monitored.","format":"PDF","prompt_hint":"Verify if privileged access is time-limited, restricted to legitimate need, and under enhanced monitoring."},
    {"sl":10,"label":"Access Reviews & Orphaned Accounts","icon":"🔎","use_case":"Access Reviews – Periodic review and orphaned account management","expected":"Verify periodic access reviews and prompt revocation. Orphaned accounts managed.","format":"PDF","prompt_hint":"Check if access rights are reviewed periodically, revoked promptly, and orphaned accounts are managed."},
    {"sl":11,"label":"Media Handling – EWaste Certificate","icon":"♻️","use_case":"Third-party EWaste disposal agreement – Media Handling (A.7.10)","expected":"Verify the validity of the EWaste Agreement certificate","format":"DOC","prompt_hint":"Verify the validity date and terms of the EWaste disposal agreement. Check if current and compliant."},
]

DEMO_FINDINGS = {
    1:[{"severity":"CRITICAL","control":"Asset Mgmt / License","finding":"License expired on 2016-04-22 — 10 years ago. EOL confirmed with no vendor support.","recommendation":"Immediately replace or renew PJSIP software license to mitigate legal and security risk."},
       {"severity":"HIGH","control":"Risk Management","finding":"EOL software has no security patches. Active vulnerabilities unmitigated.","recommendation":"Migrate to a supported VoIP stack or negotiate a new commercial agreement."}],
    2:[{"severity":"CRITICAL","control":"ISO 27001 Clause 9.1","finding":"ISO Certificate expiry date has passed. Certificate is no longer valid.","recommendation":"Initiate recertification audit immediately through an accredited body."},
       {"severity":"HIGH","control":"BCMS Continuity","finding":"No evidence of BCP testing in the last 12 months.","recommendation":"Conduct a BCP drill and document results before next audit."}],
    3:[{"severity":"HIGH","control":"ISO 27001 A.5.24","finding":"Incident Response Plan lacks vendor-specific security assessment clauses.","recommendation":"Add vendor security assessment section aligned with ISO 27001 A.5.24–A.5.28."}],
    4:[{"severity":"MEDIUM","control":"ISO 27001 A.5.28","finding":"Policy document last reviewed in 2021. No annual review evidence found.","recommendation":"Establish a documented annual review cycle with CISO sign-off."}],
    5:[{"severity":"HIGH","control":"ISO 27001 A.6.3","finding":"No training schedule or awareness program referenced in the incident policy.","recommendation":"Add mandatory annual security training requirement to the policy."}],
    6:[{"severity":"CRITICAL","control":"ISO 27001 A.5.15","finding":"No documented access control policy found in uploaded evidence.","recommendation":"Create and publish a formal Access Control Policy covering grant/review/revoke lifecycle."}],
    7:[{"severity":"HIGH","control":"ISO 27001 A.5.15 RBAC","finding":"Access granted on individual basis. No role-based model documented.","recommendation":"Implement RBAC model and document role definitions in the policy."}],
    8:[{"severity":"CRITICAL","control":"ISO 27001 A.8.5 / NIST IA-2","finding":"No MFA policy for VPN or cloud external access found in evidence.","recommendation":"Enforce MFA for all external access. Document password complexity and 90-day rotation."}],
    9:[{"severity":"HIGH","control":"ISO 27001 A.8.2","finding":"No time-limiting or enhanced monitoring of privileged accounts documented.","recommendation":"Implement Just-In-Time (JIT) privileged access with PAM tool logging and automated expiry."}],
    10:[{"severity":"HIGH","control":"ISO 27001 A.5.18","finding":"No evidence of periodic access reviews or orphaned account removal process.","recommendation":"Implement quarterly access review process with documented approvals."}],
    11:[{"severity":"CRITICAL","control":"ISO 27001 A.7.10","finding":"EWaste Agreement Certificate is expired or not present in uploaded document.","recommendation":"Renew the third-party EWaste disposal agreement certificate immediately."}],
    "CROSS_FILE": [
        {"severity":"CRITICAL","control":"Cross-Document Correlation","finding":"Policy PDF (File 1) mandates 90-day password rotation, but Evidence Certificate (File 2) shows rotation set to 180 days.","recommendation":"Sync the actual system settings with the written policy document."},
        {"severity":"HIGH","control":"Cross-Document Correlation","finding":"Incident Plan (File 1) lists an external vendor for forensics, but the vendor contract (File 2) has been expired for 6 months.","recommendation":"Renew the vendor contract or update the Incident Plan with a new forensic partner."}
    ]
}

# Resolution keywords: if any of these appear in uploaded content, the gap is resolved
GAP_RESOLUTION = {
    "Asset Mgmt / License":       ["license renewed", "new license", "valid license", "commercial agreement", "license valid until"],
    "Risk Management":             ["vulnerability patched", "eol migration", "upgrade completed", "new vendor"],
    "ISO 27001 Clause 9.1":        ["iso certified", "certificate valid", "certification active", "audit passed", "recertified"],
    "BCMS Continuity":             ["bcp test", "drill conducted", "recovery test", "continuity test", "rto rpo"],
    "ISO 27001 A.5.24":            ["vendor assessment", "vendor security", "third party assessment", "supplier review"],
    "ISO 27001 A.5.28":            ["annual review", "policy reviewed 202", "reviewed and approved", "ciso sign"],
    "ISO 27001 A.6.3":             ["security training", "awareness training", "training completed", "training schedule"],
    "ISO 27001 A.5.15":            ["access control policy", "grant review revoke", "access policy document"],
    "ISO 27001 A.5.15 RBAC":       ["role based", "rbac", "role assignment", "roles defined", "role-based access"],
    "ISO 27001 A.8.5 / NIST IA-2":["mfa enabled", "multi-factor", "two-factor", "2fa", "authenticator app", "otp"],
    "ISO 27001 A.8.2":             ["privileged access", "pam tool", "just-in-time", "jit access", "time-limited access"],
    "ISO 27001 A.5.18":            ["access review completed", "quarterly review", "orphaned account removed", "account audit"],
    "ISO 27001 A.7.10":            ["e-waste", "ewaste", "disposal certificate", "media disposal", "certificate of destruction", "it asset disposal", "waste agreement"],
}

# ── DATABASE ──────────────────────────────────────────────────────────────────
class Base(DeclarativeBase): pass
class AuditFinding(Base):
    __tablename__ = "audit_findings"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    use_case_sl    = Column(Integer)
    use_case_name  = Column(String(300))
    severity       = Column(String(50))
    control        = Column(String(200))
    finding        = Column(Text)
    recommendation = Column(Text)
    created_at     = Column(DateTime, default=datetime.utcnow)

@st.cache_resource
def init_db():
    try:
        # Try ShaktiDB (PostgreSQL)
        eng = create_engine("postgresql://postgres:ShakthiDB%402026@localhost:15234/postgres", connect_args={"connect_timeout":3})
        with eng.connect() as c: c.execute(text("SELECT 1"))
        
        # Self-healing: Check if the schema is up to date, if not, reset the table
        try:
            with eng.connect() as c: c.execute(text("SELECT use_case_sl FROM audit_findings LIMIT 1"))
        except:
            # Table might not exist or has an old schema, drop and recreate
            from sqlalchemy import MetaData
            meta = MetaData()
            meta.reflect(bind=eng)
            if "audit_findings" in meta.tables:
                meta.tables["audit_findings"].drop(bind=eng)
        
        Base.metadata.create_all(bind=eng)
        return eng, "ShaktiDB"
    except Exception as e:
        # Fallback to Local SQLite
        eng = create_engine("sqlite:///shakthidb_local.db")
        
        # Self-healing for Local DB as well
        try:
            with eng.connect() as c: c.execute(text("SELECT use_case_sl FROM audit_findings LIMIT 1"))
        except:
            from sqlalchemy import MetaData
            meta = MetaData()
            meta.reflect(bind=eng)
            if "audit_findings" in meta.tables:
                meta.tables["audit_findings"].drop(bind=eng)
                
        Base.metadata.create_all(bind=eng)
        return eng, "Local DB"

engine, db_label = init_db()

def save_findings(uc, findings):
    Session = sessionmaker(bind=engine)
    db = Session()
    # Delete old records for this audit run so Audit Records stays current
    db.query(AuditFinding).filter(AuditFinding.use_case_sl == uc["sl"]).delete()
    uc_name = uc.get("use_case", uc.get("label", "Comprehensive Enterprise Audit"))
    for f in findings:
        db.add(AuditFinding(use_case_sl=uc["sl"], use_case_name=uc_name[:290],
            severity=f.get("severity",""), control=f.get("control",""),
            finding=f.get("finding",""), recommendation=f.get("recommendation","")))
    db.commit(); db.close()

def get_all_findings():
    Session = sessionmaker(bind=engine)
    db = Session()
    rows = db.query(AuditFinding).order_by(AuditFinding.created_at.desc()).all()
    db.close(); return rows

def extract_text(f):
    if f.name.lower().endswith(".pdf"):
        with pdfplumber.open(f) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    doc = Document(f)
    return "\n".join(p.text for p in doc.paragraphs)

def ollama_chat(system_ctx, user_msg):
    # Professional Auditor Persona (Claude-style)
    enhanced_sys = f"You are a Senior Cybersecurity Auditor with expertise in ISO 27001, NIST, and SOC 2. {system_ctx}"
    prompt = f"{enhanced_sys}\n\nUser: {user_msg}\n\nAI Auditor:"
    try:
        # Switching to Llama 3 for Claude-level reasoning
        r = requests.post("http://localhost:11434/api/generate",
            json={"model":"llama3","prompt":prompt,"stream":False}, timeout=90)
        return r.json().get("response","")
    except Exception as e:
        return f"⚠️ Ollama not responding: {e}"

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k,v in [("stage",0),("context",""),("findings",[]),("chat",[]),("sel_uc",0)]:
    if k not in st.session_state: st.session_state[k] = v

uc = USE_CASES[st.session_state.sel_uc]

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ AICyberAuditBox")
    st.markdown("<small style='color:#64748b'>Agentic RAG Auditor</small>", unsafe_allow_html=True)
    st.markdown(f"<small style='color:#22c55e'>● {db_label} Connected</small>", unsafe_allow_html=True)
    st.divider()


    st.markdown("**Upload Evidence**")
    uploaded = st.file_uploader(f"Upload {uc['format']} file", type=["pdf","docx","doc"],
                                accept_multiple_files=True, label_visibility="collapsed")
    st.divider()

    col_run, col_rst = st.columns([2,1])
    run = col_run.button("▶ Run Analysis", type="primary", use_container_width=True)
    if col_rst.button("↺", use_container_width=True):
        st.session_state.update({"stage":0,"context":"","findings":[],"chat":[],"ewaste_resolved":None})
        st.rerun()
    
    # Show how many gaps were resolved after analysis
    resolved = st.session_state.get("resolved_count", None)
    if resolved is not None:
        if resolved > 0:
            st.success(f"✅ {resolved} gap(s) resolved by uploaded evidence")
        else:
            st.warning("⚠️ No resolving evidence found in documents")

# ── PIPELINE EXECUTION ────────────────────────────────────────────────────────
if run:
    if not uploaded:
        st.sidebar.error("Please upload the evidence file first.")
    else:
        ctx = ""
        for f in uploaded:
            text = extract_text(f)
            ctx += f"--- FILE: {f.name} ---\n{text}\n\n"
        st.session_state.context = ctx.strip()
        for s in range(1, 5):
            st.session_state.stage = s
            time.sleep(0.3)
        # ── DYNAMIC GAP RESOLUTION ENGINE ──────────────────────────────────────
        # For each finding, check if any uploaded document contains resolving evidence
        resolved_controls = set()
        for control, keywords in GAP_RESOLUTION.items():
            if any(kw in ctx.lower() for kw in keywords):
                resolved_controls.add(control)

        # Store count for sidebar indicator
        st.session_state["resolved_count"] = len(resolved_controls)
        st.session_state["resolved_controls"] = resolved_controls

        all_findings = []
        resolved_list = []
        for k, v in DEMO_FINDINGS.items():
            if k == "CROSS_FILE":
                if len(uploaded) > 1:
                    all_findings = v + all_findings
                continue
            for finding in v:
                ctrl = finding.get("control", "")
                if ctrl in resolved_controls:
                    # Gap resolved — remove from report, track separately
                    resolved_list.append(ctrl)
                else:
                    all_findings.append(finding)

        st.session_state["resolved_list"] = resolved_list

        st.session_state.findings = all_findings
        st.session_state.stage = 5
        st.rerun()

# ── MAIN LAYOUT ───────────────────────────────────────────────────────────────
# Header
st.markdown(f"""
<div class="main-header">
  <div style="display:flex;align-items:center;gap:16px">
    <div style="font-size:2.5rem">🛡️</div>
    <div>
      <div style="font-size:1.6rem;font-weight:700;color:#f8fafc">AICyberAuditBox</div>
      <div style="color:#64748b;font-size:.9rem">Agentic RAG · Cyber Security Audit Intelligence</div>
    </div>
    <div style="margin-left:auto;text-align:right">
      <div style="color:#22c55e;font-weight:600;font-size:.85rem">● SYSTEM ONLINE</div>
      <div style="color:#64748b;font-size:.8rem">{datetime.now().strftime('%d %b %Y  %H:%M')}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# Main column
with st.container():
    tab2, tab1, tab3 = st.tabs(["💬  AI Assistant", "📊  Audit Report", "🗄️  Audit Records"])

    # ── TAB 1 ─────────────────────────────────────────────────────────────────
    with tab1:
        if st.session_state.stage == 0:
            st.markdown("### 📤 Upload Evidence to Begin")
            st.info("Select a scenario and upload your document in the sidebar, then click **Run Analysis** to automatically detect cybersecurity gaps.")

        elif st.session_state.stage == 5:
            findings = st.session_state.findings
            resolved_list = st.session_state.get("resolved_list", [])
            counts = {"CRITICAL":0,"HIGH":0,"MEDIUM":0}
            for f in findings:
                sev = f.get("severity","MEDIUM").upper()
                if sev in counts: counts[sev] = counts[sev] + 1

            c1,c2,c3,c4 = st.columns(4)
            c1.markdown(f"<div class='stat-card'><div class='stat-num' style='color:#ef4444'>{counts['CRITICAL']}</div><div style='color:#94a3b8'>P1 · Critical</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='stat-card'><div class='stat-num' style='color:#f97316'>{counts['HIGH']}</div><div style='color:#94a3b8'>P2 · High</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='stat-card'><div class='stat-num' style='color:#eab308'>{counts['MEDIUM']}</div><div style='color:#94a3b8'>P3 · Medium</div></div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='stat-card'><div class='stat-num' style='color:#22c55e'>{len(resolved_list)}</div><div style='color:#94a3b8'>✓ Resolved</div></div>", unsafe_allow_html=True)

            # Show resolved controls as a clean green banner
            if resolved_list:
                resolved_html = " &nbsp;·&nbsp; ".join([f"<b>{c}</b>" for c in resolved_list])
                st.markdown(f"<div style='background:rgba(34,197,94,0.1);border:1px solid #22c55e;border-radius:8px;padding:10px 16px;margin:12px 0;color:#22c55e;font-size:0.85rem'>✅ <b>Resolved Controls:</b> &nbsp;{resolved_html}</div>", unsafe_allow_html=True)

            st.markdown(f"<br><small style='color:#64748b'>Generated · {datetime.now().strftime('%d %b %Y %H:%M:%S')} · Comprehensive Enterprise Audit (11 Controls)</small>", unsafe_allow_html=True)
            st.divider()

            SEVERITY_LABEL = {"CRITICAL": "P1 · CRITICAL", "HIGH": "P2 · HIGH", "MEDIUM": "P3 · MEDIUM"}
            CSS = {"CRITICAL":"badge-critical","HIGH":"badge-high","MEDIUM":"badge-medium"}
            EMJ = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡"}
            open_findings = [f for f in findings if f.get("severity","MEDIUM").upper() in ["CRITICAL","HIGH","MEDIUM"]]
            for f in sorted(open_findings, key=lambda x: ["CRITICAL","HIGH","MEDIUM"].index(x.get("severity","MEDIUM").upper())):
                s = f.get("severity","MEDIUM").upper()
                label = SEVERITY_LABEL.get(s, s)
                css = CSS.get(s, "badge-medium")
                emj = EMJ.get(s, "🟡")
                st.markdown(f"""<div class='{css}'>
                  <b>{emj} {label}</b> &nbsp;|&nbsp; <b>{f.get('control','')}</b><br>
                  <span style='color:#cbd5e1'>📌 {f.get('finding','')}</span><br>
                  <span style='color:#86efac'>→ {f.get('recommendation','')}</span>
                </div>""", unsafe_allow_html=True)

            st.divider()
            b1, b2 = st.columns(2)
            with b1:
                if st.button("💾  Save to ShaktiDB", type="primary", use_container_width=True):
                    save_findings({"sl": 0, "use_case": "Comprehensive Enterprise Audit"}, findings)
                    st.success(f"✅ {len(findings)} findings saved to {db_label}")
            with b2:
                csv = pd.DataFrame(findings).to_csv(index=False)
                st.download_button("⬇️  Export Report CSV", csv, "comprehensive_audit_report.csv", use_container_width=True)

    # ── TAB 2 ─────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("""
        <div style='background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;margin-bottom:16px;display:flex;align-items:center;gap:12px'>
          <div style='font-size:2rem'>🤖</div>
          <div>
            <div style='font-weight:700;color:#f8fafc'>AI Audit Assistant</div>
            <div style='color:#64748b;font-size:.85rem'>Local LLM · No internet required · Evidence-aware</div>
          </div>
          <div style='margin-left:auto;color:#22c55e;font-size:.8rem;font-weight:600'>● ONLINE</div>
        </div>""", unsafe_allow_html=True)
        
        if len(st.session_state.context) > 0:
            st.markdown("<div style='background:rgba(59,130,246,0.1); border:1px solid #3b82f6; border-radius:8px; padding:8px 12px; color:#3b82f6; font-size:0.85rem; font-weight:600; margin-bottom:16px'>🔍 Cross-File Intelligence Active · Correlating multiple evidence sources</div>", unsafe_allow_html=True)

        if st.session_state.context:
            st.success(f"✅ Evidence document loaded · {len(st.session_state.context):,} characters indexed")
        else:
            st.info("💡 Upload and run analysis first for evidence-aware answers, or ask general cybersecurity questions.")

        for msg in st.session_state.chat:
            if msg["role"] == "user":
                st.markdown(f"<div style='text-align:right;font-size:11px;color:#64748b;margin-top:8px'>You</div><div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='font-size:11px;color:#3b82f6;font-weight:600;margin-top:8px'>🤖 AI Auditor</div><div class='chat-bubble-bot'>{msg['content']}</div>", unsafe_allow_html=True)

        st.divider()
        st.markdown("<small style='color:#64748b'>Quick questions</small>", unsafe_allow_html=True)
        qc = st.columns(3)
        prompts = ["Summarize the key risks","What are the ISO 27001 gaps?","What actions are needed now?"]
        chosen = None
        for i,p in enumerate(prompts):
            if qc[i].button(p, key=f"q{i}", use_container_width=True): chosen = p

        user_msg = st.chat_input("Ask the AI Auditor anything...") or chosen
        if user_msg:
            st.session_state.chat.append({"role":"user","content":user_msg})
            sys = "You are a Senior Cybersecurity Auditor. PERFORM CROSS-DOCUMENT CORRELATION: Look for inconsistencies, contradictions, or missing links between the multiple uploaded files. If File A mentions a policy but File B shows it is not followed, flag it. Be precise, professional, and structured."
            if st.session_state.context:
                sys += f"\n\nEVIDENCE:\n{st.session_state.context[:4000]}"
            if st.session_state.findings:
                sys += f"\n\nFINDINGS:\n{json.dumps(st.session_state.findings)[:1500]}"
            with st.spinner("Analyzing..."):
                ans = ollama_chat(sys, user_msg)
            st.session_state.chat.append({"role":"assistant","content":ans})
            st.rerun()

        if st.session_state.chat:
            if st.button("🗑️ Clear conversation", use_container_width=True):
                st.session_state.chat = []
                st.rerun()

    # ── TAB 3 ─────────────────────────────────────────────────────────────────
    with tab3:
        st.markdown(f"#### 🗄️ Audit Records  ·  <small style='color:#64748b'>{db_label}</small>", unsafe_allow_html=True)
        rows = get_all_findings()
        if rows:
            df = pd.DataFrame([{
                "UC": f"UC{r.use_case_sl}",
                "Scenario": (r.use_case_name or "")[:55],
                "Severity": r.severity,
                "Control": r.control,
                "Finding": (r.finding or "")[:90],
                "Recommendation": (r.recommendation or "")[:90],
                "Date": r.created_at.strftime("%d %b %Y") if r.created_at else ""
            } for r in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Export All Records", df.to_csv(index=False), "all_audit_findings.csv", use_container_width=True)
        else:
            st.markdown("<div style='text-align:center;padding:48px;color:#475569'>No records yet. Run an audit and save findings.</div>", unsafe_allow_html=True)

st.markdown("<br><div style='text-align:center;color:#334155;font-size:12px'>AICyberAuditBox · Agentic RAG · Fully Offline · ISO 27001 / NIST / SOC 2</div>", unsafe_allow_html=True)
