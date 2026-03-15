document.querySelectorAll('.vote-btn').forEach(btn => {
	btn.addEventListener('click', async () => {
		const conclusion_id = btn.dataset.conclusionId;
		const vote_id = btn.dataset.voteId;
		const vote = btn.dataset.vote === 'true';
		const isUpdate = vote_id !== '';

		const siblings = document.querySelectorAll(`[data-conclusion-id="${conclusion_id}"]`);
		siblings.forEach(b => b.disabled = true);

		const response = await fetch(
			isUpdate ? `/api/conclusion/vote/${vote_id}` : '/api/conclusion/vote',
			{
				method: isUpdate ? 'PATCH' : 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(isUpdate ? { vote } : { prediction_conclusion_id: conclusion_id, vote })
			}
		);

		const data = await response.json();

		if (!response.ok) {
			siblings.forEach(b => b.disabled = false);
			alert(data.error || 'Something went wrong.');
			return;
		}

		console.log(data);
		if (data.data.status !== "active") {
			const card = document.getElementById(conclusion_id);
			card.remove()
		}

		const successProgress = document.getElementById(`${conclusion_id}-success`);
		const failureProgress = document.getElementById(`${conclusion_id}-failure`);

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
		siblings.forEach(b => {
			b.dataset.voteId = data.id;
			b.disabled = false;
			b.classList.remove('is-primary', 'is-danger');
			b.classList.add('is-light');
		});
		btn.classList.remove('is-light');
		btn.classList.add(vote ? 'is-primary' : 'is-danger');
	});
});

