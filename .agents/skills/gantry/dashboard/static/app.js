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

  function renderRun(run, columns) {
    const section = document.createElement("section");
    section.className = "swimlane" + (run.stale ? " stale" : "");

    const header = document.createElement("div");
    header.className = "swimlane-header";

    const titleGroup = document.createElement("div");
    titleGroup.className = "swimlane-title-group";

    const heading = document.createElement("h2");
    heading.textContent = run.repositoryRoot + " — " + run.run;
    titleGroup.appendChild(heading);

    const meta = document.createElement("div");
    meta.className = "swimlane-meta";

    meta.appendChild(badge("tier: " + run.tier, "tier"));

    if (run.stale) {
      meta.appendChild(badge("STALE", "stale"));
    } else {
      meta.appendChild(badge("LIVE", "live"));
    }

    if (run.compactionAt) {
      meta.appendChild(badge("compacted: " + run.compactionAt, "compaction"));
    }

    header.appendChild(titleGroup);
    header.appendChild(meta);
    section.appendChild(header);

    const columnsEl = document.createElement("div");
    columnsEl.className = "columns";

    columns.forEach(function (columnName) {
      const columnEl = document.createElement("div");
      columnEl.className = "column";

      const colHeader = document.createElement("div");
      colHeader.className = "column-header";

      const title = document.createElement("span");
      title.className = "column-title";
      title.textContent = columnName;
      colHeader.appendChild(title);

      const matchingIssues = run.issues.filter(function (issue) {
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
    return section;
  }

  function render(state) {
    const root = document.getElementById("swimlanes");
    root.textContent = "";

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
