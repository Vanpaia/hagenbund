const socket = io();

socket.on("achievement_unlocked", function (data) {
  message = `
		<strong>${data.title}</strong>
		<p>${data.description}</p>
		`;
  showNotification(
    (message = message),
    (type = "is-warning"),
    (imageUrl = data.image),
  );
});

function showNotification(message, type = "is-info", imageUrl = null) {
  const container = document.getElementById("notification-container");

  const notification = document.createElement("div");
  notification.className = `notification ${type} is-light shadow-sm`;
  notification.style.marginBottom = "10px";
  notification.style.boxShadow = "0 4px 6px rgba(0,0,0,0.1)";

  // Create a Flexbox wrapper to hold the Image and the Text
  const flexWrapper = document.createElement("div");
  flexWrapper.style.display = "flex";
  flexWrapper.style.alignItems = "center"; // Centers vertically

  // 1. Only add the image if a URL is provided
  if (imageUrl) {
    const img = document.createElement("img");
    img.src = `/static/${imageUrl}`;
    img.style.width = "128px";
    img.style.height = "128px";
    img.style.marginRight = "15px";
    img.style.borderRadius = "5px"; // Optional: makes it look nicer
    flexWrapper.appendChild(img);
  }

  // 2. Add the message container
  const messageDiv = document.createElement("div");
  messageDiv.innerHTML = message;
  flexWrapper.appendChild(messageDiv);

  // 3. Assemble the notification
  const deleteBtn = document.createElement("button");
  deleteBtn.className = "delete";

  notification.appendChild(deleteBtn);
  notification.appendChild(flexWrapper);

  container.appendChild(notification);

  setupNotificationLogic(notification);
}

// Helper function close and timeout toasts
function setupNotificationLogic(notification, timeout = 4000) {
  const deleteBtn = notification.querySelector(".delete");
  if (deleteBtn) {
    deleteBtn.onclick = () => notification.remove();
  }

  setTimeout(() => {
    if (notification.parentNode) {
      notification.remove();
    }
  }, timeout);
}

document.addEventListener("DOMContentLoaded", () => {
  const existingNotifications = document.querySelectorAll(".notification");
  existingNotifications.forEach((notification) => {
    setupNotificationLogic(notification);
  });
});
