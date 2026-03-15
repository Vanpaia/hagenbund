const modal = document.getElementById('conclusionModal');

// Open modal and store prediction id
document.querySelectorAll('.open-conclusion-modal').forEach(btn => {
	btn.addEventListener('click', () => {
		document.getElementById('conclusionPredictionId').value = btn.dataset.predictionId;
		modal.classList.add('is-active');
	});
});

// Close modal
['closeModal', 'cancelModal'].forEach(id => {
	document.getElementById(id).addEventListener('click', () => {
		modal.classList.remove('is-active');
	});
});
document.querySelector('.modal-background').addEventListener('click', () => {
	modal.classList.remove('is-active');
});

// Submit
document.getElementById('submitConclusion').addEventListener('click', async () => {
	const description = document.getElementById('conclusionDescription').value.trim();
	const outcome = document.getElementById('conclusionOutcome').value;
	const url = document.getElementById('conclusionUrl').value.trim();
	const prediction_id = document.getElementById('conclusionPredictionId').value;

	if (!description) {
		showNotification('Description is required', "is-info");
		return;
	}

	const response = await fetch('/api/conclusion', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ prediction_id, description, outcome, url: url || null })
	});

	const data = await response.json();

	if (!response.ok) {
		showNotification(data.error || 'Something went wrong.', "is-danger");
		return;
	} else {
		showNotification("Prediction conclusion successfully submitted!", "is-success");
	}

	modal.classList.remove('is-active');
});
