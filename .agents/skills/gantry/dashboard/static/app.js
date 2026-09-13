// Read-only Gantry dashboard renderer. This file makes no request that can mutate
// state: it only polls GET /api/state and rebuilds the swimlane markup from the response.
(function () {
  "use strict";

  const POLL_INTERVAL_MS = 1000;

  function badge(label, extraClass) {
    const span = document.createElement("span");
    span.className = "badge" + (extraClass ? " " + extraClass : "");
    span.textContent = label;
    return span;
  }

  function renderCard(issue) {
    const card = document.createElement("div");
    card.className = "card";

    const title = document.createElement("strong");
    title.textContent = issue.issue;
    card.appendChild(title);
    card.appendChild(document.createElement("br"));

    if (issue.branch) card.appendChild(badge("branch: " + issue.branch));
    if (issue.worktree) card.appendChild(badge("worktree: " + issue.worktree));
    Object.keys(issue.models || {}).forEach(function (role) {
      card.appendChild(badge(role + ": " + issue.models[role]));
    });
    if (issue.correctionBudget) {
      card.appendChild(
        badge("corrections: " + issue.correctionBudget.used + "/" + issue.correctionBudget.ceiling)
      );
    }
    if (typeof issue.elapsedPhaseSeconds === "number") {
      card.appendChild(badge("elapsed: " + issue.elapsedPhaseSeconds + "s"));
    }
    if (issue.operatorWaiting) {
      card.appendChild(badge("awaiting operator", "waiting"));
    }
    return card;
  }

  function renderRun(run, columns) {
    const section = document.createElement("section");
    section.className = "swimlane" + (run.stale ? " stale" : "");

    const heading = document.createElement("h2");
    heading.textContent =
      run.repositoryRoot + " — " + run.run + (run.stale ? " (stale)" : "") + " [tier: " + run.tier + "]";
    section.appendChild(heading);

    const columnsEl = document.createElement("div");
    columnsEl.className = "columns";

    columns.forEach(function (columnName) {
      const columnEl = document.createElement("div");
      columnEl.className = "column";
      const title = document.createElement("h3");
      title.textContent = columnName;
      columnEl.appendChild(title);
      run.issues
        .filter(function (issue) {
          return issue.column === columnName;
        })
        .forEach(function (issue) {
          columnEl.appendChild(renderCard(issue));
        });
      columnsEl.appendChild(columnEl);
    });

    section.appendChild(columnsEl);
    return section;
  }

  function render(state) {
    const root = document.getElementById("swimlanes");
    root.textContent = "";
    state.runs.forEach(function (run) {
      root.appendChild(renderRun(run, state.columns));
    });
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

  poll();
  setInterval(poll, POLL_INTERVAL_MS);
})();
