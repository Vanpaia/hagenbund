const socket = io();

socket.on("achievement_unlocked", function(data) {
	showNotification(data.message, "is-warning");
});

function showNotification(message, type = "is-info") {
	const container = document.getElementById("notification-container");

	// Create notification element
	const notification = document.createElement("div");
	notification.className = `notification ${type} is-light shadow-sm`;

	// Add some styling for a nice entrance
	// TODO at to css file
	notification.style.marginBottom = "10px";
	notification.style.boxShadow = "0 4px 6px rgba(0,0,0,0.1)";

	notification.innerHTML = `
	    <button class="delete"></button>
	    ${message}
	`;

	container.appendChild(notification);

	// Setup the functionality
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
