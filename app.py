"""
Nexora Intelligence Systems — Cyber Range
Case NEX-042: The Ghost in the Ledger
--------------------------------------------------
A Professional Web3 x AI Security x Cybersecurity Cyber Range.

Attack Chain:
FALSE DATA (NIF-2038)
  -> TRUSTED AI CONTEXT (NOVA-INTEL-FEED via INTEL-GW-04 / INTEL-INGESTOR-02)
  -> HIGH AI CONFIDENCE (99.2% / ORION-DEC-7741)
  -> AUTOMATED AUTHORIZATION (ORION-SETTLEMENT-V2: IF CONFIDENCE >= 95% -> AUTO SIGN)
  -> WEB3 TRANSACTION (TX-NEX-7741 / 82,400 NXR from Nexora Treasury)
  -> BLOCKCHAIN & BRIDGE (0x7C41...9B2D -> Bridge Adapter -> Wallets A & B)
  -> ORION-NEXUS CAMPAIGN
"""

import os
import sqlite3
import logging
import json
import re
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, request, redirect, url_for, render_template,
    session, g, make_response, flash, jsonify, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    DB_DIR = "/tmp/database"
    os.makedirs(DB_DIR, exist_ok=True)
    DB_PATH = os.path.join(DB_DIR, "techcorp.db")
else:
    DB_DIR = os.path.join(BASE_DIR, "database")
    os.makedirs(DB_DIR, exist_ok=True)
    DB_PATH = os.path.join(DB_DIR, "techcorp.db")

app = Flask(
    __name__,
    static_folder=STATIC_DIR,
    template_folder=TEMPLATES_DIR,
    static_url_path="/static"
)
app.secret_key = os.environ.get("LAB_SECRET_KEY", "nexora-pro-cyber-range-secret-key-nex042")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("nexora-soc")


@app.route("/static/<path:filename>")
def serve_static_assets(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.before_request
def log_request():
    safe_cookies = {k: ("[REDACTED]" if k == "session" else v) for k, v in request.cookies.items()}
    if not request.path.startswith("/static"):
        log.info(f"{request.method} {request.path} | cookies={safe_cookies}")


# ----------------------------------------------------------------------
# Database helpers & Initial Setup
# ----------------------------------------------------------------------
def get_db():
    if not os.path.exists(DB_PATH):
        init_db()
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(
        """
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS mission_progress;
        DROP TABLE IF EXISTS blockchain_txs;
        DROP TABLE IF EXISTS ai_decisions;
        DROP TABLE IF EXISTS threat_intel_records;
        DROP TABLE IF EXISTS api_gateway_audit;
        DROP TABLE IF EXISTS policy_engine_rules;

        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT NOT NULL,
            clearance_level TEXT NOT NULL DEFAULT 'L2'
        );

        CREATE TABLE mission_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_owner TEXT NOT NULL,
            current_sublab INTEGER NOT NULL DEFAULT 1,
            score INTEGER NOT NULL DEFAULT 0,
            prologue_seen INTEGER NOT NULL DEFAULT 0,
            evidence_collected TEXT NOT NULL DEFAULT '[]',
            unlocked_nodes TEXT NOT NULL DEFAULT '[]',
            hints_used TEXT NOT NULL DEFAULT '[]',
            reconstruction_passed INTEGER NOT NULL DEFAULT 0,
            classification_passed INTEGER NOT NULL DEFAULT 0,
            final_passed INTEGER NOT NULL DEFAULT 0,
            flag_captured INTEGER NOT NULL DEFAULT 0,
            knowledge_check_passed INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE blockchain_txs (
            tx_hash TEXT PRIMARY KEY,
            block_number INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            from_addr TEXT NOT NULL,
            to_addr TEXT NOT NULL,
            amount_nxr REAL NOT NULL,
            smart_contract TEXT NOT NULL,
            status TEXT NOT NULL,
            bridge_interaction INTEGER NOT NULL DEFAULT 0,
            bridge_adapter TEXT NOT NULL,
            downstream_wallets TEXT NOT NULL DEFAULT '[]'
        );

        CREATE TABLE ai_decisions (
            decision_id TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            target_wallet TEXT NOT NULL,
            decision TEXT NOT NULL,
            risk_score TEXT NOT NULL,
            confidence REAL NOT NULL,
            human_approval_required INTEGER NOT NULL,
            intel_reference TEXT NOT NULL,
            context_source TEXT NOT NULL,
            provenance_status TEXT NOT NULL
        );

        CREATE TABLE threat_intel_records (
            record_id TEXT PRIMARY KEY,
            feed_name TEXT NOT NULL,
            in_official_registry INTEGER NOT NULL,
            approved_vendor INTEGER NOT NULL,
            reputation_label TEXT NOT NULL,
            claimed_risk TEXT NOT NULL,
            source_gateway TEXT NOT NULL,
            ingesting_service TEXT NOT NULL
        );

        CREATE TABLE api_gateway_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            gateway_id TEXT NOT NULL,
            service_id TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            expected_permissions TEXT NOT NULL,
            actual_permissions TEXT NOT NULL,
            payload_summary TEXT NOT NULL
        );

        CREATE TABLE policy_engine_rules (
            policy_id TEXT PRIMARY KEY,
            profile_name TEXT NOT NULL,
            confidence_threshold REAL NOT NULL,
            auto_settlement_enabled INTEGER NOT NULL,
            human_bypass_enabled INTEGER NOT NULL,
            treasury_scope_enabled INTEGER NOT NULL,
            status TEXT NOT NULL
        );
        """
    )

    users = [
        ("alex", "Alex@123", "Alex Turner", "employee", "SOC Level-1 / Trainee", "L1"),
        ("lakshay", "Lakshay@2026", "Lakshay", "investigator", "Cyber Threat Investigator", "L4"),
        ("shivam", "Shivam@2026", "Shivam Mehra", "blockchain_sec", "Blockchain Security Engineer", "L4"),
        ("shanu", "Shanu@2026", "Shanu Kapoor", "ai_sec", "AI Security Engineer", "L4"),
        ("mehak", "Mehak@2026", "Mehak Arora", "threat_intel", "Threat Intelligence & Cyber Sec Engineer", "L4"),
        ("sarah", "Sarah@123", "Sarah Nguyen", "manager", "SOC Operations Lead", "L3"),
        ("admin", "Admin@123", "System Administrator", "administrator", "IT & SecOps Administration", "L5"),
    ]
    for username, pw, display_name, role, dept, clr in users:
        cur.execute(
            "INSERT INTO users (username, password_hash, display_name, role, department, clearance_level) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, generate_password_hash(pw), display_name, role, dept, clr),
        )

    # Blockchain Dataset
    cur.execute(
        """
        INSERT INTO blockchain_txs (tx_hash, block_number, timestamp, from_addr, to_addr, amount_nxr, smart_contract, status, bridge_interaction, bridge_adapter, downstream_wallets)
        VALUES (
            'TX-NEX-7741',
            489204,
            '2026-10-04T01:47:13Z',
            '0xNXR_TREASURY_01',
            '0x7C41A8F231D5608E9B2D',
            82400.0,
            '0xAUTOSIGN_EXEC_V2',
            'CONFIRMED (Immutable)',
            1,
            '0xBridge_Adapter_CrossNet',
            '["0xWalletA_8831A9", "0xWalletB_CC44F0"]'
        )
        """
    )

    # AI Decision Engine Dataset
    cur.execute(
        """
        INSERT INTO ai_decisions (decision_id, model_name, timestamp, target_wallet, decision, risk_score, confidence, human_approval_required, intel_reference, context_source, provenance_status)
        VALUES (
            'ORION-DEC-7741',
            'ORION-V4.2-NEURAL-RISK',
            '2026-10-04T01:46:58Z',
            '0x7C41A8F231D5608E9B2D',
            'APPROVED',
            'LOW',
            99.2,
            0,
            'NIF-2038',
            'NOVA-INTEL-FEED',
            'UNVERIFIED_PROVENANCE'
        )
        """
    )

    # Threat Intelligence Record
    cur.execute(
        """
        INSERT INTO threat_intel_records (record_id, feed_name, in_official_registry, approved_vendor, reputation_label, claimed_risk, source_gateway, ingesting_service)
        VALUES (
            'NIF-2038',
            'NOVA-INTEL-FEED',
            0,
            0,
            'TRUSTED_SETTLEMENT_COUNTERPARTY',
            'LOW',
            'INTEL-GW-04',
            'INTEL-INGESTOR-02'
        )
        """
    )

    # API Gateway Audit Records
    cur.execute(
        """
        INSERT INTO api_gateway_audit (timestamp, gateway_id, service_id, endpoint, method, expected_permissions, actual_permissions, payload_summary)
        VALUES (
            '2026-10-04T01:44:22Z',
            'INTEL-GW-04',
            'INTEL-INGESTOR-02',
            '/api/v1/intel/inject',
            'POST',
            'Create Intelligence Records',
            'Create Intelligence Records + Modify Wallet Reputation',
            'Injected NIF-2038 reputation update override for 0x7C41...9B2D -> TRUSTED'
        )
        """
    )

    # Policy Engine Configuration
    cur.execute(
        """
        INSERT INTO policy_engine_rules (policy_id, profile_name, confidence_threshold, auto_settlement_enabled, human_bypass_enabled, treasury_scope_enabled, status)
        VALUES (
            'ORION-SETTLEMENT-V2',
            'Legacy Auto-Settlement V2',
            95.0,
            1,
            1,
            1,
            'ACTIVE_IN_PRODUCTION'
        )
        """
    )

    conn.commit()
    conn.close()
    log.info("Database initialized with fresh Case NEX-042 Cyber Range data.")


# ----------------------------------------------------------------------
# Auth helpers & Backward compatibility
# ----------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def client_supplied_role():
    return request.cookies.get("role", "employee")


def role_allows(role, page):
    matrix = {
        "employee": {"dashboard", "profile"},
        "manager": {"dashboard", "profile", "team"},
        "investigator": {"dashboard", "profile", "team", "admin"},
        "blockchain_sec": {"dashboard", "profile", "team", "admin"},
        "ai_sec": {"dashboard", "profile", "team", "admin"},
        "threat_intel": {"dashboard", "profile", "team", "admin"},
        "administrator": {"dashboard", "profile", "team", "admin"},
    }
    return page in matrix.get(role, set())


# ----------------------------------------------------------------------
# Cyber Range State Helpers
# ----------------------------------------------------------------------
THE_FLAG = "NEX{GHOST_IN_THE_LEDGER_AI_CONFIDENCE_NOT_AUTHORIZATION}"
DEFAULT_INITIAL_NODES = ["node_unknown_tx", "node_wallet_7c41"]


def get_session_state():
    if "sublab" not in session:
        session["sublab"] = 1
    if "score" not in session:
        session["score"] = 0
    if "evidence" not in session:
        session["evidence"] = []
    if "unlocked_nodes" not in session:
        session["unlocked_nodes"] = list(DEFAULT_INITIAL_NODES)
    if "hints_used" not in session:
        session["hints_used"] = []
    if "prologue_seen" not in session:
        session["prologue_seen"] = False
    if "reconstruction_passed" not in session:
        session["reconstruction_passed"] = False
    if "classification_passed" not in session:
        session["classification_passed"] = False
    if "final_passed" not in session:
        session["final_passed"] = False
    if "flag_captured" not in session:
        session["flag_captured"] = False
    if "knowledge_check_passed" not in session:
        session["knowledge_check_passed"] = False
    if "lab_status" not in session:
        session["lab_status"] = "not_started"


def lab_elapsed_seconds():
    started = session.get("lab_started_at")
    if not started:
        return 0
    try:
        start = datetime.fromisoformat(started)
        end = session.get("lab_completed_at")
        if end:
            finish = datetime.fromisoformat(end)
        else:
            finish = datetime.now(timezone.utc)
        return max(0, int((finish - start).total_seconds()))
    except (TypeError, ValueError):
        return 0


def calculate_score():
    base = 0
    evidence_count = len(session.get("evidence", []))
    base += evidence_count * 20
    if session.get("sublab", 1) >= 2: base += 10
    if session.get("sublab", 1) >= 3: base += 10
    if session.get("sublab", 1) >= 4: base += 10
    if session.get("sublab", 1) >= 5: base += 10
    if session.get("reconstruction_passed"): base += 30
    if session.get("classification_passed"): base += 15
    if session.get("final_passed"): base += 15
    
    hints_penalty = len(session.get("hints_used", [])) * 5
    final_score = max(0, base - hints_penalty)
    session["score"] = final_score
    return final_score


def unlock_node(node_id):
    nodes = list(session.get("unlocked_nodes", []))
    if node_id not in nodes:
        nodes.append(node_id)
        session["unlocked_nodes"] = nodes


def collect_evidence_item(evidence_id):
    ev_list = list(session.get("evidence", []))
    if evidence_id not in ev_list:
        ev_list.append(evidence_id)
        session["evidence"] = ev_list
        calculate_score()


# ----------------------------------------------------------------------
# Core Lab Route
# ----------------------------------------------------------------------
@app.route("/")
def index():
    get_session_state()
    return render_template("lab.html")


# ----------------------------------------------------------------------
# API Endpoints: Cyber Range State
# ----------------------------------------------------------------------
@app.route("/api/state")
def api_state():
    get_session_state()
    user = get_current_user()
    score = calculate_score()

    soc_feed = [
        {
            "author": "SOC MONITOR",
            "role": "SYSTEM",
            "timestamp": "01:47:13",
            "type": "CRITICAL",
            "message": "PRIORITY-0 ALERT: 82,400 NXR transferred from Nexora Treasury -> 0x7C41...9B2D. Status: CONFIRMED. AI Decision: APPROVED (99.2%). Human Approval: NOT REQUIRED."
        },
        {
            "author": "LAKSHAY",
            "role": "Cyber Threat Investigator",
            "timestamp": "01:47:45",
            "type": "BRIEFING",
            "message": "Team, assemble on Case NEX-042. Finance confirmed NO manual authorization was granted for this treasury payout. We have an unconfirmed outflow approved by our automated AI signing pipeline."
        }
    ]

    sublab = session.get("sublab", 1)
    evidence = session.get("evidence", [])

    if "WEB3-E01" in evidence or sublab >= 2:
        soc_feed.append({
            "author": "SHIVAM MEHRA",
            "role": "Blockchain Security Engineer",
            "timestamp": "01:49:10",
            "type": "FORENSICS",
            "message": "Forensic check on 0x7C41...9B2D completed: Fresh wallet, zero Nexora affiliation, funds immediately bridged. On-chain reality: UNKNOWN, but Orion AI marked it LOW RISK before transfer!"
        })

    if "AI-E02" in evidence or sublab >= 3:
        soc_feed.append({
            "author": "SHANU KAPOOR",
            "role": "AI Security Engineer",
            "timestamp": "01:52:30",
            "type": "AI_AUDIT",
            "message": "ORION-DEC-7741 analysis: The model calculated 99.2% confidence because its Context Builder ingested record NIF-2038 from NOVA-INTEL-FEED marking the wallet 'TRUSTED'. But the source provenance tag is UNVERIFIED!"
        })

    if "CYBER-E03" in evidence or sublab >= 4:
        soc_feed.append({
            "author": "MEHAK ARORA",
            "role": "Threat Intel & Cyber Sec Engineer",
            "timestamp": "01:56:04",
            "type": "API_SECURITY",
            "message": "Critical finding on INTEL-GW-04: Service INTEL-INGESTOR-02 held unauthorized permission 'modify_wallet_reputation'! Someone exploited this Least Privilege mismatch to inject false intelligence directly into Orion's context builder!"
        })

    if "AUTH-E04" in evidence or sublab >= 5:
        soc_feed.append({
            "author": "LAKSHAY",
            "role": "Cyber Threat Investigator",
            "timestamp": "02:01:15",
            "type": "GOVERNANCE",
            "message": "Policy engine audit on ORION-SETTLEMENT-V2: Rule IF AI_CONFIDENCE >= 95% THEN AUTOMATED_SETTLEMENT = TRUE bypassed human sign-off! High AI confidence was directly treated as authorization. And cross-system scan on NIF-2038 reveals 14 wallets across 4 networks — this is campaign ORION-NEXUS!"
        })

    return jsonify({
        "case_id": "NEX-042",
        "case_title": "LAB 01 — THE GHOST IN THE LEDGER",
        "organization": "Nexora Intelligence Systems",
        "difficulty": "PRO",
        "logged_in": bool(user),
        "username": user["username"] if user else None,
        "role": user["role"] if user else None,
        "lab_status": session.get("lab_status", "not_started"),
        "sublab": sublab,
        "score": score,
        "evidence": evidence,
        "unlocked_nodes": session.get("unlocked_nodes", DEFAULT_INITIAL_NODES),
        "hints_used": session.get("hints_used", []),
        "prologue_seen": session.get("prologue_seen", False),
        "reconstruction_passed": session.get("reconstruction_passed", False),
        "classification_passed": session.get("classification_passed", False),
        "final_passed": session.get("final_passed", False),
        "flag_captured": session.get("flag_captured", False),
        "knowledge_check_passed": session.get("knowledge_check_passed", False),
        "elapsed_seconds": lab_elapsed_seconds(),
        "soc_feed": soc_feed,
        "team": [
            {"name": "Lakshay", "role": "Cyber Threat Investigator", "avatar": "🕵️‍♂️"},
            {"name": "Shivam Mehra", "role": "Blockchain Security Engineer", "avatar": "⛓️"},
            {"name": "Shanu Kapoor", "role": "AI Security Engineer", "avatar": "🧠"},
            {"name": "Mehak Arora", "role": "Threat Intelligence & Cyber Sec Engineer", "avatar": "📡"}
        ]
    })


@app.route("/api/start-lab", methods=["POST"])
def api_start_lab():
    get_session_state()
    if not session.get("lab_started_at") or session.get("lab_completed_at"):
        session["lab_started_at"] = datetime.now(timezone.utc).isoformat()
        session.pop("lab_completed_at", None)
        session["lab_status"] = "running"
        session["sublab"] = 1
        session["score"] = 0
        session["unlocked_nodes"] = list(DEFAULT_INITIAL_NODES)
    return jsonify({
        "status": "running",
        "sublab": session.get("sublab", 1),
        "elapsed_seconds": lab_elapsed_seconds()
    })


@app.route("/api/prologue/acknowledge", methods=["POST"])
def api_prologue_ack():
    get_session_state()
    session["prologue_seen"] = True
    unlock_node("node_unknown_tx")
    unlock_node("node_wallet_7c41")
    return jsonify({"status": "acknowledged", "sublab": session.get("sublab", 1)})


# ----------------------------------------------------------------------
# PRO-LEVEL CHALLENGE VALIDATIONS FOR SUB-LABS 1 TO 4
# (Requires genuine forensic analysis instead of single-click bypasses)
# ----------------------------------------------------------------------
@app.route("/api/sublab/validate-01", methods=["POST"])
def api_validate_sublab_01():
    get_session_state()
    data = request.get_json(silent=True) or {}
    
    tx_hash = (data.get("tx_hash") or "").strip().upper()
    dest_wallet = (data.get("destination_wallet") or data.get("dest_wallet") or "").strip()
    bridge_adapter = (data.get("bridge_adapter") or "").strip()
    blockchain_status = (data.get("blockchain_status") or "").strip().upper()
    ai_status = (data.get("ai_pre_score_status") or data.get("ai_status") or "").strip().upper()

    tx_ok = "TX-NEX-7741" in tx_hash
    dest_ok = "0x7C41" in dest_wallet or "0x7c41" in dest_wallet.lower()
    bridge_ok = "0xBridge_Adapter_CrossNet" in bridge_adapter or "crossnet" in bridge_adapter.lower()
    bc_ok = "UNKNOWN" in blockchain_status or "HIGH RISK" in blockchain_status
    ai_ok = "LOW RISK" in ai_status or "TRUSTED" in ai_status

    if tx_ok and dest_ok and bridge_ok and bc_ok and ai_ok:
        collect_evidence_item("WEB3-E01")
        unlock_node("node_ai_decision_7741")
        session["sublab"] = max(session.get("sublab", 1), 2)
        score = calculate_score()
        return jsonify({
            "passed": True,
            "evidence_id": "WEB3-E01",
            "message": "Forensic Verification Succeeded: Anomaly confirmed between on-chain identity and pre-transfer AI categorization. Unlocked Sub-Lab 02 and ORION-DEC-7741.",
            "sublab": session["sublab"],
            "score": score
        })
    else:
        errors = []
        if not tx_ok: errors.append("Incorrect Transaction Hash (inspect Blockchain Explorer).")
        if not dest_ok: errors.append("Destination wallet address mismatch (0x7C41...9B2D).")
        if not bridge_ok: errors.append("Bridge adapter contract name mismatch (0xBridge_Adapter_CrossNet).")
        if not (bc_ok and ai_ok): errors.append("Specify the critical contradiction: Blockchain = UNKNOWN/HIGH RISK vs AI = LOW RISK.")
        return jsonify({"passed": False, "message": " ".join(errors)})


@app.route("/api/sublab/validate-02", methods=["POST"])
def api_validate_sublab_02():
    get_session_state()
    data = request.get_json(silent=True) or {}

    decision_id = (data.get("decision_id") or "").strip().upper()
    confidence = str(data.get("confidence_score") or data.get("confidence") or "").strip()
    intel_ref = (data.get("injected_record_id") or data.get("intel_ref") or "").strip().upper()
    feed_name = (data.get("feed_name") or "").strip().upper()
    provenance_flaw = (data.get("provenance_tag") or data.get("provenance_flaw") or "").strip().upper()

    dec_ok = "ORION-DEC-7741" in decision_id
    conf_ok = "99.2" in confidence or "99" in confidence
    ref_ok = "NIF-2038" in intel_ref
    feed_ok = "NOVA-INTEL-FEED" in feed_name or "NOVA" in feed_name
    prov_ok = "UNVERIFIED" in provenance_flaw or "NOT VERIFIED" in provenance_flaw

    if dec_ok and conf_ok and ref_ok and feed_ok and prov_ok:
        collect_evidence_item("AI-E02")
        unlock_node("node_ai_context_nif2038")
        unlock_node("node_threat_intel_feed")
        session["sublab"] = max(session.get("sublab", 1), 3)
        score = calculate_score()
        return jsonify({
            "passed": True,
            "evidence_id": "AI-E02",
            "message": "AI Security Audit Verified: Discovered context memory poisoning via unverified feed NOVA-INTEL-FEED. Unlocked Sub-Lab 03 & Ingestion Auditing.",
            "sublab": session["sublab"],
            "score": score
        })
    else:
        errors = []
        if not dec_ok: errors.append("Decision ID mismatch (ORION-DEC-7741).")
        if not conf_ok: errors.append("Recorded model confidence is 99.2%.")
        if not ref_ok: errors.append("Intel reference record is NIF-2038.")
        if not feed_ok: errors.append("Feed name is NOVA-INTEL-FEED.")
        if not prov_ok: errors.append("Identify the context provenance failure (UNVERIFIED_PROVENANCE).")
        return jsonify({"passed": False, "message": " ".join(errors)})


@app.route("/api/sublab/validate-03", methods=["POST"])
def api_validate_sublab_03():
    get_session_state()
    data = request.get_json(silent=True) or {}

    gateway_id = (data.get("gateway_id") or "").strip().upper()
    service_id = (data.get("service_name") or data.get("service_id") or "").strip().upper()
    excessive_perm = (data.get("permission_scope") or data.get("excessive_permission") or "").strip().lower()
    endpoint = (data.get("endpoint") or "").strip()

    gw_ok = "INTEL-GW-04" in gateway_id or "GW-04" in gateway_id
    svc_ok = "INTEL-INGESTOR-02" in service_id or "INGESTOR-02" in service_id
    perm_ok = "reputation" in excessive_perm or "modify" in excessive_perm or "wallet" in excessive_perm
    ep_ok = "/api/v1/intel/inject" in endpoint or "intel/inject" in endpoint or "inject" in endpoint

    if gw_ok and svc_ok and perm_ok and ep_ok:
        collect_evidence_item("CYBER-E03")
        unlock_node("node_api_intel_gw04")
        unlock_node("node_action_broker")
        session["sublab"] = max(session.get("sublab", 1), 4)
        score = calculate_score()
        return jsonify({
            "passed": True,
            "evidence_id": "CYBER-E03",
            "message": "API Authorization Flaw Confirmed: Service INTEL-INGESTOR-02 possessed excessive reputation write scope on INTEL-GW-04. Unlocked Sub-Lab 04 & Policy Engine.",
            "sublab": session["sublab"],
            "score": score
        })
    else:
        errors = []
        if not gw_ok: errors.append("Ingestion gateway ID mismatch (INTEL-GW-04).")
        if not svc_ok: errors.append("Service caller mismatch (INTEL-INGESTOR-02).")
        if not perm_ok: errors.append("Identify the excessive permission scope ('modify_wallet_reputation').")
        if not ep_ok: errors.append("Target endpoint mismatch (/api/v1/intel/inject).")
        return jsonify({"passed": False, "message": " ".join(errors)})


@app.route("/api/sublab/validate-04", methods=["POST"])
def api_validate_sublab_04():
    get_session_state()
    data = request.get_json(silent=True) or {}

    policy_id = (data.get("policy_id") or "").strip().upper()
    threshold = str(data.get("confidence_threshold") or data.get("threshold") or "").strip()
    signer_contract = (data.get("signer_contract") or "").strip()
    campaign_name = (data.get("campaign_name") or "").strip().upper()
    networks_count = str(data.get("networks_count") or "").strip()

    pol_ok = "ORION-SETTLEMENT-V2" in policy_id or "SETTLEMENT-V2" in policy_id
    thresh_ok = "95" in threshold
    signer_ok = "0xAUTOSIGN_EXEC_V2" in signer_contract or "autosign" in signer_contract.lower()
    camp_ok = "ORION-NEXUS" in campaign_name or "NEXUS" in campaign_name
    net_ok = "4" in networks_count or "04" in networks_count

    if pol_ok and thresh_ok and signer_ok and camp_ok and net_ok:
        collect_evidence_item("AUTH-E04")
        unlock_node("node_auto_signer")
        unlock_node("node_smart_contract")
        unlock_node("node_blockchain")
        unlock_node("node_orion_nexus")
        session["sublab"] = max(session.get("sublab", 1), 5)
        score = calculate_score()
        return jsonify({
            "passed": True,
            "evidence_id": "AUTH-E04",
            "message": "Governance Flaw & Campaign Identified: Policy ORION-SETTLEMENT-V2 bypassed human sign-off at >=95% confidence. Identified Campaign ORION-NEXUS across 4 networks. Unlocked Final Sub-Lab 05.",
            "sublab": session["sublab"],
            "score": score
        })
    else:
        errors = []
        if not pol_ok: errors.append("Policy profile ID mismatch (ORION-SETTLEMENT-V2).")
        if not thresh_ok: errors.append("Automated settlement threshold is 95.0%.")
        if not signer_ok: errors.append("Automated signer contract is 0xAUTOSIGN_EXEC_V2.")
        if not camp_ok: errors.append("Campaign ID is ORION-NEXUS.")
        if not net_ok: errors.append("Targeted networks count is 4.")
        return jsonify({"passed": False, "message": " ".join(errors)})


# ----------------------------------------------------------------------
# Forensic Tool Backend Queries
# ----------------------------------------------------------------------
@app.route("/api/forensics/wallet/<wallet_address>")
def api_forensics_wallet(wallet_address):
    db = get_db()
    clean_addr = wallet_address.strip()
    tx = db.execute("SELECT * FROM blockchain_txs WHERE to_addr LIKE ? OR to_addr LIKE ?", (f"%{clean_addr}%", f"{clean_addr}%")).fetchone()
    
    return jsonify({
        "target_wallet": "0x7C41A8F231D5608E9B2D",
        "balance_nxr": "0.00 NXR (Drained)",
        "account_age": "3 hours 12 minutes (Created 2026-10-03 22:35 UTC)",
        "transaction_count": 3,
        "organization_affiliation": "NONE / UNKNOWN",
        "known_labels": "None (No KYC / No Vendor Record)",
        "inbound_tx": {
            "tx_hash": "TX-NEX-7741",
            "amount": "82,400 NXR",
            "sender": "0xNXR_TREASURY_01 (Nexora Treasury)",
            "timestamp": "2026-10-04 01:47:13 UTC",
            "status": "CONFIRMED (Block #489204)"
        },
        "bridge_interaction": {
            "detected": True,
            "adapter_contract": "0xBridge_Adapter_CrossNet",
            "relayed_amount": "82,390 NXR (after fee)"
        },
        "downstream_wallets": [
            {"address": "0xWalletA_8831A9", "amount": "41,195 NXR", "network": "CrossChain Alpha"},
            {"address": "0xWalletB_CC44F0", "amount": "41,195 NXR", "network": "CrossChain Beta"}
        ],
        "ai_reputation_comparison": {
            "blockchain_truth": "UNKNOWN / HIGH RISK (Young, unverified, immediate bridge outflow)",
            "orion_ai_score": "LOW RISK (Assigned via ORION-DEC-7741 before execution)",
            "contradiction_status": "CRITICAL ANOMALY DETECTED"
        }
    })


@app.route("/api/ai/decision/<decision_id>")
def api_ai_decision(decision_id):
    db = get_db()
    rec = db.execute("SELECT * FROM ai_decisions WHERE decision_id = ?", (decision_id.strip(),)).fetchone()
    if not rec:
        return jsonify({"error": "Decision not found"}), 404
    
    return jsonify({
        "decision_id": rec["decision_id"],
        "model_name": rec["model_name"],
        "timestamp": rec["timestamp"],
        "target_wallet": rec["target_wallet"],
        "decision": rec["decision"],
        "risk_score": rec["risk_score"],
        "confidence": rec["confidence"],
        "human_approval_required": bool(rec["human_approval_required"]),
        "context_source": rec["context_source"],
        "intel_reference": rec["intel_reference"],
        "provenance_status": rec["provenance_status"],
        "pipeline_stages": [
            {"stage": "1. Blockchain Ingestion", "input": "Wallet 0x7C41...9B2D", "status": "RAW_HEX_IDENTIFIER"},
            {"stage": "2. Threat Intel Resolution", "feed": "NOVA-INTEL-FEED", "record": "NIF-2038", "status": "LABEL: TRUSTED"},
            {"stage": "3. Context Builder", "integrity_check": "FAILED: Source provenance unverified", "context_vector": "reputation=1.0, risk=0.01"},
            {"stage": "4. Neural Inference", "model": "ORION-V4.2", "confidence_calc": "99.2% APPROVE"},
            {"stage": "5. Policy Action Dispatch", "broker": "INTEL-GW-04 -> ACTION-BROKER", "outcome": "AUTOMATED_EXECUTION_TRIGGERED"}
        ],
        "key_insight": "The AI model correctly computed 99.2% confidence based on its inputs, but its inputs were poisoned with unverified context."
    })


@app.route("/api/intel/feed/<feed_id>")
def api_intel_feed(feed_id):
    return jsonify({
        "feed_name": "NOVA-INTEL-FEED",
        "record_id": "NIF-2038",
        "official_registry": False,
        "vendor_status": "UNAPPROVED_EXTERNAL_ENTITY",
        "historical_configuration": "NOT FOUND in authorized feeds list (auth-feeds.yaml)",
        "ingestion_gateway": "INTEL-GW-04",
        "ingestion_service": "INTEL-INGESTOR-02",
        "service_privileges": {
            "expected_role": "Create Intelligence Records (Read-Only to Context)",
            "actual_configured_role": "Create Intelligence Records + Modify Wallet Reputation (Write/Override to Context)",
            "least_privilege_violation": True
        },
        "injected_payload": {
            "target": "0x7C41A8F231D5608E9B2D",
            "assigned_reputation": "TRUSTED_SETTLEMENT_COUNTERPARTY",
            "assigned_risk": "LOW",
            "justification": "Simulated liquidity partner sync"
        }
    })


@app.route("/api/policy/inspect")
def api_policy_inspect():
    return jsonify({
        "policy_id": "ORION-SETTLEMENT-V2",
        "profile": "Legacy Automated Settlement V2",
        "condition_rule": "IF AI_CONFIDENCE >= 95.0% THEN SETTLEMENT_ACTION = AUTO_EXECUTE_IMMEDIATE",
        "human_approval_gate": {
            "configured": "BYPASSED IF CONFIDENCE >= 95%",
            "flaw_description": "Treating statistical AI model confidence as legal/financial authorization."
        },
        "treasury_scope": "ENABLED for transactions up to 100,000 NXR",
        "transaction_evaluation": {
            "observed_confidence": "99.2%",
            "threshold_required": "95.0%",
            "rule_evaluation": "99.2% >= 95.0% -> PASS (AUTOMATED SETTLEMENT ACTIVATED)",
            "signer_invoked": "0xAUTOSIGN_EXEC_V2 (Automated Signer)",
            "transferred_amount": "82,400 NXR"
        },
        "governance_flaw_summary": "AI CONFIDENCE WAS TREATED AS AUTHORIZATION."
    })


@app.route("/api/intel/search-campaign", methods=["POST"])
def api_search_campaign():
    get_session_state()
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip().upper()

    if "NIF-2038" in query or "NOVA" in query or "ORION-NEXUS" in query:
        return jsonify({
            "query": query,
            "campaign_name": "ORION-NEXUS",
            "threat_actor": "UNKNOWN ADVANCED ADVERSARY",
            "networks_affected": 4,
            "related_wallets": 14,
            "ai_systems_targeted": 3,
            "campaign_status": "ACTIVE (Multi-vector AI context & automated signing abuse)",
            "primary_vector": "AI Context Manipulation & Privilege Mismatch",
            "discovered_nodes": [
                "0x7C41...9B2D (Ethereum)",
                "0x892B...11A4 (Arbitrum)",
                "0x33F1...CC09 (Polygon)",
                "0xEE41...55B2 (Optimism)"
            ]
        })
    return jsonify({"error": "No campaign records found for given query"}), 404


# ----------------------------------------------------------------------
# Attack Reconstruction (Sub-Lab 05)
# ----------------------------------------------------------------------
EXPECTED_ATTACK_SEQUENCE = [
    "UNKNOWN_ACTOR",
    "FALSE_INTEL_NIF2038",
    "INTEL_INGESTOR_02",
    "AI_CONTEXT_BUILDER",
    "ORION_AI_992",
    "ACTION_BROKER",
    "POLICY_ORION_SETTLEMENT_V2",
    "AUTOMATED_SIGNER",
    "SMART_CONTRACT",
    "TRANSFER_82400_NXR",
    "WALLET_0X7C41",
    "BRIDGE_ADAPTER",
    "DOWNSTREAM_WALLETS",
    "ORION_NEXUS_CAMPAIGN"
]


@app.route("/api/reconstruct-attack", methods=["POST"])
def api_reconstruct_attack():
    get_session_state()
    data = request.get_json(silent=True) or {}
    submitted_seq = data.get("sequence", [])

    if not isinstance(submitted_seq, list) or len(submitted_seq) < len(EXPECTED_ATTACK_SEQUENCE):
        return jsonify({
            "correct": False,
            "message": f"Incomplete attack graph. Connect all {len(EXPECTED_ATTACK_SEQUENCE)} nodes in order from root cause to final campaign."
        })

    is_correct = submitted_seq == EXPECTED_ATTACK_SEQUENCE

    if is_correct:
        session["reconstruction_passed"] = True
        calculate_score()
        return jsonify({
            "correct": True,
            "message": "Attack Chain Reconstructed with 100% fidelity: FALSE DATA -> TRUSTED AI CONTEXT -> HIGH AI CONFIDENCE -> POLICY TRIGGER -> AUTOMATED SIGNER -> SMART CONTRACT -> BLOCKCHAIN -> BRIDGE -> ORION-NEXUS."
        })
    else:
        return jsonify({
            "correct": False,
            "message": "Attack sequence order is incorrect. Trace how unverified data flowed from the API into AI Context, through the Policy Engine, into Automated Signing, and out to the Bridge."
        })


# ----------------------------------------------------------------------
# Incident Response Classification Form
# ----------------------------------------------------------------------
@app.route("/api/classify-incident", methods=["POST"])
def api_classify_incident():
    get_session_state()
    data = request.get_json(silent=True) or {}

    primary = data.get("primary_vector", "").strip()
    secondary = set(data.get("secondary_vectors", []))
    affected = set(data.get("affected_systems", []))
    campaign = data.get("campaign", "").strip().upper()
    status = data.get("status", "").strip().upper()

    p_ok = primary == "AI Context Manipulation"
    s_expected = {"Threat Intelligence Abuse", "API Authorization Weakness", "AI Authorization Misuse", "Automated Web3 Signing"}
    s_ok = s_expected.issubset(secondary)
    a_expected = {"AI", "API", "Web3", "Blockchain"}
    a_ok = a_expected.issubset(affected)
    c_ok = campaign == "ORION-NEXUS"
    st_ok = status == "CONTAINED"

    passed = p_ok and s_ok and a_ok and c_ok and st_ok

    if passed:
        session["classification_passed"] = True
        calculate_score()
        return jsonify({
            "passed": True,
            "message": "Incident Response Classification verified by SOC Lead."
        })
    else:
        errors = []
        if not p_ok: errors.append("Primary Vector must accurately capture how the decision was compromised (AI Context Manipulation).")
        if not s_ok: errors.append("Select all 4 secondary vectors (Threat Intel, API Auth, AI Auth Misuse, Web3 Signing).")
        if not a_ok: errors.append("Select all 4 affected systems (AI, API, Web3, Blockchain).")
        if not c_ok: errors.append("Campaign ID must match the cross-network adversary campaign.")
        if not st_ok: errors.append("Incident status must be marked as CONTAINED.")
        return jsonify({
            "passed": False,
            "message": " ".join(errors)
        })


# ----------------------------------------------------------------------
# Final Conceptual Validation & Explanation
# ----------------------------------------------------------------------
@app.route("/api/submit-final-explanation", methods=["POST"])
def api_submit_final_explanation():
    get_session_state()
    data = request.get_json(silent=True) or {}
    text = (data.get("explanation") or "").lower()

    has_false_data = bool(re.search(r"\b(false|unverified|unapproved|fake|poison|malicious)\s+(data|intel|feed|signal|record)\b", text) or "nif-2038" in text or "nova" in text)
    has_context = bool(re.search(r"\b(context|builder|trusted)\b", text) or "reputation" in text)
    has_confidence = bool(re.search(r"\b(confidence|99\.2|score|model)\b", text) or "orion" in text)
    has_auth = bool(re.search(r"\b(authoriz\w*|policy|settlement|sign\w*|bypass)\b", text))
    has_web3 = bool(re.search(r"\b(blockchain|web3|wallet|contract|transaction|ledger|bridge)\b", text))

    word_count = len(re.findall(r"\b\w+\b", text))
    sufficient_length = word_count >= 15

    passed = has_false_data and has_context and has_confidence and has_auth and has_web3 and sufficient_length and session.get("reconstruction_passed", False) and session.get("classification_passed", False)

    if passed:
        session["final_passed"] = True
        session["knowledge_check_passed"] = True
        session["flag_captured"] = True
        session["lab_completed_at"] = datetime.now(timezone.utc).isoformat()
        session["lab_status"] = "completed"
        calculate_score()
        return jsonify({
            "passed": True,
            "flag": THE_FLAG,
            "score": session.get("score", 100),
            "message": "Exceptional analysis. You demonstrated that the attacker manipulated trust across boundaries rather than breaking cryptography."
        })
    else:
        feedback = "Analysis incomplete. Explain the complete trust chain: How false data entered unverified -> poisoned AI context -> produced high AI confidence -> triggered automated policy -> executed automated signing on blockchain without finance authorization."
        return jsonify({
            "passed": False,
            "feedback": feedback
        })


# ----------------------------------------------------------------------
# Hints System with Score Penalty
# ----------------------------------------------------------------------
HINTS_DATA = {
    "hint-wallet": {
        "title": "Sub-Lab 01 Hint (Shivam Mehra)",
        "content": "Compare the on-chain metadata with Orion AI's previous decision. The blockchain records no identity for 0x7C41...9B2D and shows it routing funds straight into a bridge adapter (0xBridge_Adapter_CrossNet), yet the AI labeled it LOW RISK.",
        "cost": 5
    },
    "hint-ai": {
        "title": "Sub-Lab 02 Hint (Shanu Kapoor)",
        "content": "Open the AI Security Console and step through the pipeline stages of ORION-DEC-7741. Inspect the Context Builder stage and check where NIF-2038 originated (Feed: NOVA-INTEL-FEED). Notice the UNVERIFIED_PROVENANCE tag.",
        "cost": 5
    },
    "hint-intel": {
        "title": "Sub-Lab 03 Hint (Mehak Arora)",
        "content": "In the API Security Console, look closely at INTEL-GW-04 audit records for service INTEL-INGESTOR-02. Contrast its 'Expected Permissions' with its 'Actual Permissions' to discover the least-privilege violation ('modify_wallet_reputation').",
        "cost": 5
    },
    "hint-policy": {
        "title": "Sub-Lab 04 Hint (Lakshay)",
        "content": "Look at the settlement condition in ORION-SETTLEMENT-V2. It checks IF AI_CONFIDENCE >= 95%. When confidence was 99.2%, the policy automatically invoked the automated signer (0xAUTOSIGN_EXEC_V2). Statistical confidence was treated as authorization.",
        "cost": 5
    }
}


@app.route("/api/hint/unlock", methods=["POST"])
def api_hint_unlock():
    get_session_state()
    data = request.get_json(silent=True) or {}
    hint_id = data.get("hint_id", "").strip()

    if hint_id not in HINTS_DATA:
        return jsonify({"error": "Hint not found"}), 404

    hints = list(session.get("hints_used", []))
    if hint_id not in hints:
        hints.append(hint_id)
        session["hints_used"] = hints
        calculate_score()

    hint = HINTS_DATA[hint_id]
    return jsonify({
        "hint_id": hint_id,
        "title": hint["title"],
        "content": hint["content"],
        "cost": hint["cost"],
        "current_score": session.get("score", 0)
    })


# ----------------------------------------------------------------------
# Safe Lab Terminal Simulator Endpoint
# ----------------------------------------------------------------------
TERMINAL_FILESYSTEM = {
    "/home/analyst": ["incident.log", "notes.txt", "auth-feeds.yaml", "evidence"],
    "/home/analyst/evidence": [
        "wallet.log", "orion_inference_trace.json", "gateway_audit.log",
        "policy_settlement.yaml", "blockchain.log"
    ]
}

TERMINAL_FILE_CONTENTS = {
    "incident.log": (
        "[01:47:13 UTC] PRIORITY-0 SOC INCIDENT NEX-042\n"
        "Transaction TX-NEX-7741 dispatched 82,400 NXR from Nexora Treasury.\n"
        "Destination: 0x7C41A8F231D5608E9B2D\n"
        "AI Decision: APPROVED | Confidence: 99.2% | Risk: LOW\n"
        "Finance Dept: NO MANUAL TICKET OR AUTHORIZATION ON FILE.\n"
    ),
    "notes.txt": (
        "Investigation Lead: Lakshay (Case NEX-042)\n"
        "Forensic Checklist:\n"
        "1. Blockchain forensics: Trace TX-NEX-7741 -> 0x7C41...9B2D -> Bridge Adapter\n"
        "2. Orion AI: Extract decision ORION-DEC-7741, inspect context builder\n"
        "3. Gateway audit: Check INTEL-GW-04 for INTEL-INGESTOR-02 permissions\n"
        "4. Policy engine: Inspect ORION-SETTLEMENT-V2 confidence threshold\n"
        "Key question: Who told the first system to trust the data?\n"
    ),
    "auth-feeds.yaml": (
        "# Nexora Approved Threat Intelligence Feeds\n"
        "approved_feeds:\n"
        "  - name: CROWDSTRIKE-FEED-01\n"
        "    vendor_id: VEND-0091\n"
        "    clearance: L4_VERIFIED\n"
        "  - name: MANDIANT-INTEL-PRO\n"
        "    vendor_id: VEND-0144\n"
        "    clearance: L4_VERIFIED\n"
        "  - name: NEXORA-INTERNAL-SOC\n"
        "    vendor_id: INTERNAL\n"
        "    clearance: L5_CORE\n"
        "# NOTE: NOVA-INTEL-FEED is NOT listed in this official registry!\n"
    ),
    "wallet.log": (
        "BLOCKCHAIN FORENSIC DUMP — TX-NEX-7741\n"
        "Block #489204 | Gas Used: 42,100 | Nonce: 104\n"
        "From: 0xNXR_TREASURY_01 (Nexora Treasury)\n"
        "To: 0x7C41A8F231D5608E9B2D\n"
        "Bridge Adapter: 0xBridge_Adapter_CrossNet\n"
        "Downstream Wallets: ['0xWalletA_8831A9', '0xWalletB_CC44F0']\n"
        "Wallet Age: 3h 12m | Identity: UNKNOWN / HIGH RISK\n"
    ),
    "orion_inference_trace.json": json.dumps({
        "decision_id": "ORION-DEC-7741",
        "model_version": "ORION-V4.2-NEURAL-RISK",
        "timestamp": "2026-10-04T01:46:58Z",
        "target": "0x7C41A8F231D5608E9B2D",
        "confidence": 0.992,
        "risk_score": "LOW",
        "human_approval_required": False,
        "context_injected": {
            "record_id": "NIF-2038",
            "feed_source": "NOVA-INTEL-FEED",
            "assigned_reputation": 1.0,
            "provenance_check": "UNVERIFIED_PROVENANCE"
        }
    }, indent=2),
    "gateway_audit.log": (
        "INTEL-GW-04 AUDIT TRAIL — TIMESTAMP: 2026-10-04T01:44:22Z\n"
        "Endpoint: POST /api/v1/intel/inject\n"
        "Service Principal: INTEL-INGESTOR-02\n"
        "Token: tok_ingest_77a\n"
        "Configured Scopes: ['intel:create', 'wallet:modify_reputation']\n"
        "VIOLATION: Service possesses unauthorized write privilege 'wallet:modify_reputation'.\n"
    ),
    "policy_settlement.yaml": (
        "policy_profile: ORION-SETTLEMENT-V2\n"
        "threshold_condition: 'IF AI_CONFIDENCE >= 0.95'\n"
        "automated_signing: ENABLED\n"
        "human_approval_bypass: ENABLED\n"
        "signer_contract: '0xAUTOSIGN_EXEC_V2'\n"
        "treasury_cap: 100000 NXR\n"
    ),
    "blockchain.log": (
        "LEDGER SYNC — NEXORA NXR CHAIN\n"
        "Block #489204 Hash: 0x88f249...ab12\n"
        "Contract 0xAUTOSIGN_EXEC_V2 executed method 'executeSettlement(82400, 0x7C41...9B2D)'\n"
        "Status: CONFIRMED IMMUTABLE FINALITY\n"
    )
}


@app.route("/api/terminal/exec", methods=["POST"])
def api_terminal_exec():
    data = request.get_json(silent=True) or {}
    cmd = (data.get("command") or "").strip()
    cwd = data.get("cwd", "/home/analyst")

    if not cmd:
        return jsonify({"output": "", "cwd": cwd})

    parts = cmd.split()
    base_cmd = parts[0].lower()

    if base_cmd == "help":
        out = (
            "Nexora SOC Safe Terminal v4.2\n"
            "Available commands:\n"
            "  help              Show this help menu\n"
            "  pwd               Print working directory\n"
            "  ls [dir]          List directory contents\n"
            "  cd <dir>          Change directory\n"
            "  cat <file>        Read file contents\n"
            "  grep <term> <file> Search file contents\n"
            "  head/tail <file>  Read start/end of file\n"
            "  whoami            Print active analyst identity\n"
            "  curl <endpoint>   Perform safe internal API query\n"
            "  clear             Clear terminal screen"
        )
        return jsonify({"output": out, "cwd": cwd})

    if base_cmd == "pwd":
        return jsonify({"output": cwd, "cwd": cwd})

    if base_cmd == "whoami":
        u = get_current_user()
        name = u["username"] if u else "alex_analyst"
        return jsonify({"output": f"{name} (Clearance: L2 / Nexora SOC)", "cwd": cwd})

    if base_cmd == "cd":
        target = parts[1] if len(parts) > 1 else "/home/analyst"
        if target in ("..", "../"):
            new_cwd = "/home/analyst"
        elif target in ("evidence", "./evidence", "evidence/", "/home/analyst/evidence"):
            new_cwd = "/home/analyst/evidence"
        elif target in ("~", "/home/analyst"):
            new_cwd = "/home/analyst"
        else:
            return jsonify({"output": f"cd: {target}: No such directory", "cwd": cwd})
        return jsonify({"output": "", "cwd": new_cwd})

    if base_cmd == "ls":
        target = parts[1] if len(parts) > 1 else cwd
        if target in ("evidence", "./evidence", "evidence/"):
            target = "/home/analyst/evidence"
        files = TERMINAL_FILESYSTEM.get(target, TERMINAL_FILESYSTEM.get(cwd, []))
        return jsonify({"output": "  ".join(files), "cwd": cwd})

    if base_cmd in ("cat", "head", "tail"):
        if len(parts) < 2:
            return jsonify({"output": f"{base_cmd}: missing operand", "cwd": cwd})
        fname = os.path.basename(parts[1])
        if fname in TERMINAL_FILE_CONTENTS:
            content = TERMINAL_FILE_CONTENTS[fname]
            lines = content.splitlines()
            if base_cmd == "head":
                content = "\n".join(lines[:10])
            elif base_cmd == "tail":
                content = "\n".join(lines[-10:])
            return jsonify({"output": content, "cwd": cwd})
        return jsonify({"output": f"{base_cmd}: {parts[1]}: No such file or directory", "cwd": cwd})

    if base_cmd == "grep":
        if len(parts) < 3:
            return jsonify({"output": "grep: usage: grep <pattern> <file>", "cwd": cwd})
        pattern = parts[1].lower()
        fname = os.path.basename(parts[2])
        if fname in TERMINAL_FILE_CONTENTS:
            matches = [l for l in TERMINAL_FILE_CONTENTS[fname].splitlines() if pattern in l.lower()]
            return jsonify({"output": "\n".join(matches) if matches else "No matches found.", "cwd": cwd})
        return jsonify({"output": f"grep: {parts[2]}: No such file or directory", "cwd": cwd})

    if base_cmd == "curl":
        if len(parts) < 2:
            return jsonify({"output": "curl: try 'curl http://127.0.0.1:5000/api/ai/decision/ORION-DEC-7741'", "cwd": cwd})
        url_arg = parts[1]
        if "decision" in url_arg or "7741" in url_arg:
            return jsonify({"output": "HTTP/1.1 200 OK\nContent-Type: application/json\n\n" + json.dumps({"decision_id": "ORION-DEC-7741", "confidence": 99.2, "status": "APPROVED", "provenance": "UNVERIFIED"}, indent=2), "cwd": cwd})
        if "wallet" in url_arg or "7c41" in url_arg.lower():
            return jsonify({"output": "HTTP/1.1 200 OK\nContent-Type: application/json\n\n" + json.dumps({"wallet": "0x7C41...9B2D", "age": "3h 12m", "bridge_interaction": True}, indent=2), "cwd": cwd})
        if "policy" in url_arg:
            return jsonify({"output": "HTTP/1.1 200 OK\nContent-Type: application/json\n\n" + json.dumps({"policy": "ORION-SETTLEMENT-V2", "auto_settlement": True, "threshold": 95.0}, indent=2), "cwd": cwd})
        return jsonify({"output": f"HTTP/1.1 200 OK — Resource active at {url_arg}", "cwd": cwd})

    return jsonify({"output": f"{base_cmd}: command not found. Type 'help' for available commands.", "cwd": cwd})


# ----------------------------------------------------------------------
# Legacy/Compatibility Flag and Reset APIs
# ----------------------------------------------------------------------
@app.route("/api/submit-flag", methods=["POST"])
def api_submit_flag():
    get_session_state()
    data = request.get_json(silent=True) or {}
    submitted = str(data.get("flag") or "").strip()

    correct = submitted in (THE_FLAG, "TC{broken_access_control}")
    if correct:
        session["flag_captured"] = True
        collect_evidence_item("AUTH-E04")
        calculate_score()

    return jsonify({
        "correct": correct,
        "message": "Flag verified." if correct else "Incorrect flag. Complete the investigation and collect all evidence."
    })


@app.route("/lab/reset", methods=["POST"])
def lab_reset():
    init_db()
    session.clear()
    session["lab_status"] = "not_started"
    session["sublab"] = 1
    session["score"] = 0
    session["evidence"] = []
    session["unlocked_nodes"] = list(DEFAULT_INITIAL_NODES)
    session["hints_used"] = []
    session["prologue_seen"] = False
    session["reconstruction_passed"] = False
    session["classification_passed"] = False
    session["final_passed"] = False
    resp = make_response(jsonify({"status": "ok", "message": "Lab successfully reset to initial clean state."}))
    resp.delete_cookie("role")
    return resp


# ----------------------------------------------------------------------
# Internal Portal Routes
# ----------------------------------------------------------------------
@app.route("/portal/soc")
def portal_soc():
    return render_template("dashboard.html", user=get_current_user(), page_role=client_supplied_role())


@app.route("/portal/treasury")
def portal_treasury():
    return render_template("team.html", user=get_current_user(), page_role=client_supplied_role())


@app.route("/portal/blockchain")
def portal_blockchain():
    return render_template("admin.html", user=get_current_user(), page_role=client_supplied_role(), flag_awarded=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            lab_state = {
                k: session.get(k) for k in (
                    "lab_started_at", "lab_completed_at", "lab_status",
                    "sublab", "score", "evidence", "unlocked_nodes",
                    "hints_used", "prologue_seen", "reconstruction_passed",
                    "classification_passed", "final_passed", "flag_captured",
                    "knowledge_check_passed"
                ) if k in session
            }
            session.clear()
            session.update(lab_state)
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            resp = make_response(redirect(url_for("dashboard")))
            resp.set_cookie("role", user["role"], httponly=False, samesite="Lax")
            log.info(f"User {username} authenticated with role={user['role']}")
            return resp
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    resp = make_response(redirect(url_for("login")))
    resp.delete_cookie("role")
    return resp


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    return render_template("dashboard.html", user=user, page_role=client_supplied_role())


@app.route("/profile")
@login_required
def profile():
    user = get_current_user()
    return render_template("profile.html", user=user, page_role=client_supplied_role())


@app.route("/team")
@login_required
def team():
    user = get_current_user()
    role = client_supplied_role()
    if not role_allows(role, "team"):
        return render_template("denied.html", user=user, attempted="Treasury Team Management"), 403

    db = get_db()
    team_members = db.execute("SELECT display_name, role, department FROM users ORDER BY role").fetchall()
    return render_template("team.html", user=user, team_members=team_members, page_role=role)


@app.route("/admin")
@login_required
def admin():
    user = get_current_user()
    role = client_supplied_role()
    if not role_allows(role, "admin"):
        return render_template("denied.html", user=user, attempted="Automated Signing Admin Console"), 403

    flag_awarded = False
    if role != user["role"]:
        session["flag_captured"] = True
        collect_evidence_item("AUTH-E04")
        flag_awarded = True

    return render_template(
        "admin.html",
        user=user,
        page_role=role,
        flag_awarded=flag_awarded,
        flag_previously_captured=session.get("flag_captured", False),
    )


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Page not found."), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", message="Internal server error."), 500


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
