// This listens for the 'my response' event you defined in Python
socket.on("chat_broadcast", function (msg) {
  console.log("Message received from server:", msg.data);

  // Optional: Append to the page so you don't just rely on the console
  let item = document.createElement("li");
  item.textContent = msg.data;
  document.getElementById("messages").appendChild(item);
});

socket.on("user_list", function (data) {
  console.log(data);
  const player_list = document.getElementById("player-list");
  player_list.innerHTML = "";

  for (let i = 0; i < data.length; i++) {
    let item = document.createElement("li");
    item.textContent = data[i];
    player_list.appendChild(item);
  }
});

function sendMessage() {
  var message_input = document.getElementById("message_input");
  socket.emit("chat_message", { data: message_input.value });
  message_input.value = "";
}
