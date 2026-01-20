var pause = false;
var start = false;

socket.on("player_update", function (data) {
  console.log(data.player);
  const player_list = document.getElementById("player-list");
  player_list.innerHTML = "";

  for (let i = 0; i < data.player.length; i++) {
    let item = document.createElement("li");
    item.textContent = data.player[i];
    player_list.appendChild(item);
  }
});

socket.on("timer_status_update", function (data) {
  pause = data.is_paused;
  start = data.is_active;
  updateTimerUI(data.remaining_ms);
  console.log("Time received:", data.remaining_ms);
  console.log("Paused:", data.is_paused);
});

socket.on("game_status_update", function (data) {
  pause = data.is_paused;
  start = data.is_active;
  updateTimerUI(data.remaining_ms);
  updateStateUI(data.current_round, data.round_data);
  console.log("Time received:", data.remaining_ms);
  console.log("Round:", data.current_round);
  console.log("Active:", data.is_active);
  console.log("Paused:", data.is_paused);
  console.log("Data:", data.round_data);
});

function sendMessage() {
  var message_input = document.getElementById("message_input");
  socket.emit("my broadcast event", { data: message_input.value });
  message_input.value = "";
}

const slider = document.getElementById("sliderInput");
const output = document.getElementById("sliderValue");

slider.addEventListener("input", () => {
  output.textContent = slider.value;
});

function submitVote() {
  console.log(slider.value);
  socket.emit("submit_prediction_vote", { data: slider.value });
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
  activeButton.textContent = start ? "STOP" : "START";
  const pauseButton = document.getElementById("timerButton");
  pauseButton.textContent = pause ? "UNPAUSE" : "PAUSE";
}

function updateStateUI(round, data) {
  var roundCount = document.getElementById("round_count");
  var roundTitle = document.getElementById("prediction-card-title");
  var roundDescription = document.getElementById("prediction-card-description");

  roundCount.textContent = round.toString();
  roundTitle.textContent = data.title;
  roundDescription.textContent = data.description;
}

function toggleActive() {
  if (!start) {
    socket.emit("start_game");
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
