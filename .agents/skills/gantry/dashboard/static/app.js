// Read-only Gantry dashboard renderer. This file makes no request that can mutate
// state: it only polls GET /api/state and rebuilds the swimlane markup from the response.
(function () {
  "use strict";

  const POLL_INTERVAL_MS = 1000;
  let selectedProject = "ALL";
  let latestState = null;

  function badge(label, extraClass) {
    const span = document.createElement("span");
    span.className = "badge" + (extraClass ? " " + extraClass : "");
    span.textContent = label;
    return span;
  }

  function renderCard(issue) {
    const card = document.createElement("div");
    card.className = "card";
    if (issue.unitId) card.dataset.unitId = issue.unitId;
    if (issue.project) card.dataset.project = issue.project;

    const title = document.createElement("div");
    title.className = "card-title";
    const titleText = document.createElement("span");
    titleText.textContent = issue.issue;
    title.appendChild(titleText);

    if (issue.operatorWaiting) {
      title.appendChild(badge("AWAITING OPERATOR", "waiting"));
    } else if (issue.liveActivity) {
      const isThinking = issue.liveActivity.toLowerCase().indexOf("thinking") !== -1;
      title.appendChild(badge(issue.liveActivity, isThinking ? "waiting" : "live"));
    }
    card.appendChild(title);

    const badgesContainer = document.createElement("div");
    badgesContainer.className = "card-badges";

    if (issue.project) {
      badgesContainer.appendChild(badge(issue.project, "project"));
    }
    if (issue.branch) {
      badgesContainer.appendChild(badge("br: " + issue.branch, "branch"));
    }
    if (issue.worktree) {
      badgesContainer.appendChild(badge("wt: " + issue.worktree, "branch"));
    }
    Object.keys(issue.models || {}).forEach(function (role) {
      badgesContainer.appendChild(badge(role + ": " + issue.models[role], "model"));
    });
    if (issue.correctionBudget) {
      badgesContainer.appendChild(
        badge("corrections: " + issue.correctionBudget.used + "/" + issue.correctionBudget.ceiling, "budget")
      );
    }
    if (typeof issue.elapsedPhaseSeconds === "number") {
      badgesContainer.appendChild(badge(issue.elapsedPhaseSeconds + "s", "elapsed"));
    }

    if (badgesContainer.children.length > 0) {
      card.appendChild(badgesContainer);
    }

    if (issue.operatorWaiting) {
      const actionBar = document.createElement("div");
      actionBar.className = "card-action-bar";
      const approveBtn = document.createElement("button");
      approveBtn.type = "button";
      approveBtn.className = "btn-approve-gate";
      approveBtn.textContent = "Aprovar Gate";
      approveBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        approveGate(issue, approveBtn);
      });
      actionBar.appendChild(approveBtn);
      card.appendChild(actionBar);
    }

    card.addEventListener("click", function () {
      openExecutionModal(issue);
    });

    return card;
  }

  function updateProjectSelect(projects, runs) {
    const select = document.getElementById("project-select");
    if (!select) return;

    const available = [];
    const seen = new Set();

    (projects || []).forEach(function (p) {
      if (!seen.has(p.unitId)) {
        seen.add(p.unitId);
        available.push({ id: p.unitId, name: p.name || p.unitId });
      }
    });

    (runs || []).forEach(function (r) {
      if (!seen.has(r.unitId)) {
        seen.add(r.unitId);
        const repoName = r.repositoryRoot ? r.repositoryRoot.split("/").filter(Boolean).pop() : r.unitId;
        available.push({ id: r.unitId, name: repoName || r.unitId });
      }
    });

    const currentOptions = Array.from(select.options).map(function (o) {
      return o.value;
    });
    const newOptions = ["ALL"].concat(
      available.map(function (a) {
        return a.id;
      })
    );
    const changed =
      currentOptions.length !== newOptions.length ||
      !newOptions.every(function (val, i) {
        return currentOptions[i] === val;
      });

    if (changed) {
      const prevVal = select.value || selectedProject;
      select.innerHTML = "";
      const allOpt = document.createElement("option");
      allOpt.value = "ALL";
      allOpt.textContent = "ALL";
      select.appendChild(allOpt);

      available.forEach(function (proj) {
        const opt = document.createElement("option");
        opt.value = proj.id;
        opt.textContent = proj.name;
        select.appendChild(opt);
      });

      if (newOptions.indexOf(prevVal) !== -1) {
        select.value = prevVal;
        selectedProject = prevVal;
      } else {
        select.value = "ALL";
        selectedProject = "ALL";
      }
    }
  }

  function render(state) {
    latestState = state;
    const root = document.getElementById("swimlanes");
    root.textContent = "";

    updateProjectSelect(state.projects, state.runs);

    if (!state.runs || state.runs.length === 0) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      const title = document.createElement("div");
      title.className = "empty-state-title";
      title.textContent = "NO ACTIVE RUNS DETECTED";
      empty.appendChild(title);
      const desc = document.createElement("p");
      desc.textContent = "No execution units found in ~/.gantry/state.";
      empty.appendChild(desc);
      root.appendChild(empty);
      return;
    }

    const filteredRuns =
      selectedProject === "ALL"
        ? state.runs
        : state.runs.filter(function (run) {
            return run.unitId === selectedProject;
          });

    const section = document.createElement("section");
    const isStale = filteredRuns.some(function (r) {
      return r.stale;
    });
    section.className = "swimlane" + (isStale ? " stale" : "");

    const header = document.createElement("div");
    header.className = "swimlane-header";

    const titleGroup = document.createElement("div");
    titleGroup.className = "swimlane-title-group";

    const heading = document.createElement("h2");
    if (selectedProject === "ALL") {
      heading.textContent = "ALL PROJECTS — UNIFIED KANBAN";
    } else {
      const proj = (state.projects || []).find(function (p) {
        return p.unitId === selectedProject;
      });
      const projName = proj ? proj.name : selectedProject;
      heading.textContent = projName + " — KANBAN";
    }
    titleGroup.appendChild(heading);

    const meta = document.createElement("div");
    meta.className = "swimlane-meta";

    if (selectedProject === "ALL") {
      const uniqueProjects = new Set(
        filteredRuns.map(function (r) {
          return r.unitId;
        })
      );
      meta.appendChild(badge("projects: " + uniqueProjects.size, "tier"));
      meta.appendChild(badge("runs: " + filteredRuns.length, "tier"));
    } else {
      const runTiers = Array.from(
        new Set(
          filteredRuns.map(function (r) {
            return r.tier;
          })
        )
      );
      if (runTiers.length > 0) {
        meta.appendChild(badge("tier: " + runTiers.join(", "), "tier"));
      }
    }

    if (isStale) {
      meta.appendChild(badge("STALE", "stale"));
    } else {
      meta.appendChild(badge("LIVE", "live"));
    }

    header.appendChild(titleGroup);
    header.appendChild(meta);
    section.appendChild(header);

    const columnsEl = document.createElement("div");
    columnsEl.className = "columns";

    const allIssues = [];
    filteredRuns.forEach(function (run) {
      (run.issues || []).forEach(function (issue) {
        allIssues.push(issue);
      });
    });

    state.columns.forEach(function (columnName) {
      const columnEl = document.createElement("div");
      columnEl.className = "column";

      const colHeader = document.createElement("div");
      colHeader.className = "column-header";

      const title = document.createElement("span");
      title.className = "column-title";
      title.textContent = columnName;
      colHeader.appendChild(title);

      const matchingIssues = allIssues.filter(function (issue) {
        return issue.column === columnName;
      });

      const count = document.createElement("span");
      count.className = "column-count";
      count.textContent = matchingIssues.length;
      colHeader.appendChild(count);

      columnEl.appendChild(colHeader);

      const cardsContainer = document.createElement("div");
      cardsContainer.className = "column-cards";
      matchingIssues.forEach(function (issue) {
        cardsContainer.appendChild(renderCard(issue));
      });
      columnEl.appendChild(cardsContainer);

      columnsEl.appendChild(columnEl);
    });

    section.appendChild(columnsEl);
    root.appendChild(section);
  }

  let activeModalIssue = null;
  let modalPollInterval = null;

  function formatDiff(content) {
    const container = document.createElement("div");
    container.className = "diff-record";
    const title = document.createElement("div");
    title.className = "tool-name";
    title.textContent = "CODE CHANGES / DIFF";
    container.appendChild(title);

    const diffEl = document.createElement("pre");
    diffEl.className = "diff-content";
    const lines = (content || "").split("\n");
    lines.forEach(function (line) {
      const lineSpan = document.createElement("span");
      if (line.startsWith("+")) {
        lineSpan.className = "diff-line-add";
      } else if (line.startsWith("-")) {
        lineSpan.className = "diff-line-del";
      } else if (line.startsWith("@@") || line.startsWith("diff") || line.startsWith("index")) {
        lineSpan.className = "diff-line-info";
      }
      lineSpan.textContent = line + "\n";
      diffEl.appendChild(lineSpan);
    });
    container.appendChild(diffEl);
    return container;
  }

  function renderTranscriptSteps(steps, container) {
    container.innerHTML = "";
    if (!steps || steps.length === 0) {
      const empty = document.createElement("div");
      empty.className = "transcript-loading";
      empty.textContent = "No transcript steps recorded yet.";
      container.appendChild(empty);
      return;
    }

    steps.forEach(function (step) {
      // 1. Collapsible thinking block
      if (step.thinking && typeof step.thinking === "string") {
        const block = document.createElement("div");
        block.className = "thinking-block";

        const header = document.createElement("div");
        header.className = "thinking-header";
        const headerText = document.createElement("span");
        headerText.textContent = "MODEL REASONING (THINKING)";
        const toggleText = document.createElement("span");
        toggleText.className = "thinking-toggle";
        toggleText.textContent = "[+] EXPAND";
        header.appendChild(headerText);
        header.appendChild(toggleText);

        const content = document.createElement("div");
        content.className = "thinking-content collapsed";
        content.textContent = step.thinking;

        header.addEventListener("click", function () {
          const isCollapsed = content.classList.contains("collapsed");
          if (isCollapsed) {
            content.classList.remove("collapsed");
            toggleText.textContent = "[-] COLLAPSE";
          } else {
            content.classList.add("collapsed");
            toggleText.textContent = "[+] EXPAND";
          }
        });

        block.appendChild(header);
        block.appendChild(content);
        container.appendChild(block);
      }

      // 2. Tool calls
      if (step.tool_calls && Array.isArray(step.tool_calls)) {
        step.tool_calls.forEach(function (tool) {
          const toolEl = document.createElement("div");
          toolEl.className = "tool-record";

          const nameEl = document.createElement("div");
          nameEl.className = "tool-name";
          nameEl.textContent = "TOOL: " + (tool.name || "unknown");
          toolEl.appendChild(nameEl);

          if (tool.args) {
            const argsEl = document.createElement("pre");
            argsEl.className = "tool-args";
            argsEl.textContent = JSON.stringify(tool.args, null, 2);
            toolEl.appendChild(argsEl);
          }
          container.appendChild(toolEl);
        });
      }

      // 3. Diff or output content
      if (step.content && typeof step.content === "string") {
        if (step.content.includes("diff --git") || step.content.includes("--- a/") || step.content.includes("+added line")) {
          container.appendChild(formatDiff(step.content));
        }
      }
    });
  }

  function approveGate(issue, btnEl, onComplete) {
    if (!issue || !issue.unitId || !issue.run || !issue.issue) return;
    if (btnEl) {
      btnEl.disabled = true;
      btnEl.textContent = "Aprovando...";
    }
    const encodedIssue = encodeURIComponent(issue.issue);
    fetch("/api/runs/" + issue.unitId + "/" + issue.run + "/issues/" + encodedIssue + "/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    })
      .then(function (res) {
        return res.json();
      })
      .then(function (data) {
        if (btnEl) {
          btnEl.textContent = "Aprovado ✓";
          btnEl.classList.add("approved");
        }
        issue.operatorWaiting = false;
        issue.operatorApproved = true;
        const gateAlert = document.getElementById("modal-gate-alert");
        if (gateAlert) {
          gateAlert.className = "gate-alert success";
          const alertText = document.getElementById("modal-gate-alert-text");
          if (alertText) alertText.textContent = "✓ Gate aprovado pelo operador. Iniciando integração...";
        }
        const activityBadge = document.getElementById("modal-activity-badge");
        if (activityBadge) {
          activityBadge.textContent = "GATE APROVADO";
          activityBadge.className = "badge live";
        }
        if (typeof onComplete === "function") {
          onComplete(data);
        }
        poll();
      })
      .catch(function () {
        if (btnEl) {
          btnEl.disabled = false;
          btnEl.textContent = "Erro ao Aprovar";
        }
      });
  }

  function renderGates(gates, container) {
    container.innerHTML = "";
    if (!gates || Object.keys(gates).length === 0) {
      container.innerHTML = '<div class="transcript-loading">Nenhum parecer de gate registrado ainda.</div>';
      return;
    }

    const phases = [
      { key: "plan", label: "Gate 1: Planejamento (Plan)", desc: "Critérios de aceitação e escopo planejado" },
      { key: "implement", label: "Gate 2: Implementação (Implement)", desc: "Provas de TDD e cobertura de testes" },
      { key: "critic", label: "Gate 3: Avaliação Adversarial (Critic)", desc: "Verificação rigorosa de critérios e evidências" },
      { key: "integrate", label: "Gate 4: Integração (Integrate)", desc: "Verificação pós-merge e entrega de código" },
    ];

    phases.forEach(function (phase) {
      const gdata = gates[phase.key];
      const card = document.createElement("div");
      card.className = "gate-card";

      const header = document.createElement("div");
      header.className = "gate-card-header";
      const title = document.createElement("span");
      title.className = "gate-card-title";
      title.textContent = phase.label;
      header.appendChild(title);

      const statusBadge = document.createElement("span");
      if (gdata) {
        const isPassed = gdata.complete === true || gdata.verdict === "accepted" || gdata.verdict === "complete" || gdata.verdict === "tests_passed" || gdata.verdict === "merged";
        statusBadge.className = "badge " + (isPassed ? "live" : "stale");
        statusBadge.textContent = isPassed ? "APROVADO" : "PENDENTE / REFUTADO";
      } else {
        statusBadge.className = "badge";
        statusBadge.textContent = "NÃO INICIADO";
      }
      header.appendChild(statusBadge);
      card.appendChild(header);

      const body = document.createElement("div");
      body.className = "gate-card-body";

      if (!gdata) {
        body.innerHTML = '<div style="color: var(--slate-500); font-style: italic;">Aguardando execução desta fase.</div>';
      } else {
        if (phase.key === "plan") {
          const scopeDiv = document.createElement("div");
          scopeDiv.className = "gate-metric";
          scopeDiv.innerHTML = '<span class="gate-metric-label">Escopo Planejado:</span><span>' + (Array.isArray(gdata.scope) ? gdata.scope.length + " itens" : (gdata.scope || "Definido")) + '</span>';
          body.appendChild(scopeDiv);

          if (gdata.criteria && Array.isArray(gdata.criteria)) {
            const critDiv = document.createElement("div");
            critDiv.innerHTML = '<div class="gate-metric-label">Critérios Avaliados:</div>';
            const list = document.createElement("ul");
            list.className = "gate-checklist";
            gdata.criteria.forEach(function (c) {
              const li = document.createElement("li");
              li.className = "gate-checklist-item";
              li.textContent = "✓ " + (typeof c === "string" ? c : c.text || JSON.stringify(c));
              list.appendChild(li);
            });
            critDiv.appendChild(list);
            body.appendChild(critDiv);
          }
        } else if (phase.key === "implement") {
          const tddDiv = document.createElement("div");
          tddDiv.className = "gate-metric";
          tddDiv.innerHTML = '<span class="gate-metric-label">TDD Proofs:</span><span>' + (gdata.tddProofs ? "Passou (Red-Green Verificado)" : (gdata.verdict || "Concluído")) + '</span>';
          body.appendChild(tddDiv);

          if (gdata.attempt) {
            const attDiv = document.createElement("div");
            attDiv.className = "gate-metric";
            attDiv.innerHTML = '<span class="gate-metric-label">Tentativas:</span><span>' + gdata.attempt + '</span>';
            body.appendChild(attDiv);
          }
        } else if (phase.key === "critic") {
          const compDiv = document.createElement("div");
          compDiv.className = "gate-metric";
          compDiv.innerHTML = '<span class="gate-metric-label">Veredito Adversarial:</span><span>' + (gdata.complete ? "Aprovado (Zero Refutações)" : "Refutado") + '</span>';
          body.appendChild(compDiv);

          if (gdata.evidence && Array.isArray(gdata.evidence) && gdata.evidence.length > 0) {
            const evDiv = document.createElement("div");
            evDiv.innerHTML = '<div class="gate-metric-label">Evidências de Verificação:</div>';
            const list = document.createElement("ul");
            list.className = "gate-checklist";
            gdata.evidence.forEach(function (e) {
              const li = document.createElement("li");
              li.className = "gate-checklist-item";
              li.textContent = "✓ " + (typeof e === "string" ? e : JSON.stringify(e));
              list.appendChild(li);
            });
            evDiv.appendChild(list);
            body.appendChild(evDiv);
          }

          if (gdata.gateFailures && Array.isArray(gdata.gateFailures) && gdata.gateFailures.length > 0) {
            const failDiv = document.createElement("div");
            failDiv.innerHTML = '<div class="gate-metric-label" style="color: var(--red-alert)">Falhas Detectadas:</div>';
            const list = document.createElement("ul");
            list.className = "gate-checklist";
            gdata.gateFailures.forEach(function (f) {
              const li = document.createElement("li");
              li.className = "gate-checklist-item";
              li.style.color = "var(--red-alert)";
              li.textContent = "✗ " + (typeof f === "string" ? f : JSON.stringify(f));
              list.appendChild(li);
            });
            failDiv.appendChild(list);
            body.appendChild(failDiv);
          }
        } else if (phase.key === "integrate") {
          const intDiv = document.createElement("div");
          intDiv.className = "gate-metric";
          intDiv.innerHTML = '<span class="gate-metric-label">Status de Integração:</span><span>' + (gdata.verdict === "merged" ? "Merge Concluído com Sucesso" : (gdata.verdict || "Concluído")) + '</span>';
          body.appendChild(intDiv);
          if (gdata.worktree) {
            const wtDiv = document.createElement("div");
            wtDiv.className = "gate-metric";
            wtDiv.innerHTML = '<span class="gate-metric-label">Worktree:</span><span>' + gdata.worktree + '</span>';
            body.appendChild(wtDiv);
          }
        }
      }

      card.appendChild(body);
      container.appendChild(card);
    });
  }

  function fetchModalGates(issue) {
    if (!issue || !issue.unitId || !issue.run || !issue.issue) return;
    const container = document.getElementById("gates-container");
    if (!container) return;

    const encodedIssue = encodeURIComponent(issue.issue);
    fetch("/api/runs/" + issue.unitId + "/" + issue.run + "/issues/" + encodedIssue + "/gates", { cache: "no-store" })
      .then(function (res) {
        return res.json();
      })
      .then(function (data) {
        if (activeModalIssue && activeModalIssue.issue === issue.issue) {
          renderGates(data.gates || {}, container);
        }
      })
      .catch(function () {
        // Keep existing on error
      });
  }

  function fetchModalTranscript(issue) {
    if (!issue || !issue.unitId || !issue.run || !issue.issue) return;
    const container = document.getElementById("modal-transcript-container");
    if (!container) return;

    const encodedIssue = encodeURIComponent(issue.issue);
    fetch("/api/runs/" + issue.unitId + "/" + issue.run + "/issues/" + encodedIssue + "/transcript", { cache: "no-store" })
      .then(function (res) {
        return res.json();
      })
      .then(function (data) {
        if (activeModalIssue && activeModalIssue.issue === issue.issue) {
          renderTranscriptSteps(data.steps || [], container);
        }
      })
      .catch(function () {
        // Leave previous state on error
      });
  }

  function openExecutionModal(issue) {
    activeModalIssue = issue;
    const modal = document.getElementById("execution-modal");
    if (!modal) return;

    document.getElementById("modal-issue-title").textContent = "ISSUE: " + issue.issue;
    const phaseBadge = document.getElementById("modal-phase-badge");
    phaseBadge.textContent = issue.column;
    phaseBadge.className = "badge tier";

    const activityBadge = document.getElementById("modal-activity-badge");
    if (issue.operatorWaiting) {
      activityBadge.textContent = "AWAITING OPERATOR";
      activityBadge.className = "badge waiting";
      activityBadge.style.display = "inline-flex";
    } else if (issue.liveActivity) {
      activityBadge.textContent = issue.liveActivity;
      activityBadge.className = "badge live";
      activityBadge.style.display = "inline-flex";
    } else {
      activityBadge.style.display = "none";
    }

    document.getElementById("modal-meta-project").textContent = "PROJECT: " + (issue.project || issue.unitId || "-");
    document.getElementById("modal-meta-unit").textContent = "UNIT: " + (issue.unitId || "-");
    document.getElementById("modal-meta-run").textContent = "RUN: " + (issue.run || "-");
    document.getElementById("modal-meta-branch").textContent = "BRANCH: " + (issue.branch || "-");

    // Gate alert strip
    const gateAlert = document.getElementById("modal-gate-alert");
    const modalApproveBtn = document.getElementById("modal-approve-btn");
    if (gateAlert && modalApproveBtn) {
      if (issue.operatorWaiting) {
        gateAlert.className = "gate-alert";
        gateAlert.classList.remove("hidden");
        modalApproveBtn.disabled = false;
        modalApproveBtn.textContent = "Aprovar Gate";
        modalApproveBtn.onclick = function () {
          approveGate(issue, modalApproveBtn);
        };
      } else {
        gateAlert.classList.add("hidden");
      }
    }

    // Default to gates tab
    const tabGates = document.getElementById("tab-btn-gates");
    const tabHistory = document.getElementById("tab-btn-history");
    const paneGates = document.getElementById("tab-content-gates");
    const paneHistory = document.getElementById("tab-content-history");
    if (tabGates && tabHistory && paneGates && paneHistory) {
      tabGates.classList.add("active");
      tabHistory.classList.remove("active");
      paneGates.classList.remove("hidden");
      paneHistory.classList.add("hidden");
    }

    // Popout button
    const popoutBtn = document.getElementById("btn-popout-history");
    if (popoutBtn) {
      popoutBtn.onclick = function () {
        const url = "/history.html?unit=" + encodeURIComponent(issue.unitId) + "&run=" + encodeURIComponent(issue.run) + "&issue=" + encodeURIComponent(issue.issue);
        window.open(url, "_blank");
      };
    }

    const gatesContainer = document.getElementById("gates-container");
    if (gatesContainer) gatesContainer.innerHTML = '<div class="transcript-loading">Carregando pareceres dos gates...</div>';

    const transcriptContainer = document.getElementById("modal-transcript-container");
    if (transcriptContainer) transcriptContainer.innerHTML = '<div class="transcript-loading">Awaiting transcript events...</div>';

    modal.classList.remove("hidden");

    fetchModalGates(issue);
    fetchModalTranscript(issue);
    if (modalPollInterval) clearInterval(modalPollInterval);
    modalPollInterval = setInterval(function () {
      if (activeModalIssue) {
        fetchModalGates(activeModalIssue);
        fetchModalTranscript(activeModalIssue);
      }
    }, POLL_INTERVAL_MS);
  }

  function closeExecutionModal() {
    activeModalIssue = null;
    if (modalPollInterval) {
      clearInterval(modalPollInterval);
      modalPollInterval = null;
    }
    const modal = document.getElementById("execution-modal");
    if (modal) {
      modal.classList.add("hidden");
    }
  }

  function setupEvents() {
    const select = document.getElementById("project-select");
    if (select) {
      select.addEventListener("change", function () {
        selectedProject = this.value;
        if (latestState) {
          render(latestState);
        }
      });
    }

    const closeBtn = document.getElementById("modal-close-btn");
    if (closeBtn) {
      closeBtn.addEventListener("click", closeExecutionModal);
    }

    const modal = document.getElementById("execution-modal");
    if (modal) {
      modal.addEventListener("click", function (e) {
        if (e.target === modal) {
          closeExecutionModal();
        }
      });
    }

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && activeModalIssue) {
        closeExecutionModal();
      }
    });

    const tabGates = document.getElementById("tab-btn-gates");
    const tabHistory = document.getElementById("tab-btn-history");
    const paneGates = document.getElementById("tab-content-gates");
    const paneHistory = document.getElementById("tab-content-history");

    if (tabGates && tabHistory && paneGates && paneHistory) {
      tabGates.addEventListener("click", function () {
        tabGates.classList.add("active");
        tabHistory.classList.remove("active");
        paneGates.classList.remove("hidden");
        paneHistory.classList.add("hidden");
      });

      tabHistory.addEventListener("click", function () {
        tabHistory.classList.add("active");
        tabGates.classList.remove("active");
        paneHistory.classList.remove("hidden");
        paneGates.classList.add("hidden");
      });
    }
  }

  function poll() {
    fetch("/api/state", { cache: "no-store" })
      .then(function (response) {
        return response.json();
      })
      .then(render)
      .catch(function () {
        // A transient fetch failure leaves the previous render in place.
      });
  }

  setupEvents();
  poll();
  setInterval(poll, POLL_INTERVAL_MS);
})();
