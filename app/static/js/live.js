var pause = false;
var start = false;
var current_round = {};
var last_round = {};
var user_id;
var user_name;

socket.emit("game_connect");

socket.on("player_update", function(data) {
  console.log(data);
  const player_list = document.getElementById("player-list");
  player_list.innerHTML = "";

  for (let i = 0; i < data.length; i++) {
    let item = document.createElement("li");
    item.textContent = data[i][1];
    player_list.appendChild(item);
  }
});

socket.on("player_info", function(user) {
  console.log(user);
  user_id = user.id;
  user_name = user.name;
});

socket.on("timer_status_update", function(data) {
  pause = data.is_paused;
  updateTimerUI(data.remaining_ms);
  console.log("Time received:", data.remaining_ms);
  console.log("Paused:", data.is_paused);
});

socket.on("end_round", function(data) {
  socket.emit("submit_prediction_vote", {
    vote: slider.value,
    id: data.id,
    name: user_name,
    round: data.round,
  });
});

socket.on("end_game", function(gameStats) {
  var gameCard = document.getElementById("game-card");
  gameOverState = `
              <h2 class="subtitle is-spaced">
                Game Over!
              </h2>
              <div class="card">
                <div id="game-stats"class="card-content has-text-centered">
                  <h2 class="subtitle is-spaced">
                    Game Stats
                  </h2>
                  <ul>
                    <li>
                      Highest scoring round: ${gameStats.game_stats.highest_round}
                    </li>
                    <li>
                      Quickest round: ${gameStats.game_stats.quickest_round}
                    </li>
                    <li>
                      Highest average score: ${gameStats.game_stats.highest_score.map(p => p.name).join(", ")} 
                      (${gameStats.game_stats.highest_score[0].value})
                    </li>
                    <li>
                      Lowest average score: ${gameStats.game_stats.lowest_score.map(p => p.name).join(", ")} 
                      (${gameStats.game_stats.lowest_score[0].value})
                    </li>
                    <li>
                      Highest average speed: ${gameStats.game_stats.highest_speed.map(p => p.name).join(", ")} 
                      (${(gameStats.game_stats.highest_speed[0].value / 1000).toFixed(2)}s)
                    </li>
                    <li>
                      Lowest average speed: ${gameStats.game_stats.lowest_speed.map(p => p.name).join(", ")} 
                      (${(gameStats.game_stats.lowest_speed[0].value / 1000).toFixed(2)}s)
                    </li>
                    <li>
                      Quickest player: ${gameStats.game_stats.quickest_player.map(p => p.name).join(", ")} 
                      (${(gameStats.game_stats.quickest_player[0].value / 1000).toFixed(2)}s)
                    </li>
                  </ul>
                </div>
              </div>`;
  Object.values(gameStats.player_stats).forEach(stats => {
    gameOverState += `
              <div class="card">
                <div id="game-stats"class="card-content has-text-centered">
                  <h2 class="subtitle is-spaced">
                    ${stats.name}
                  </h2>
                  <ul>
                    <li>
                      Highest risk assessment: ${Math.max(...stats.votes)}%
                    </li>
                    <li>
                      Lowest risk assessment: ${Math.min(...stats.votes)}%
                    </li>
                    <li>
                      Average risk assessment: ${stats.average_score.toFixed(2)}%
                    </li>
                    <li>
                      Weighted points: ${stats.weighted_score.toFixed(2)}
                    </li>
                    <li>
                      Average speed: ${(stats.avg_speed / 1000).toFixed(2)} sec
                    </li>
                    <li>
                      Quickest speed: ${(Math.min(...stats.speeds) / 1000).toFixed(2)} sec
                    </li>
                  </ul>
                </div>
              </div>`;
  });

  gameCard.innerHTML = gameOverState;
  console.log(gameStats);
});

socket.on("clear_game", function() {
  var gameCard = document.getElementById("game-card");
  gameOverState = `
              <div class="is-widget-icon">
                <span class="icon has-text-primary is-large">
                  <span id="category-icon" class="material-symbols-outlined" style="font-size: 48px;">
                    hourglass
                  </span>
                </span>
              </div>
              <h2 id="prediction-card-title" class="subtitle is-spaced">
                Waiting for game to start...
              </h2>
              <p id="prediction-author" class="has-text-justified">
              </p>`;
  gameCard.innerHTML = gameOverState;
});

socket.on("game_status_update", function(data) {
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
    name: user_name,
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
    pauseButton.innerHTML = pause ? unpauseState : pauseState;
  }
}

function updateStateUI(round, total, length, data) {
  var roundCount = document.getElementById("round_count");
  var roundTotal = document.getElementById("total_rounds");
  var roundLengthInput = document.getElementById("roundLengthInput");
  var playerAmountInput = document.getElementById("playerAmountInput");
  var roundTitle = document.getElementById("prediction-card-title");
  var roundDescription = document.getElementById("prediction-author");
  var timerCount = document.getElementById("timer_count");
  var rangeButton = document.getElementById("range_button");
  var timerBar = document.getElementById("timer_bar");
  var categoryIcon = document.getElementById('category-icon');

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
    roundDescription.textContent = data.author;
    if (data.category == "World Politics") {
      categoryIcon.innerText = 'globe';
    } else if (data.category == "European Union") {
      categoryIcon.innerText = 'euro_symbol';
    } else if (data.category == "Entertainment/Sport") {
      categoryIcon.innerText = 'sports_and_outdoors';
    } else if (data.category == "Science/Technology") {
      categoryIcon.innerText = 'experiment';
    } else if (data.category == "Economy/Business") {
      categoryIcon.innerText = 'finance_mode';
    } else {
      categoryIcon.innerText = 'hourglass';
    }

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
