// ============================================================
// NEXORA SOC — CASE NEX-042: THE GHOST IN THE LEDGER
// Cyber Range Interactive Controller & Virtual Desktop Engine
// ============================================================

let currentLabState = null;
let statePollInterval = null;
let toastTimeout = null;
let deskTermCwd = "/home/analyst";
let deskZIndex = 100;

// Investigation Map Node Metadata
const MAP_NODE_DATA = {
  "node_unknown_tx": {
    "title": "TX-NEX-7741 (82,400 NXR Outflow)",
    "type": "Blockchain Transaction",
    "status": "CONFIRMED on Block #489204",
    "timestamp": "2026-10-04 01:47:13 UTC",
    "observation": "82,400 NXR transferred from Nexora Treasury. Smart contract executed without human finance ticket.",
    "anomaly": "No corporate financial ticket authorized this transaction."
  },
  "node_wallet_7c41": {
    "title": "Destination 0x7C41...9B2D",
    "type": "Web3 Wallet Address",
    "status": "UNKNOWN / UNREGISTERED",
    "timestamp": "2026-10-04 01:47:13 UTC",
    "observation": "Account created 3 hours ago. Immediately funneled funds into Cross-Chain Bridge Adapter.",
    "anomaly": "On-chain identity is HIGH RISK, yet Orion AI categorized it as LOW RISK."
  },
  "node_ai_decision_7741": {
    "title": "ORION-DEC-7741 (Neural Risk Model)",
    "type": "AI Decision Engine",
    "status": "APPROVED (99.2% Confidence)",
    "timestamp": "2026-10-04 01:46:58 UTC",
    "observation": "Neural model calculated 99.2% approval based on reputation vector injected by Context Builder.",
    "anomaly": "Input context provenance was unverified."
  },
  "node_ai_context_nif2038": {
    "title": "Context Record NIF-2038",
    "type": "AI Context Feature",
    "status": "CORRUPTED / POISONED",
    "timestamp": "2026-10-04 01:45:00 UTC",
    "observation": "Assigned reputation score 1.0 (Trusted Counterparty) to fresh wallet 0x7C41...9B2D.",
    "anomaly": "Unverified data source accepted directly into AI context."
  },
  "node_threat_intel_feed": {
    "title": "NOVA-INTEL-FEED",
    "type": "External Threat Feed",
    "status": "UNREGISTERED VENDOR",
    "timestamp": "2026-10-04 01:44:00 UTC",
    "observation": "Feed is completely absent from official Nexora vendor registry (auth-feeds.yaml).",
    "anomaly": "Rogue intelligence feed spoofed counterparty trust."
  },
  "node_api_intel_gw04": {
    "title": "Gateway INTEL-GW-04 & INTEL-INGESTOR-02",
    "type": "Internal Ingestion API",
    "status": "LEAST PRIVILEGE VIOLATION",
    "timestamp": "2026-10-04 01:44:22 UTC",
    "observation": "Service held unauthorized write permissions ('modify_wallet_reputation').",
    "anomaly": "API permission mismatch enabled direct context manipulation."
  },
  "node_action_broker": {
    "title": "Orion Action Broker",
    "type": "Execution Dispatcher",
    "status": "AUTOMATED TRIGGER",
    "timestamp": "2026-10-04 01:47:00 UTC",
    "observation": "Converted model confidence output into smart contract dispatch request.",
    "anomaly": "Failed to enforce zero-trust boundary before dispatch."
  },
  "node_auto_signer": {
    "title": "0xAUTOSIGN_EXEC_V2 (Policy Engine)",
    "type": "Automated Signer",
    "status": "POLICY TRIGGERED",
    "timestamp": "2026-10-04 01:47:05 UTC",
    "observation": "ORION-SETTLEMENT-V2 rule: IF CONFIDENCE >= 95% -> BYPASS HUMAN APPROVAL.",
    "anomaly": "AI confidence was treated as legal/financial authorization."
  },
  "node_smart_contract": {
    "title": "Nexora Treasury Smart Contract",
    "type": "Web3 Contract",
    "status": "EXECUTED",
    "timestamp": "2026-10-04 01:47:10 UTC",
    "observation": "Validated cryptographic signature from auto-signer and released 82,400 NXR.",
    "anomaly": "Smart contract operated exactly as coded, executing an unauthorized payout."
  },
  "node_blockchain": {
    "title": "NXR Ledger & Cross-Chain Bridge",
    "type": "Blockchain Infrastructure",
    "status": "SETTLED / BRIDGED",
    "timestamp": "2026-10-04 01:47:13 UTC",
    "observation": "Funds split across Bridge Adapter into Wallets A and B on downstream chains.",
    "anomaly": "Immutable record of what happened, not proof of authorization."
  },
  "node_orion_nexus": {
    "title": "Campaign ORION-NEXUS",
    "type": "Global Adversary Campaign",
    "status": "ACTIVE THREAT",
    "timestamp": "CURRENT",
    "observation": "14 related wallets across 4 blockchain networks targeting 3 AI decision pipelines.",
    "anomaly": "Systemic attack abusing trusted boundaries across Web3 and AI."
  }
};

// Sub-Lab 05 Attack Reconstruction Node Bank
const RECON_TOKENS = [
  { id: "UNKNOWN_ACTOR", label: "1. UNKNOWN THREAT ACTOR" },
  { id: "FALSE_INTEL_NIF2038", label: "2. FALSE INTELLIGENCE NIF-2038" },
  { id: "INTEL_INGESTOR_02", label: "3. OVERPRIVILEGED INTEL-INGESTOR-02" },
  { id: "AI_CONTEXT_BUILDER", label: "4. POISONED AI CONTEXT BUILDER" },
  { id: "ORION_AI_992", label: "5. ORION AI (99.2% CONFIDENCE)" },
  { id: "ACTION_BROKER", label: "6. ORION ACTION BROKER" },
  { id: "POLICY_ORION_SETTLEMENT_V2", label: "7. POLICY ORION-SETTLEMENT-V2 (AUTO-SETTLE)" },
  { id: "AUTOMATED_SIGNER", label: "8. AUTOMATED SIGNER (0xAUTOSIGN_EXEC_V2)" },
  { id: "SMART_CONTRACT", label: "9. TREASURY SMART CONTRACT" },
  { id: "TRANSFER_82400_NXR", label: "10. 82,400 NXR OUTFLOW" },
  { id: "WALLET_0X7C41", label: "11. WALLET 0x7C41...9B2D" },
  { id: "BRIDGE_ADAPTER", label: "12. CROSS-CHAIN BRIDGE ADAPTER" },
  { id: "DOWNSTREAM_WALLETS", label: "13. WALLETS A & B" },
  { id: "ORION_NEXUS_CAMPAIGN", label: "14. CAMPAIGN ORION-NEXUS (4 NETWORKS)" }
];

let placedReconSequence = [];

// ============================================================
// Core Initialization & Polling
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  initReconBoard();
  refreshState();
  statePollInterval = setInterval(refreshState, 2000);

  // Load any saved incident notes from localStorage
  const savedNotes = localStorage.getItem('nexora_incident_notes');
  if (savedNotes) {
    const editor = document.getElementById('desk-notes-editor');
    if (editor) editor.value = savedNotes;
  }
});

async function refreshState() {
  try {
    const res = await fetch('/api/state');
    if (!res.ok) return;
    const data = await res.json();
    currentLabState = data;
    updateUI(data);
  } catch (e) {
    console.warn("State refresh failed:", e);
  }
}

function updateUI(data) {
  // Timer & Prologue
  const timerEl = document.getElementById('lab-timer');
  if (timerEl) timerEl.textContent = formatTime(data.elapsed_seconds);

  const prologueOverlay = document.getElementById('prologue-overlay');
  if (prologueOverlay) {
    if (data.prologue_seen || data.lab_status === 'running' || data.lab_status === 'completed') {
      prologueOverlay.classList.add('hidden');
    } else {
      prologueOverlay.classList.remove('hidden');
    }
  }

  // Header counters
  const sublabEl = document.getElementById('sublab-indicator');
  if (sublabEl) sublabEl.textContent = `SUB-LAB 0${data.sublab} / 05`;

  const scoreEl = document.getElementById('score-counter');
  if (scoreEl) scoreEl.textContent = `${data.score} PTS`;

  const evidenceEl = document.getElementById('evidence-counter');
  if (evidenceEl) evidenceEl.textContent = `${data.evidence.length} / 4`;

  // Chapter statuses and unlock logic
  updateChapters(data.sublab, data.evidence);

  // Update Persistent Map & Locker
  renderEvidenceGrid();

  // Update SOC Feed
  renderSocFeed(data.soc_feed);

  // Check Final Completion
  if (data.final_passed || data.lab_status === 'completed') {
    const card = document.getElementById('lab-complete-card');
    if (card) card.style.display = 'block';
    const finalScore = document.getElementById('final-score-display');
    if (finalScore) finalScore.textContent = `${data.score} PTS`;
  }
}

function updateChapters(currentSublab, evidence) {
  for (let i = 1; i <= 5; i++) {
    const card = document.getElementById(`chapter-${i}`);
    const status = document.getElementById(`ch-status-${i}`);
    if (!card || !status) continue;

    if (i < currentSublab) {
      card.className = 'chapter-card completed';
      status.textContent = '✓ COMPLETED';
      status.style.color = '#10b981';
    } else if (i === currentSublab) {
      card.className = 'chapter-card active open';
      status.textContent = '● IN PROGRESS';
      status.style.color = '#00f0ff';
    } else {
      card.className = 'chapter-card locked';
      status.textContent = '🔒 LOCKED';
      status.style.color = '#64748b';
    }
  }

  // Update Attack Chain Tracker in Hero Banner
  const chainMapping = [
    { id: 'cnode-1', active: currentSublab >= 3 },
    { id: 'cnode-2', active: currentSublab >= 2 },
    { id: 'cnode-3', active: currentSublab >= 2 },
    { id: 'cnode-4', active: currentSublab >= 4 },
    { id: 'cnode-5', active: currentSublab >= 1 }
  ];
  chainMapping.forEach(c => {
    const el = document.getElementById(c.id);
    if (el) el.classList.toggle('active', c.active);
  });
}

function toggleChapter(id) {
  const card = document.getElementById(id);
  if (card && !card.classList.contains('locked')) {
    card.classList.toggle('open');
  }
}

// ============================================================
// Prologue
// ============================================================
async function acknowledgePrologue() {
  const btn = document.getElementById('prologue-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'INITIALIZING...'; }
  try {
    await fetch('/api/start-lab', { method: 'POST' });
    await fetch('/api/prologue/acknowledge', { method: 'POST' });
    document.getElementById('prologue-overlay')?.classList.add('hidden');
    notify("Workstation provisioned. Case NEX-042 active.");
    openAppWindow('terminal');
    refreshState();
  } catch (e) {
    notify("Initialization error.");
    if (btn) { btn.disabled = false; btn.textContent = 'LAUNCH PERSONAL WORKSTATION & INITIALIZE CASE →'; }
  }
}

// ============================================================
// View Switcher (Split / Story Mode / Workstation Fullscreen)
// ============================================================
function setViewMode(mode) {
  const body = document.querySelector('.cyber-range-body');
  const btnSplit = document.getElementById('vbtn-split');
  const btnStory = document.getElementById('vbtn-story');
  const btnWorkstation = document.getElementById('vbtn-workstation');
  if (!body) return;

  body.classList.remove('view-story', 'view-workstation');
  if (btnSplit) btnSplit.classList.remove('active');
  if (btnStory) btnStory.classList.remove('active');
  if (btnWorkstation) btnWorkstation.classList.remove('active');

  if (mode === 'story') {
    body.classList.add('view-story');
    if (btnStory) btnStory.classList.add('active');
  } else if (mode === 'workstation') {
    body.classList.add('view-workstation');
    if (btnWorkstation) btnWorkstation.classList.add('active');
  } else {
    if (btnSplit) btnSplit.classList.add('active');
  }
}

// ============================================================
// Virtual Workstation Window Manager
// ============================================================
function openAppWindow(appId) {
  // If story mode was active, switch to split mode so user sees the workstation window
  const body = document.querySelector('.cyber-range-body');
  if (body && body.classList.contains('view-story')) {
    setViewMode('split');
  }

  const win = document.getElementById(`win-${appId}`);
  const tab = document.getElementById(`tab-${appId}`);
  if (!win) return;

  win.classList.remove('minimized');
  win.classList.add('open', 'active-win');
  bringWinToFront(`win-${appId}`);

  if (tab) tab.classList.add('active');

  if (appId === 'terminal') {
    setTimeout(() => document.getElementById('desk-term-input')?.focus(), 50);
  } else if (appId === 'evidence') {
    renderEvidenceGrid();
  }
}

function closeAppWindow(appId) {
  const win = document.getElementById(`win-${appId}`);
  const tab = document.getElementById(`tab-${appId}`);
  if (win) {
    win.classList.remove('active-win', 'open');
    win.classList.add('minimized');
  }
  if (tab) tab.classList.remove('active');
}

function minimizeAppWindow(appId) {
  closeAppWindow(appId);
}

function toggleAppWindow(appId) {
  const win = document.getElementById(`win-${appId}`);
  if (win && win.classList.contains('active-win') && !win.classList.contains('minimized')) {
    closeAppWindow(appId);
  } else {
    openAppWindow(appId);
  }
}

function bringWinToFront(winId) {
  deskZIndex += 1;
  const win = document.getElementById(winId);
  if (win) {
    win.style.zIndex = deskZIndex;
    win.classList.add('open', 'active-win');
  }
  document.querySelectorAll('.vdesk-window').forEach(w => {
    if (w.id === winId) {
      w.classList.add('active-win');
    } else {
      w.classList.remove('active-win');
    }
  });
}

function toggleDeskMenu(event) {
  event.stopPropagation();
  const dropdown = document.getElementById('vdesk-app-dropdown');
  if (dropdown) {
    dropdown.classList.toggle('open');
  }
}

document.addEventListener('click', () => {
  const dropdown = document.getElementById('vdesk-app-dropdown');
  if (dropdown) dropdown.classList.remove('open');
});

// ============================================================
// Sub-Lab 01: Web3 Blockchain Forensics Validation
// ============================================================
async function submitSublab01() {
  const tx = document.getElementById('f1-tx')?.value.trim() || "";
  const wallet = document.getElementById('f1-wallet')?.value.trim() || "";
  const bridge = document.getElementById('f1-bridge')?.value.trim() || "";
  const bcStatus = document.getElementById('f1-bc-status')?.value || "";
  const aiStatus = document.getElementById('f1-ai-status')?.value || "";
  const feedback = document.getElementById('f1-feedback');

  try {
    const res = await fetch('/api/sublab/validate-01', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tx_hash: tx,
        destination_wallet: wallet,
        bridge_adapter: bridge,
        blockchain_status: bcStatus,
        ai_pre_score_status: aiStatus
      })
    });
    const data = await res.json();
    if (feedback) {
      feedback.className = `validation-msg ${data.passed ? 'correct' : 'incorrect'}`;
      feedback.textContent = data.passed ? `✅ ${data.message} Evidence WEB3-E01 secured!` : `❌ ${data.message}`;
    }
    if (data.passed) {
      notify("Sub-Lab 01 Completed! Stage 02 Unlocked.");
      refreshState();
    }
  } catch (e) {
    notify("Validation request failed.");
  }
}

// ============================================================
// Sub-Lab 02: AI Security Audit Validation
// ============================================================
async function submitSublab02() {
  const decision = document.getElementById('f2-decision')?.value.trim() || "";
  const confidence = document.getElementById('f2-confidence')?.value.trim() || "";
  const intel = document.getElementById('f2-intel')?.value.trim() || "";
  const feed = document.getElementById('f2-feed')?.value.trim() || "";
  const provenance = document.getElementById('f2-provenance')?.value || "";
  const feedback = document.getElementById('f2-feedback');

  try {
    const res = await fetch('/api/sublab/validate-02', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        decision_id: decision,
        confidence_score: confidence,
        injected_record_id: intel,
        feed_name: feed,
        provenance_tag: provenance
      })
    });
    const data = await res.json();
    if (feedback) {
      feedback.className = `validation-msg ${data.passed ? 'correct' : 'incorrect'}`;
      feedback.textContent = data.passed ? `✅ ${data.message} Evidence AI-E02 secured!` : `❌ ${data.message}`;
    }
    if (data.passed) {
      notify("Sub-Lab 02 Completed! Stage 03 Unlocked.");
      refreshState();
    }
  } catch (e) {
    notify("Validation request failed.");
  }
}

// ============================================================
// Sub-Lab 03: API Least Privilege Audit Validation
// ============================================================
async function submitSublab03() {
  const gateway = document.getElementById('f3-gateway')?.value.trim() || "";
  const service = document.getElementById('f3-service')?.value.trim() || "";
  const endpoint = document.getElementById('f3-endpoint')?.value.trim() || "";
  const perm = document.getElementById('f3-perm')?.value.trim() || "";
  const feedback = document.getElementById('f3-feedback');

  try {
    const res = await fetch('/api/sublab/validate-03', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        gateway_id: gateway,
        service_name: service,
        endpoint: endpoint,
        permission_scope: perm
      })
    });
    const data = await res.json();
    if (feedback) {
      feedback.className = `validation-msg ${data.passed ? 'correct' : 'incorrect'}`;
      feedback.textContent = data.passed ? `✅ ${data.message} Evidence CYBER-E03 secured!` : `❌ ${data.message}`;
    }
    if (data.passed) {
      notify("Sub-Lab 03 Completed! Stage 04 Unlocked.");
      refreshState();
    }
  } catch (e) {
    notify("Validation request failed.");
  }
}

// ============================================================
// Sub-Lab 04: AI Governance & Policy Validation
// ============================================================
async function submitSublab04() {
  const policy = document.getElementById('f4-policy')?.value.trim() || "";
  const threshold = document.getElementById('f4-threshold')?.value.trim() || "";
  const signer = document.getElementById('f4-signer')?.value.trim() || "";
  const campaign = document.getElementById('f4-campaign')?.value.trim() || "";
  const networks = document.getElementById('f4-networks')?.value.trim() || "";
  const feedback = document.getElementById('f4-feedback');

  try {
    const res = await fetch('/api/sublab/validate-04', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        policy_id: policy,
        confidence_threshold: threshold,
        signer_contract: signer,
        campaign_name: campaign,
        networks_count: networks
      })
    });
    const data = await res.json();
    if (feedback) {
      feedback.className = `validation-msg ${data.passed ? 'correct' : 'incorrect'}`;
      feedback.textContent = data.passed ? `✅ ${data.message} Evidence AUTH-E04 secured!` : `❌ ${data.message}`;
    }
    if (data.passed) {
      notify("Sub-Lab 04 Completed! Sub-Lab 05 Unlocked.");
      refreshState();
    }
  } catch (e) {
    notify("Validation request failed.");
  }
}

// ============================================================
// Sub-Lab 05: Attack Graph Reconstruction Board
// ============================================================
function initReconBoard() {
  const slotsContainer = document.getElementById('recon-slots-container');
  const bankContainer = document.getElementById('recon-bank-container');
  if (!slotsContainer || !bankContainer) return;

  // 14 drop slots
  slotsContainer.innerHTML = Array.from({ length: 14 }).map((_, i) => `
    <div class="recon-slot-row">
      <span class="slot-num">${i + 1}.</span>
      <div class="slot-target" id="recon-slot-${i}" onclick="removeTokenFromSlot(${i})">
        <span class="slot-placeholder">[ Click a node below to place here ]</span>
      </div>
    </div>
  `).join('');

  // Node token bank
  bankContainer.innerHTML = RECON_TOKENS.map(t => `
    <div class="recon-token" id="token-${t.id}" onclick="placeTokenInNextSlot('${t.id}')">
      ${t.label}
    </div>
  `).join('');
}

function placeTokenInNextSlot(tokenId) {
  if (placedReconSequence.includes(tokenId)) return;
  if (placedReconSequence.length >= 14) {
    notify("All 14 slots filled. Verify sequence or click a slot to remove.");
    return;
  }
  placedReconSequence.push(tokenId);
  updateReconSlotDisplay();
}

function removeTokenFromSlot(idx) {
  if (idx < placedReconSequence.length) {
    placedReconSequence.splice(idx, 1);
    updateReconSlotDisplay();
  }
}

function updateReconSlotDisplay() {
  for (let i = 0; i < 14; i++) {
    const slotEl = document.getElementById(`recon-slot-${i}`);
    if (!slotEl) continue;
    if (i < placedReconSequence.length) {
      const tId = placedReconSequence[i];
      const token = RECON_TOKENS.find(t => t.id === tId);
      slotEl.className = 'slot-target filled';
      slotEl.innerHTML = `<strong>${token.label}</strong> <span style="font-size:10px; color:#94a3b8; margin-left:auto;">[Click to remove]</span>`;
    } else {
      slotEl.className = 'slot-target';
      slotEl.innerHTML = `<span class="slot-placeholder">[ Click a node below to place here ]</span>`;
    }
  }

  RECON_TOKENS.forEach(t => {
    const tokenEl = document.getElementById(`token-${t.id}`);
    if (tokenEl) {
      tokenEl.classList.toggle('placed', placedReconSequence.includes(t.id));
    }
  });
}

function autoPopulateReconHelper() {
  placedReconSequence = RECON_TOKENS.map(t => t.id);
  updateReconSlotDisplay();
  notify("Attack graph sequence populated for review.");
}

async function submitAttackReconstruction() {
  const feedback = document.getElementById('recon-feedback');
  if (placedReconSequence.length < 14) {
    if (feedback) {
      feedback.className = 'validation-msg incorrect';
      feedback.textContent = `❌ Please place all 14 nodes into the attack graph before verification.`;
    }
    return;
  }

  try {
    const res = await fetch('/api/reconstruct-attack', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sequence: placedReconSequence })
    });
    const data = await res.json();
    if (feedback) {
      feedback.className = `validation-msg ${data.correct ? 'correct' : 'incorrect'}`;
      feedback.textContent = data.correct ? `✅ ${data.message}` : `❌ ${data.message}`;
    }
    refreshState();
  } catch (e) {
    notify("Reconstruction check failed.");
  }
}

// ============================================================
// Sub-Lab 05: Incident Response Classification
// ============================================================
async function submitIncidentClassification() {
  const primary = document.getElementById('ir-primary-vector')?.value || "";
  const secNodes = Array.from(document.querySelectorAll('input[name="ir-sec-vector"]:checked')).map(el => el.value);
  const affNodes = Array.from(document.querySelectorAll('input[name="ir-aff-system"]:checked')).map(el => el.value);
  const campaign = document.getElementById('ir-campaign')?.value || "";
  const status = document.getElementById('ir-status')?.value || "";
  const feedback = document.getElementById('classification-feedback');

  try {
    const res = await fetch('/api/classify-incident', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        primary_vector: primary,
        secondary_vectors: secNodes,
        affected_systems: affNodes,
        campaign: campaign,
        status: status
      })
    });
    const data = await res.json();
    if (feedback) {
      feedback.className = `validation-msg ${data.passed ? 'correct' : 'incorrect'}`;
      feedback.textContent = data.passed ? `✅ ${data.message}` : `❌ ${data.message}`;
    }
    refreshState();
  } catch (e) {
    notify("Classification submission failed.");
  }
}

// ============================================================
// Sub-Lab 05: Final Conceptual Explanation & Flag
// ============================================================
async function submitFinalExplanation() {
  const explanation = document.getElementById('final-explanation-text')?.value || "";
  const feedback = document.getElementById('final-feedback');

  try {
    const res = await fetch('/api/submit-final-explanation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ explanation: explanation })
    });
    const data = await res.json();
    if (feedback) {
      feedback.className = `validation-msg ${data.passed ? 'correct' : 'incorrect'}`;
      feedback.textContent = data.passed ? `✅ ${data.message} Flag: ${data.flag}` : `❌ ${data.feedback}`;
    }
    refreshState();
  } catch (e) {
    notify("Explanation verification failed.");
  }
}

// ============================================================
// Workstation Desktop Tools: Campaign Search, Files, Notes, CLI
// ============================================================
async function searchDeskCampaign() {
  const input = document.getElementById('desk-campaign-query')?.value || "";
  const display = document.getElementById('desk-campaign-results');
  if (!display) return;

  try {
    const res = await fetch('/api/intel/search-campaign', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: input })
    });
    const data = await res.json();
    display.style.display = 'block';
    display.innerHTML = `
      <div style="font-size:12px; line-height:1.6;">
        <div style="color:#00f0ff; font-weight:700;">CAMPAIGN DETECTED: ${data.campaign_name} (${data.campaign_status})</div>
        <div><strong>Threat Actor:</strong> ${data.threat_actor}</div>
        <div><strong>Networks Affected:</strong> ${data.networks_affected} &bull; <strong>Related Wallets:</strong> ${data.related_wallets} &bull; <strong>AI Systems Targeted:</strong> ${data.ai_systems_targeted}</div>
        <div style="color:#f59e0b; margin-top:4px;"><strong>Discovered Nodes:</strong> ${data.discovered_nodes.join(', ')}</div>
      </div>
    `;
  } catch (e) {
    display.style.display = 'block';
    display.innerHTML = "No campaign records found.";
  }
}

async function handleDeskTerminalKey(e) {
  if (e.key !== 'Enter') return;
  const input = document.getElementById('desk-term-input');
  if (!input) return;
  const cmd = input.value.trim();
  input.value = '';

  const history = document.getElementById('desk-term-history');
  if (history) {
    history.textContent += `\nalex@nexora-soc:${deskTermCwd}$ ${cmd}\n`;
  }

  if (cmd.toLowerCase() === 'clear') {
    if (history) history.textContent = '';
    return;
  }

  try {
    const res = await fetch('/api/terminal/exec', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd, cwd: deskTermCwd })
    });
    const data = await res.json();
    deskTermCwd = data.cwd;
    const prompt = document.getElementById('desk-term-prompt');
    if (prompt) prompt.textContent = `alex@nexora-soc:${deskTermCwd}$`;
    if (history && data.output) {
      history.textContent += `${data.output}\n`;
    }
    const screen = document.querySelector('.terminal-body-desk');
    if (screen) screen.scrollTop = screen.scrollHeight;
  } catch (err) {
    if (history) history.textContent += `Error executing command.\n`;
  }
}

function viewFileContent(filename) {
  const preview = document.getElementById('desk-file-preview');
  if (!preview) return;

  const fileMap = {
    'incident.log': `[01:47:13 UTC] CRITICAL: 82,400 NXR Treasury Outflow confirmed on Block #489204.\n[01:47:05 UTC] AUTH_POLICY: ORION-SETTLEMENT-V2 executed signer contract 0xAUTOSIGN_EXEC_V2.\n[01:46:58 UTC] AI_INFERENCE: ORION-DEC-7741 returned confidence 99.2% for wallet 0x7C41...9B2D.`,
    'notes.txt': `Target Case: NEX-042\nLead Investigator: Lakshay\nBlockchain: Shivam Mehra\nAI Security: Shanu Kapoor\nCyber / Threat Intel: Mehak Arora\n\nCore Rule: Never treat AI output as automated financial authority.`,
    'auth-feeds.yaml': `version: 2.1\napproved_threat_feeds:\n  - name: CROWDSTRIKE-FEED-01\n    vendor_id: VEND-001\n    status: ACTIVE_APPROVED\n  - name: MANDIANT-INTEL-PRO\n    vendor_id: VEND-002\n    status: ACTIVE_APPROVED\n  - name: NEXORA-INTERNAL-SOC\n    vendor_id: VEND-INT-01\n    status: INTERNAL`,
    'wallet.log': `WALLET FORENSICS REPORT:\nTarget: 0x7C41A8F231D5608E9B2D\nCreated: 2026-10-04 22:35:00 UTC (Age: ~3.2h)\nBridge Interaction: 0xBridge_Adapter_CrossNet -> Relayed to Wallet-A, Wallet-B\nStatus: UNKNOWN / HIGH RISK`,
    'orion_inference_trace.json': `{\n  "decision_id": "ORION-DEC-7741",\n  "input_context": {\n    "wallet": "0x7C41A8F231D5608E9B2D",\n    "threat_intel_record": "NIF-2038",\n    "feed_source": "NOVA-INTEL-FEED",\n    "provenance_status": "UNVERIFIED_PROVENANCE"\n  },\n  "neural_model_confidence": 0.992,\n  "action_broker": "DISPATCH_SETTLEMENT"\n}`,
    'gateway_audit.log': `[2026-10-04 01:44:22 UTC] INGESTION AUDIT:\nGateway: INTEL-GW-04\nCaller Principal: INTEL-INGESTOR-02\nEndpoint: POST /api/v1/intel/inject\nScopes Detected: ["create_intel", "modify_wallet_reputation"]\nPolicy Check: Least Privilege Violation`
  };

  preview.innerHTML = `<pre style="font-family:'JetBrains Mono',monospace; font-size:12px; color:#00f0ff; margin:0; white-space:pre-wrap;">${fileMap[filename] || "File not found."}</pre>`;
}

function saveDeskNotes() {
  const editor = document.getElementById('desk-notes-editor');
  const status = document.getElementById('desk-notes-status');
  if (editor) {
    localStorage.setItem('nexora_incident_notes', editor.value);
    if (status) {
      status.textContent = "Saved to encrypted analyst disk!";
      status.style.color = "#10b981";
      setTimeout(() => { if (status) status.textContent = ""; }, 2500);
    }
  }
}

// Evidence Locker Grid
function renderEvidenceGrid() {
  const container = document.getElementById('desk-evidence-grid');
  if (!container) return;

  const allItems = [
    { id: "WEB3-E01", title: "Blockchain Forensics & Reputation Discrepancy", cat: "Web3 Security", desc: "0x7C41...9B2D is an unverified fresh wallet that bridged 82,400 NXR. Blockchain reality: UNKNOWN / HIGH RISK, Orion label: LOW RISK." },
    { id: "AI-E02", title: "Context Integrity Failure & Unverified Source", cat: "AI Security", desc: "ORION-DEC-7741 reached 99.2% confidence via poisoned record NIF-2038 from unregistered NOVA-INTEL-FEED with UNVERIFIED_PROVENANCE." },
    { id: "CYBER-E03", title: "API Least Privilege & Ingestion Flaw", cat: "API Security", desc: "Ingestion service INTEL-INGESTOR-02 possessed unauthorized scope 'modify_wallet_reputation' on INTEL-GW-04." },
    { id: "AUTH-E04", title: "AI Confidence Misuse as Automated Authorization", cat: "AI Governance / Web3", desc: "ORION-SETTLEMENT-V2 automated signing for >=95% confidence via 0xAUTOSIGN_EXEC_V2. Campaign ORION-NEXUS spans 4 networks." }
  ];

  const collected = currentLabState?.evidence || [];

  container.innerHTML = allItems.map(item => {
    const isCollected = collected.includes(item.id);
    return `
      <div class="ev-card ${isCollected ? 'collected' : ''}" style="background:#0f172a; border:1px solid ${isCollected ? '#10b981' : '#334155'}; border-radius:6px; padding:10px; margin-bottom:8px;">
        <div style="font-size:11px; font-weight:700; color:${isCollected ? '#10b981' : '#64748b'};">${item.id} &bull; ${item.cat}</div>
        <div style="font-size:13px; font-weight:700; color:#f8fafc; margin:4px 0;">${item.title}</div>
        <div style="font-size:11px; color:#94a3b8;">${isCollected ? item.desc : '🔒 Complete the relevant Sub-Lab to secure this forensic artifact.'}</div>
        <div style="font-size:10px; font-weight:700; color:${isCollected ? '#00f0ff' : '#64748b'}; margin-top:6px;">${isCollected ? 'STATUS: VERIFIED & SEALED' : 'STATUS: UNCOLLECTED'}</div>
      </div>
    `;
  }).join('');
}

// SOC Feed
function renderSocFeed(messages = []) {
  const container = document.getElementById('soc-feed-messages');
  if (!container) return;

  container.innerHTML = messages.map(m => `
    <div class="feed-msg ${m.type === 'CRITICAL' ? 'critical' : ''}">
      <div class="feed-msg-head">
        <span class="feed-author ${m.role === 'SYSTEM' ? 'system' : ''}">${m.author} (${m.role})</span>
        <span class="feed-time">${m.timestamp}</span>
      </div>
      <div class="feed-body">${m.message}</div>
    </div>
  `).join('');
}

// Hints System
async function unlockHint(hintId) {
  if (!confirm("Unlocking this hint will deduct 5 points from your investigation score. Proceed?")) return;
  try {
    const res = await fetch('/api/hint/unlock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hint_id: hintId })
    });
    const data = await res.json();
    alert(`💡 ${data.title}:\n\n${data.content}`);
    refreshState();
  } catch (e) {
    notify("Could not retrieve hint.");
  }
}

// Browser navigation
function navigateBrowser(path) {
  const iframe = document.getElementById('browser-iframe');
  const urlDisplay = document.getElementById('browser-url-display');
  if (iframe) iframe.src = path;
  if (urlDisplay) urlDisplay.textContent = `http://nexora.internal${path}`;
}
function browserNavBack() { try { document.getElementById('browser-iframe')?.contentWindow.history.back(); } catch(e){} }
function browserNavForward() { try { document.getElementById('browser-iframe')?.contentWindow.history.forward(); } catch(e){} }
function browserNavReload() { try { document.getElementById('browser-iframe')?.contentWindow.location.reload(); } catch(e){} }

// Lab Reset
async function resetLab() {
  if (!confirm("Are you sure you want to reset Case NEX-042 to its initial clean state?")) return;
  try {
    await fetch('/lab/reset', { method: 'POST' });
    location.reload();
  } catch (e) {
    notify("Failed to reset lab.");
  }
}

// Toast helper
function notify(msg) {
  const toast = document.getElementById('soc-toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.remove('show'), 3500);
}

function formatTime(totalSec) {
  totalSec = Math.max(0, Number(totalSec) || 0);
  const h = Math.floor(totalSec / 3600), m = Math.floor((totalSec % 3600) / 60), s = totalSec % 60;
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}
