var pause = false;
var start = false;
var current_round = {};
var last_round = {};
var user_id;

socket.emit("game_connect");

socket.on("player_update", function (data) {
  console.log(data);
  const player_list = document.getElementById("player-list");
  player_list.innerHTML = "";

  for (let i = 0; i < data.length; i++) {
    let item = document.createElement("li");
    item.textContent = data[i][1];
    player_list.appendChild(item);
  }
});

socket.on("player_info", function (id) {
  console.log(id);
  user_id = id;
});

socket.on("timer_status_update", function (data) {
  pause = data.is_paused;
  updateTimerUI(data.remaining_ms);
  console.log("Time received:", data.remaining_ms);
  console.log("Paused:", data.is_paused);
});

socket.on("end_round", function (data) {
  socket.emit("submit_prediction_vote", {
    vote: slider.value,
    id: data.id,
    round: data.round,
  });
});

socket.on("end_game", function () {
  var gameCard = document.getElementById("game-card");
  gameOverState = `
              <h2 class="subtitle is-spaced">
                Game Over!
              </h2>`;
  gameCard.innerHTML = gameOverState;
});

socket.on("clear_game", function () {
  var gameCard = document.getElementById("game-card");
  gameOverState = `
              <h2 id="prediction-card-title" class="subtitle is-spaced">
                Waiting for game to start...
              </h2>
              <p id="prediction-card-description" class="has-text-justified">
              </p>`;
  gameCard.innerHTML = gameOverState;
});

socket.on("game_status_update", function (data) {
  pause = data.is_paused;
  start = data.is_active;
  updateTimerUI(data.remaining_ms);
  updateStateUI(
    data.current_round,
    data.total_rounds,
    data.round_length,
    data.round_data,
  );
  current_round["data"] = data.round_data;
  current_round["round"] = data.current_round;
  console.log("Time received:", data.remaining_ms);
  console.log("Round:", data.current_round);
  console.log("Active:", data.is_active);
  console.log("Paused:", data.is_paused);
  console.log("Data:", data.round_data);
});

const slider = document.getElementById("sliderInput");
const output = document.getElementById("sliderValue");

slider.addEventListener("input", () => {
  output.textContent = slider.value;
});

function submitVote() {
  console.log(slider.value);
  socket.emit("submit_prediction_vote", {
    vote: slider.value,
    id: current_round["data"]["id"],
    round: current_round["round"],
  });
  slider.value = 50;
  output.textContent = slider.value;
}

function updateTimerUI(value) {
  var timerBar = document.getElementById("timer_bar");
  var timerCount = document.getElementById("timer_count");

  if (!start) {
    timerBar.classList.replace("is-primary", "is-danger");
    timerBar.classList.replace("is-warning", "is-danger");
  } else {
    timerBar.classList.replace("is-danger", "is-primary");
  }
  if (pause) {
    timerBar.classList.replace("is-primary", "is-warning");
  } else {
    timerBar.classList.replace("is-warning", "is-primary");
  }

  var timerSeconds = Math.floor(value / 1000);
  timerBar.value = timerSeconds;
  timerCount.textContent = timerSeconds.toString();

  const activeButton = document.getElementById("startStopButton");
  const pauseButton = document.getElementById("timerButton");
  const startState = `
              <span class="icon has-text-white is-large">
                <span class="material-symbols-outlined" style="font-size: 48px;">
                  play_arrow
                </span>
              </span>`;
  const stopState = `
              <span class="icon has-text-white is-large">
                <span class="material-symbols-outlined" style="font-size: 48px;">
                  stop
                </span>
              </span>`;
  const pauseState = `
              <span class="icon has-text-white is-large">
                <span class="material-symbols-outlined" style="font-size: 48px;">
                  pause
                </span>
              </span>`;
  const unpauseState = `
              <span class="icon has-text-white is-large">
                <span class="material-symbols-outlined" style="font-size: 48px;">
                  resume
                </span>
              </span>`;

  if (activeButton && pauseButton) {
    activeButton.innerHTML = start ? stopState : startState;
    pauseButton.innerHTML = pause ? pauseState : unpauseState;
  }
}

function updateStateUI(round, total, length, data) {
  var roundCount = document.getElementById("round_count");
  var roundTotal = document.getElementById("total_rounds");
  var roundLengthInput = document.getElementById("roundLengthInput");
  var playerAmountInput = document.getElementById("playerAmountInput");
  var roundTitle = document.getElementById("prediction-card-title");
  var roundDescription = document.getElementById("prediction-card-description");
  var timerCount = document.getElementById("timer_count");
  var rangeButton = document.getElementById("range_button");
  var timerBar = document.getElementById("timer_bar");

  if (!start) {
    if (roundLengthInput && playerAmountInput) {
      roundLengthInput.classList.remove("is-hidden");
      playerAmountInput.classList.remove("is-hidden");
    }
    timerCount.textContent = "X";
    roundCount.textContent = "X";
    roundTotal.textContent = "X";
    roundTitle.textContent = "Waiting for game to start...";
    roundDescription.textContent = "";
    rangeButton.disabled = true;
  } else {
    if (roundLengthInput && playerAmountInput) {
      roundLengthInput.classList.add("is-hidden");
      playerAmountInput.classList.add("is-hidden");
    }
    roundCount.textContent = round.toString();
    roundTotal.textContent = total.toString();
    roundTitle.textContent = data.title;
    roundDescription.textContent = data.description;
    rangeButton.removeAttribute("disabled");
    var timerSeconds = Math.floor(length / 1000);
    timerBar.max = timerSeconds;
  }

  if (user_id == data.user_id) {
    rangeButton.disabled = true;
  }
}

function toggleActive() {
  if (!start) {
    var roundLengthInput = document.getElementById("roundLengthInput");
    var playerAmountInput = document.getElementById("playerAmountInput");
    var lengthInput = roundLengthInput.value;
    var playerAmount = playerAmountInput.value;
    var game_config = { data: { length: lengthInput, player: playerAmount } };
    console.log(game_config);
    socket.emit("start_game", game_config);
  } else {
    socket.emit("stop_game");
  }
}

function toggleTimer() {
  if (start) {
    socket.emit("toggle_pause");
  }
}

function nextRound() {
  socket.emit("next_round");
}

function previousRound() {
  socket.emit("previous_round");
}

function saveGame() {
  socket.emit("save_game");
}
