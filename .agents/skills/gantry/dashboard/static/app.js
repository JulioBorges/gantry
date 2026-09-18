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
