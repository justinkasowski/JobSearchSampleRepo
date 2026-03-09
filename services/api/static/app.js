//region Firebase
  import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js";
  import {
    getAuth,
    GoogleAuthProvider,
    signInWithPopup,
    onAuthStateChanged
  } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";

  const LOCAL_RUN = window.LOCAL_RUN;
  const firebaseConfig = {
  apiKey: "AIzaSyDaMaoajiceJbaGC3y7XK4qyc7kMkA2ApY",
  authDomain: "jobsearchsamplerepo.firebaseapp.com",
  projectId: "jobsearchsamplerepo",
  storageBucket: "jobsearchsamplerepo.firebasestorage.app",
  messagingSenderId: "622998584903",
  appId: "1:622998584903:web:6c2c5c78a59b8cc2fb7b62",
  measurementId: "G-BQWKGHL67L"
  };

  let auth = null;
  let firebaseToken = null;

  if (!LOCAL_RUN) {
    const app = initializeApp(firebaseConfig);
    auth = getAuth(app);

    const provider = new GoogleAuthProvider();

    document.getElementById("googleLoginBtn").onclick = async () => {
      try {
        const result = await signInWithPopup(auth, provider);
        firebaseToken = await result.user.getIdToken();
      } catch (err) {
        alert("Login failed: " + err.message);
      }
    };

    onAuthStateChanged(auth, async (user) => {

      const overlay = document.getElementById("authOverlay");

      if (user) {
        firebaseToken = await user.getIdToken();
        overlay.style.display = "none";
      } else {
        overlay.style.display = "flex";
      }
    });
  } else {
    // local mode skips login
    document.getElementById("authOverlay").style.display = "none";
  }

  async function getAuthHeaders() {
    const headers = {
      "Content-Type": "application/json"
    };

    if (!LOCAL_RUN && auth?.currentUser) {
      const token = await auth.currentUser.getIdToken();
      headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
  }

//endregion

//region Health Check
  let modelDetailText = "Warming Ollama model...";
  let lastHealthCheckText = "Last check: never";

  function formatHealthTimestamp(date = new Date()) {
    return date.toLocaleString();
  }

  function renderWarmupDetail() {
    document.getElementById("modelDetail").textContent = modelDetailText;
    document.getElementById("healthDetail").textContent = lastHealthCheckText;
  }

  function setWarmupStatus(state, detail = "") {
    const statusEl = document.getElementById("warmupStatus");
    const pillEl = document.getElementById("warmupPill");

    pillEl.classList.remove("ready", "error");

    if (state === "loading") {
      statusEl.textContent = "Loading...";
    } else if (state === "ready") {
      statusEl.textContent = "Ready";
      pillEl.classList.add("ready");
    } else if (state === "error") {
      statusEl.textContent = "Error";
      pillEl.classList.add("error");
    }

    if (detail) {
      modelDetailText = detail;
    }

    renderWarmupDetail();
  }

  async function healthCheck() {
    const button = document.querySelector('.status-card-inline button');
    const previousText = button.textContent;
    button.disabled = true;
    button.textContent = "Checking...";

    try {
      const response = await fetch("/health");
      const rawText = await response.text();

      let data;
      try {
        data = JSON.parse(rawText);
      } catch {
        lastHealthCheckText = `Last check: ${formatHealthTimestamp()}`;
        renderWarmupDetail();
        alert("The service returned an invalid response. Restart the demo if queries are failing.");
        return;
      }

      if (!response.ok || data.status !== "ok") {
          lastHealthCheckText = `Last check: ${formatHealthTimestamp()}`;
          renderWarmupDetail();
          const errorText = data?.detail?.error || data?.error || "Unknown health failure.";
          alert(`The service is unhealthy: ${errorText}`);
          return;
        }

      lastHealthCheckText = `Last check: ${formatHealthTimestamp()}`;
      renderWarmupDetail();
      alert("The API and Ollama service appear healthy. If queries are still failing, restart the demo.");
    } catch (err) {
      lastHealthCheckText = `Last check: ${formatHealthTimestamp()}`;
      renderWarmupDetail();
      alert("Health check failed. The server may be down or unreachable. Restart the demo and try again.");
    } finally {
      button.disabled = false;
      button.textContent = previousText;
    }
  }

  async function runSilentHealthCheck() {
    try {
      const response = await fetch("/health");
      const rawText = await response.text();

      let data;
      try {
        data = JSON.parse(rawText);
      } catch {
        lastHealthCheckText = `Last check: ${formatHealthTimestamp()}`;
        renderWarmupDetail();
        return;
      }

      if (!response.ok || data.status !== "ok") {
        lastHealthCheckText = `Last check: ${formatHealthTimestamp()}`;
        renderWarmupDetail();
        return;
      }

      lastHealthCheckText = `Last check: ${formatHealthTimestamp()}`;
      renderWarmupDetail();
    } catch {
      lastHealthCheckText = `Last check: ${formatHealthTimestamp()}`;
      renderWarmupDetail();
    }
  }

  async function warmupModel() {
    setWarmupStatus("loading", "Warming Ollama model...");

    try {
      const response = await fetch("/warmup", { method: "POST" });
      const rawText = await response.text();

      let data;
      try {
        data = JSON.parse(rawText);
      } catch {
        setWarmupStatus("error", "Model warmup failed. Restart container.");
        return;
      }

      if (!response.ok) {
        setWarmupStatus("error", "Model not available. Restart container.");
        return;
      }

      setWarmupStatus("ready", `Model ${data.model ?? "unknown"} is loaded.`);
    } catch (err) {
      setWarmupStatus("error", "Model not found. Restart container.");
    }
  }
//endregion

//region Corpus
  async function checkCorpusStatus() {
    const ingestResult = document.getElementById("ingestResult");

    try {
      const response = await fetch("/rag/status");
      const data = await response.json();

      const status = data.corpus_status;
      const missing = Object.keys(status).filter(corpus => !status[corpus]);

      if (missing.length === 0) {
        ingestResult.textContent = "Corpus Ingested";
      } else {
        ingestResult.textContent = "Missing: " + missing.join(", ");
      }
    } catch (err) {
      ingestResult.textContent = "Unable to check corpus status.";
    }
  }

  async function ingestCorpus() {
    const corpus = document.getElementById("ingestCorpus").value;
    const cleanRebuild = document.getElementById("cleanRebuild").checked;
    const resultBox = document.getElementById("ingestResult");

    resultBox.textContent = "Running ingest...";

    try {
      const response = await fetch("/rag/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          corpus,
          clean_rebuild: cleanRebuild
        })
      });

      const rawText = await response.text();

      let data;
      try {
        data = JSON.parse(rawText);
      } catch {
        resultBox.textContent = rawText;
        return;
      }

      resultBox.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      resultBox.textContent = "Error: " + err;
    }
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function renderCitations(citations) {
    const citationsBox = document.getElementById("citationsResult");

    if (!citations || citations.length === 0) {
      citationsBox.innerHTML = `<div class="empty-state">No citations returned.</div>`;
      return;
    }

    citationsBox.innerHTML = citations.map(c => {
      const snippetBlock = c.snippet
        ? `
          <div class="citation-snippet-block">
            <div class="citation-snippet-label">Snippet</div>
            <pre class="citation-snippet-text">${escapeHtml(c.snippet)}</pre>
          </div>
        `
        : "";

      return `
        <div class="citation">
          <div class="citation-grid">
            <div><strong>source:</strong> ${escapeHtml(c.source)}</div>
            <div><strong>page:</strong> ${escapeHtml(c.page)}</div>
            <div><strong>doc_id:</strong> ${escapeHtml(c.doc_id)}</div>
            <div><strong>corpus:</strong> ${escapeHtml(c.corpus)}</div>
            <div><strong>section:</strong> ${escapeHtml(c.section)}</div>
            <div><strong>document_type:</strong> ${escapeHtml(c.document_type)}</div>
            <div style="grid-column: 1 / -1;"><strong>source_path:</strong> ${escapeHtml(c.source_path)}</div>
          </div>
          ${snippetBlock}
        </div>
      `;
    }).join("");
  }


  function syncCorpusQueryVisibility() {
    const enabled = document.getElementById("enableCorpusQuery").checked;
    const corpusBlock = document.getElementById("corpusControlsBlock");
    const topKBlock = document.getElementById("topKBlock");

    if (enabled) {
      corpusBlock.classList.remove("hidden");
      topKBlock.classList.remove("hidden");
    } else {
      corpusBlock.classList.add("hidden");
      topKBlock.classList.add("hidden");
    }
  }
//endregion

//region Generate Questions
  const generatedQuestions = [
    {
      question: "What is the approval process for employee PTO requests?",
      corpus: "all",
      section: "all",
      documentType: "all"
    },
    {
      question: "Are employees allowed to store customer personal data on local devices?",
      corpus: "all",
      section: "all",
      documentType: "all",
    },
    {
      question: "Who is responsible for employee data privacy compliance?",
      corpus: "all",
      section: "all",
      documentType: "all"
    },
    {
      question: "What is the company policy on employee expense reimbursements?",
      corpus: "all",
      section: "all",
      documentType: "all"
    },
    {
      question: "Can sales representatives offer discounts without manager approval?",
      corpus: "all",
      section: "all",
      documentType: "all",
    },
    {
      question: "What onboarding training must new employees complete?",
      corpus:"all",
      section: "all",
      documentType: "all",
    },
    {
      question: "What systems must employees use to store customer information?",
      corpus: "all",
      section: "all",
      documentType: "all",
    },
    {
      question: "What are the consequences for violating company compliance policies?",
      corpus: "all",
      section: "all",
      documentType: "all"
    },
    {
      question: "How should employees report suspected compliance violations?",
      corpus: "all",
      section: "all",
      documentType: "all",
    },
    {
      question: "What sales practices are prohibited by company policy?",
      corpus: "all",
      section: "all",
      documentType: "all",
    },
    {
      question: "What is the company's discord policy?",
      corpus: "all",
      section: "all",
      documentType: "all",
    },
    {
      question: "Does the company use slack?",
      corpus: "all",
      section: "all",
      documentType:"all",
    }
  ];

  const integrationPrompts = [
        "Send this to Slack policy.",
        "Send this to Discord HR.",
        "Send this to Slack.",
        "Send this to Discord.",
        "Post to Slack.",
        "Post to Discord.",
        "Post to Discord, HR policy or sales",
        "Post to Slack, HR policy or sales"
      ];

  function generateQuestion() {
    const item = generatedQuestions[Math.floor(Math.random() * generatedQuestions.length)];
    const integrationsEnabled = document.getElementById("enableWebhookIntegrations").checked;

    let questionText = item.question;

    if (integrationsEnabled) {
      const extra = integrationPrompts[Math.floor(Math.random() * integrationPrompts.length)];
      questionText = `${questionText}\n\n${extra}`;
    }

    document.getElementById("question").value = questionText;
    document.getElementById("queryCorpus").value = item.corpus;
    document.getElementById("sectionSelect").value = item.section;
    document.getElementById("documentTypeSelect").value = item.documentType;
  }
//endregion

//region Queries
  async function runDirectQuery(payload, answerBox, answerJsonBox) {
    const response = await fetch("/directQuery", {
    method: "POST",
    headers: await getAuthHeaders(),
    body: JSON.stringify(payload)
    });

    const rawText = await response.text();

    let data;
    try {
      data = JSON.parse(rawText);
    } catch {
      answerBox.textContent = `HTTP ${response.status}`;
      answerJsonBox.textContent = rawText;
      return null;
    }

    if (!response.ok) {
      answerBox.textContent = data.detail || `HTTP ${response.status}`;
      answerJsonBox.textContent = JSON.stringify(data, null, 2);
      return null;
    }

    answerBox.textContent = data.response ?? "No response returned.";
    answerJsonBox.textContent = JSON.stringify(data, null, 2);

    return data;
  }

  async function runCorpusQuery(payload, answerBox, answerJsonBox, ingestResultBox) {
    const response = await fetch("/rag/query", {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify(payload)
    });

    const rawText = await response.text();

    let data;
    try {
      data = JSON.parse(rawText);
    } catch {
      answerBox.textContent = `HTTP ${response.status}`;
      answerJsonBox.textContent = rawText;
      return null;
    }

    if (!response.ok) {
      answerBox.textContent = data.detail || `HTTP ${response.status}`;
      answerJsonBox.textContent = JSON.stringify(data, null, 2);
      renderCitations([]);
      return null;
    }

    if (data.auto_ingested) {
      if (data.ingest_result) {
        ingestResultBox.textContent = JSON.stringify(data.ingest_result, null, 2);
      } else {
        ingestResultBox.textContent = "Auto-ingest completed.";
      }
    }

    answerBox.textContent = data.answer ?? "No answer returned.";
    answerJsonBox.textContent = JSON.stringify(data, null, 2);
    renderCitations(data.citations || []);

    return data;
  }

  async function runQuery() {
    const queryCorpusEnabled = document.getElementById("enableCorpusQuery").checked;
    const integrationsEnabled = document.getElementById("enableWebhookIntegrations").checked;

    const corpus = document.getElementById("queryCorpus").value;
    const section = document.getElementById("sectionSelect").value;
    const documentType = document.getElementById("documentTypeSelect").value;
    const k = parseInt(document.getElementById("kValue").value, 10);
    const keepAlive = document.getElementById("keepAlive").value.trim();
    const rawQuestion = document.getElementById("question").value.trim();
    const cleanedQuestion = stripGeneratedIntegrationPrompt(rawQuestion);

    const answerBox = document.getElementById("answerResult");
    const answerJsonBox = document.getElementById("answerJsonResult");
    const ingestResultBox = document.getElementById("ingestResult");

    if (!rawQuestion) {
      answerBox.textContent = "Please enter a question.";
      answerJsonBox.textContent = "Please enter a question.";
      return;
    }

    answerBox.textContent = "Running query...";
    answerJsonBox.textContent = "Running query...";
    renderCitations([]);
    setIntegrationJson("No integration plan run yet.");

    if (!integrationsEnabled) {
      document.getElementById("integrationPanel").classList.add("hidden");
      setIntegrationJson("Integrations disabled.");
    } else {
      populateIntegrationPlan(null);
    }

    try {
      let result = null;
      let answerToSend = "";

      if (queryCorpusEnabled) {
        const payload = {
          corpus,
          question: cleanedQuestion,
          k,
          section,
          document_type: documentType
        };

        if (keepAlive) {
          payload.keep_alive = keepAlive;
        }

        result = await runCorpusQuery(payload, answerBox, answerJsonBox, ingestResultBox);
        if (!result) return;

        answerToSend = result.answer || "";
      } else {
        const payload = {
          prompt: cleanedQuestion
        };

        if (keepAlive) {
          payload.keep_alive = keepAlive;
        }

        result = await runDirectQuery(payload, answerBox, answerJsonBox);
        renderCitations([]);
        if (!result) return;

        answerToSend = result.response || "";
      }

      if (integrationsEnabled) {
        try {
          const plan = await runIntegrationPlan(rawQuestion, keepAlive);
          populateIntegrationPlan(plan);

          if (
            !plan.requiresReview &&
            Array.isArray(plan.integrations) &&
            !plan.integrations.includes("none") &&
            answerToSend
          ) {
            const sendResult = await runIntegrationSend(plan, answerToSend);
            setIntegrationJson({
              plan,
              send_result: sendResult
            });
          }
        } catch (planErr) {
          console.error(planErr);
          setIntegrationJson({ error: String(planErr) });
          populateIntegrationPlan({
            integrations: ["none"],
            channel: "none",
            requiresReview: true,
            rationale: "Integration planning failed and requires manual review."
          });
        }
      }
    } catch (err) {
      answerBox.textContent = "Error: " + err;
      answerJsonBox.textContent = "Error: " + err;
      renderCitations([]);
    }
  }
//endregion

//region Slack/Discord Integration

let currentIntegrationPlan = null;
let integrationAlreadySent = false;

  function stripGeneratedIntegrationPrompt(text) {
    if (!text) return text;

    let cleaned = text;

    for (const prompt of integrationPrompts) {
      const escaped = prompt.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const regex = new RegExp(`\\s*${escaped}\\s*$`, "i");
      cleaned = cleaned.replace(regex, "");
    }

    return cleaned.trim();
  }

  function syncIntegrationPanelVisibility() {
    const enabled = document.getElementById("enableWebhookIntegrations").checked;
    const panel = document.getElementById("integrationPanel");

    if (enabled) {
      panel.classList.remove("hidden");
    } else {
      panel.classList.add("hidden");
      document.getElementById("integrationTypeSelect").value = "none";
      document.getElementById("integrationChannelSelect").value = "none";
      document.getElementById("integrationRationale").value = "";
      document.getElementById("integrationStatus").textContent = "No action detected.";
      document.getElementById("integrationStatus").className = "integration-status";
      document.getElementById("integrationReportBtn").textContent = "Report Bug";
      syncIntegrationChannelState();
    }
  }

  function setIntegrationJson(value) {
    const box = document.getElementById("integrationJsonResult");

    if (!box) return;

    if (typeof value === "string") {
      box.textContent = value;
    } else {
      box.textContent = JSON.stringify(value, null, 2);
    }
  }

  function populateIntegrationPlan(plan) {
    const panel = document.getElementById("integrationPanel");
    const statusEl = document.getElementById("integrationStatus");
    const reportBtn = document.getElementById("integrationReportBtn");
    const sendBtn = document.getElementById("integrationSendBtn");

    panel.classList.remove("hidden");
    sendBtn.classList.remove("manual-ready", "sent");
    sendBtn.textContent = "Execute Manually";
    sendBtn.disabled = true;

    if (!plan) {
      currentIntegrationPlan = null;
      integrationAlreadySent = false;

      statusEl.textContent = "No manual action needed.";
      statusEl.className = "integration-status";
      reportBtn.textContent = "Report Bug";

      document.getElementById("integrationTypeSelect").value = "none";
      document.getElementById("integrationChannelSelect").value = "none";
      document.getElementById("integrationRationale").value = "No action plan returned.";
      syncIntegrationChannelState();
      return;
    }

    currentIntegrationPlan = structuredClone(plan);
    integrationAlreadySent = false;

    const integrations = Array.isArray(plan.integrations) ? plan.integrations : ["none"];
    const primaryIntegration = integrations.find(x => x !== "none") || "none";

    document.getElementById("integrationTypeSelect").value = primaryIntegration;
    document.getElementById("integrationChannelSelect").value = plan.channel || "none";
    document.getElementById("integrationRationale").value = plan.rationale || "";

    if (primaryIntegration === "none") {
      statusEl.textContent = "No action detected.";
      statusEl.className = "integration-status";
    } else if (plan.requiresReview) {
      statusEl.textContent = "Manual review required.";
      statusEl.className = "integration-status review";
      sendBtn.disabled = false;
      sendBtn.classList.add("manual-ready");
    } else {
      statusEl.textContent = "No manual review needed.";
      statusEl.className = "integration-status success";
    }

    syncIntegrationChannelState();
  }

  function syncIntegrationChannelState() {
    const integration = document.getElementById("integrationTypeSelect").value;
    document.getElementById("integrationChannelSelect").disabled = integration === "none";
  }

  async function runIntegrationPlan(question, keepAlive) {
    const response = await fetch("/integrations/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        instruction: question,
        keep_alive: keepAlive || null
      })
    });

    const rawText = await response.text();

    let data;
    try {
      data = JSON.parse(rawText);
    } catch {
      setIntegrationJson(rawText);
      throw new Error(`Integration plan returned invalid JSON: ${rawText}`);
    }

    setIntegrationJson(data);

    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }

    return data.plan || data;
  }

  async function runIntegrationSend(plan, message) {
    const response = await fetch("/integrations/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plan: plan,
        message: message
      })
    });

    const rawText = await response.text();

    let data;
    try {
      data = JSON.parse(rawText);
    } catch {
      throw new Error(`Integration send returned invalid JSON: ${rawText}`);
    }

    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }

    return data;
  }

  async function reportIntegrationBug() {
    const reportText = window.prompt("Describe the bug:");
    if (reportText === null) return;

    const question = document.getElementById("question")?.value || "";
    const answer = document.getElementById("answerResult")?.textContent || "";
    const integrationType = document.getElementById("integrationTypeSelect")?.value || "";
    const integrationChannel = document.getElementById("integrationChannelSelect")?.value || "";
    const integrationRationale = document.getElementById("integrationRationale")?.value || "";

    let integrationJson = {};
    let ragJson = {};

    try {
      const integrationRaw = document.getElementById("integrationJsonResult")?.textContent || "{}";
      integrationJson = integrationRaw.trim() ? JSON.parse(integrationRaw) : {};
    } catch {
      integrationJson = { raw: document.getElementById("integrationJsonResult")?.textContent || "" };
    }

    try {
      const ragRaw = document.getElementById("answerJsonResult")?.textContent || "{}";
      ragJson = ragRaw.trim() ? JSON.parse(ragRaw) : {};
    } catch {
      ragJson = { raw: document.getElementById("answerJsonResult")?.textContent || "" };
    }

    const headers = {
      "Content-Type": "application/json"
    };

    if (!window.LOCAL_RUN && auth.currentUser) {
      const token = await auth.currentUser.getIdToken();
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch("/bugs/report", {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify({
        question,
        answer,
        integration_type: integrationType,
        integration_channel: integrationChannel,
        integration_rationale: integrationRationale,
        integration_json: integrationJson,
        rag_json: ragJson,
        report_text: reportText,
        report_type: "bug"
      })
    });

    const data = await response.json();

    if (!response.ok) {
      alert(data.detail || "Failed to submit bug report.");
      return;
    }

    alert("Bug report submitted.");
  }

  async function submitManualReviewReport({ appropriate, note }) {
    const question = document.getElementById("question")?.value || "";
    const answer = document.getElementById("answerResult")?.textContent || "";
    const integrationType = document.getElementById("integrationTypeSelect")?.value || "";
    const integrationChannel = document.getElementById("integrationChannelSelect")?.value || "";
    const integrationRationale = document.getElementById("integrationRationale")?.value || "";

    let integrationJson = {};
    let ragJson = {};

    try {
      const integrationRaw = document.getElementById("integrationJsonResult")?.textContent || "{}";
      integrationJson = integrationRaw.trim() ? JSON.parse(integrationRaw) : {};
    } catch {
      integrationJson = { raw: document.getElementById("integrationJsonResult")?.textContent || "" };
    }

    try {
      const ragRaw = document.getElementById("answerJsonResult")?.textContent || "{}";
      ragJson = ragRaw.trim() ? JSON.parse(ragRaw) : {};
    } catch {
      ragJson = { raw: document.getElementById("answerJsonResult")?.textContent || "" };
    }

    const response = await fetch("/bugs/report", {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify({
        question,
        answer,
        integration_type: integrationType,
        integration_channel: integrationChannel,
        integration_rationale: integrationRationale,
        integration_json: integrationJson,
        rag_json: ragJson,
        report_text: note || "",
        report_type: "manual_review",
        manual_review_appropriate: appropriate,
        manual_review_note: note || ""
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Failed to submit manual review report.");
    }

    return data;
  }

  let pendingManualReviewResolve = null;
  function openManualReviewModal() {
    const modal = document.getElementById("manualReviewModal");
    const noteInput = document.getElementById("manualReviewNote");
    const checked = document.querySelector('input[name="manualReviewAppropriate"]:checked');

    if (checked) {
      checked.checked = false;
    }

    noteInput.value = "";
    modal.classList.remove("hidden");
  }

  function closeManualReviewModal() {
    const modal = document.getElementById("manualReviewModal");
    modal.classList.add("hidden");

    if (pendingManualReviewResolve) {
      pendingManualReviewResolve(null);
      pendingManualReviewResolve = null;
    }
  }

  function submitManualReviewModal() {
    const selected = document.querySelector('input[name="manualReviewAppropriate"]:checked');
    const note = document.getElementById("manualReviewNote").value.trim();

    if (!selected) {
      alert("Select Yes or No.");
      return;
    }

    const appropriate = selected.value === "yes";

    document.getElementById("manualReviewModal").classList.add("hidden");

    if (pendingManualReviewResolve) {
      pendingManualReviewResolve({ appropriate, note });
      pendingManualReviewResolve = null;
    }
  }

  function promptManualReviewFeedback() {
    return new Promise((resolve) => {
      pendingManualReviewResolve = resolve;
      openManualReviewModal();
    });
  }

  async function executeManualIntegration() {
    const button = document.getElementById("integrationSendBtn");
    const statusEl = document.getElementById("integrationStatus");

    if (!currentIntegrationPlan) {
      alert("No integration plan available.");
      return;
    }

    if (integrationAlreadySent) {
      alert("This plan was already executed.");
      return;
    }

    const selectedIntegration = document.getElementById("integrationTypeSelect").value;
    const selectedChannel = document.getElementById("integrationChannelSelect").value;
    const answerText = document.getElementById("answerResult")?.textContent?.trim() || "";

    if (button.disabled) {
      return;
    }

    if (!answerText || answerText === "No query run yet." || answerText === "Running query...") {
      alert("No answer available to send.");
      return;
    }

    if (selectedIntegration === "none" || selectedChannel === "none") {
      alert("Select a valid integration and channel.");
      return;
    }

    const planToSend = {
      ...currentIntegrationPlan,
      integrations: [selectedIntegration],
      channel: selectedChannel,
      requiresReview: false
    };

    button.disabled = true;
    statusEl.textContent = "Executing manual send...";

    try {
      const sendResult = await runIntegrationSend(planToSend, answerText);

      integrationAlreadySent = true;
      currentIntegrationPlan = structuredClone(planToSend);

      setIntegrationJson({
        plan: planToSend,
        send_result: sendResult
      });

      statusEl.textContent = "Manual send complete.";
      statusEl.className = "integration-status success";

      const feedback = await promptManualReviewFeedback();
      if (feedback) {
        await submitManualReviewReport(feedback);
      }

      button.textContent = "Executed";
    } catch (err) {
      button.disabled = false;
      statusEl.textContent = "Manual send failed.";
      statusEl.className = "integration-status review";
      setIntegrationJson({ error: String(err) });
      alert("Manual execution failed: " + err);
    }
  }

//endregion

//region Window
  window.addEventListener("load", async () => {
    window.scrollTo({ top: 0, behavior: "instant" });

    try {
      await warmupModel();
    } catch (e) {
      console.error(e);
    }

    try {
      await checkCorpusStatus();
    } catch (e) {
      console.error(e);
    }

    try {
      await runSilentHealthCheck();
    } catch (e) {
      console.error(e);
    }
    setInterval(runSilentHealthCheck, 900000);

    syncIntegrationPanelVisibility();
    syncIntegrationChannelState();
    syncCorpusQueryVisibility();

    document
      .getElementById("enableWebhookIntegrations")
      .addEventListener("change", syncIntegrationPanelVisibility);

    document
      .getElementById("integrationTypeSelect")
      .addEventListener("change", syncIntegrationChannelState);

    document
      .getElementById("enableCorpusQuery")
      .addEventListener("change", syncCorpusQueryVisibility);
  });

  window.getFirebaseToken = async () => {
    if (LOCAL_RUN) return null;

    if (!firebaseToken && auth?.currentUser) {
      firebaseToken = await auth.currentUser.getIdToken();
    }

    return firebaseToken;
  };

  window.healthCheck = healthCheck;
  window.ingestCorpus = ingestCorpus;
  window.generateQuestion = generateQuestion;
  window.runQuery = runQuery;
  window.reportIntegrationBug = reportIntegrationBug;
  window.executeManualIntegration = executeManualIntegration;
  window.closeManualReviewModal = closeManualReviewModal;
  window.submitManualReviewModal = submitManualReviewModal;
//endregion
