const betModal = document.getElementById("betModal");
const conclusionModal = document.getElementById("conclusionModal");

// Open modal and store bet id
document.querySelectorAll(".open-conclusion-modal").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.getElementById("conclusionBetId").value = btn.dataset.betId;
    conclusionModal.classList.add("is-active");
  });
});

// Open modal and store prediction id
document.querySelectorAll(".open-bet-modal").forEach((btn) => {
  btn.addEventListener("click", () => {
    betModal.classList.add("is-active");
  });
});

// Close modal
[
  "closeBetModal",
  "cancelBetModal",
  "closeConclusionModal",
  "cancelConclusionModal",
].forEach((id) => {
  document.getElementById(id).addEventListener("click", () => {
    betModal.classList.remove("is-active");
    conclusionModal.classList.remove("is-active");
  });
});
document.querySelector(".modal-background").addEventListener("click", () => {
  conclusionModal.classList.remove("is-active");
  betModal.classList.remove("is-active");
});

// Submit
document.getElementById("submitBet").addEventListener("click", async () => {
  const title = document.getElementById("betTitle").value.trim();
  const description = document.getElementById("betDescription").value;
  const days = parseInt(document.getElementById("openDays").value) || 0;
  const hours = parseInt(document.getElementById("openHours").value) || 0;
  const minutes = parseInt(document.getElementById("openMinutes").value) || 0;

  if (!title) {
    showNotification("Description is required", "is-info");
    return;
  }

  const response = await fetch("/api/bets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      description,
      days,
      hours,
      minutes,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    showNotification(data.error || "Something went wrong.", "is-danger");
    return;
  } else {
    showNotification("Bet successfully submitted!", "is-success");
  }

  modal.classList.remove("is-active");
});

// Submit
document
  .getElementById("submitConclusion")
  .addEventListener("click", async () => {
    const bet_id = document.getElementById("conclusionBetId").value.trim();
    const outcome = document.getElementById("conclusionOutcome").value.trim();
    const description = document
      .getElementById("conclusionDescription")
      .value.trim();
    const url = document.getElementById("conclusionUrl").value.trim();

    if (!description) {
      showNotification("Description is required", "is-info");
      return;
    }

    const response = await fetch("/api/bet-conclusion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bet_id, outcome, description, url: url || null }),
    });

    const data = await response.json();

    if (!response.ok) {
      showNotification(data.error || "Something went wrong.", "is-danger");
      return;
    } else {
      showNotification("Bet conclusion successfully submitted!", "is-success");
    }

    modal.classList.remove("is-active");
  });

document.querySelectorAll(".bet-vote-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const bet_id = btn.dataset.conclusionId;
    const vote_id = btn.dataset.voteId;
    const vote = btn.dataset.vote === "true";
    const isUpdate = vote_id !== "";

    const siblings = document.querySelectorAll(
      `[data-conclusion-id="${bet_id}"]`,
    );
    siblings.forEach((b) => (b.disabled = true));

    const response = await fetch(
      isUpdate ? `/api/bet/vote/${vote_id}` : "/api/bet/vote",
      {
        method: isUpdate ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(isUpdate ? { vote } : { bet_id: bet_id, vote }),
      },
    );

    const data = await response.json();

    if (!response.ok) {
      siblings.forEach((b) => (b.disabled = false));
      alert(data.error || "Something went wrong.");
      return;
    }

    console.log(data);

    const successProgress = document.getElementById(`${bet_id}-success`);
    const failureProgress = document.getElementById(`${bet_id}-failure`);

    if (vote == true) {
      const successCount = parseInt(successProgress.value) + 1;
      const failureCount = parseInt(failureProgress.value) - 1;
      successProgress.value = successCount;
      failureProgress.value = failureCount;
    } else {
      const successCount = parseInt(successProgress.value) - 1;
      const failureCount = parseInt(failureProgress.value) + 1;
      successProgress.value = successCount;
      failureProgress.value = failureCount;
    }

    // Update vote_id on both buttons so future clicks know to PATCH
    siblings.forEach((b) => {
      b.dataset.voteId = data.id;
      b.disabled = false;
      b.classList.remove("is-primary", "is-danger");
      b.classList.add("is-light");
    });
    btn.classList.remove("is-light");
    btn.classList.add(vote ? "is-primary" : "is-danger");
  });
});
