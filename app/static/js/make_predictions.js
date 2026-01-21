async function addPrediction(e) {
	try {
		// Get the data
		const metadata = e.target.closest('.cell');

		// Now that we have the specific row, we find the inputs inside ONLY that row
		const category = metadata.dataset.category;
		let count = parseInt(metadata.dataset.count, 10);
		const title = metadata.querySelector('#new_title');
		const description = metadata.querySelector('#new_description');

		if (!title.value.trim()) {
			showNotification('Title missing!', 'is-info');
			return;
		}

		if (count >= 5) {
			showNotification('No more than 5 predictions per category!', 'is-info');
			return;
		}

		const data = { "category": category, "title": title.value, "description": description.value };
		// Submit the data
		const response = await fetch('/api/predictions', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(data)
		});
		const result = await response.json();
		// Process the data
		if (response.ok) {
			addPredictionCard(e, result.id, title.value, description.value);
			title.value = "";
			description.value = "";
			metadata.dataset.count = count + 1;
			metadata.style.setProperty('--count', `'${count + 1}'`);
			showNotification('Prediction saved successfully!', 'is-success');
			// Update your UI count here if needed
		} else {
			showNotification(result.error || 'Something went wrong', 'is-danger');
		}
	} catch (error) {
		showNotification('Network error. Please try again.', 'is-danger');
	}
}

async function removePrediction(e) {
	try {
		// Get the data
		const metadata = e.target.closest('.cell');
		let count = parseInt(metadata.dataset.count, 10);

		const row = e.target.closest('.card');
		const prediction_id = row.id;
		// Submit the data
		const response = await fetch(`/api/predictions/${prediction_id}`, {
			method: 'DELETE',
			headers: { 'Content-Type': 'application/json' }
		});
		const result = await response.json();
		// Process the data
		if (response.ok) {
			row.remove();
			metadata.dataset.count = count - 1;
			metadata.style.setProperty('--count', `'${count - 1}'`);
			showNotification('Prediction removed!', 'is-success');
			// Update your UI count here if needed
		} else {
			showNotification(result.error || 'Something went wrong', 'is-danger');
		}
	} catch (error) {
		showNotification('Network error. Please try again.', 'is-danger');
	}
}

function addPredictionCard(e, id, title, description) {
	const container = e.target.closest('.is-widget-label');

	var htmlString = `
    <div id="${id}" class="card">
      <div class="columns">
	<div class="column is-two-fifths">
	  <p>${title}</p>
	</div>
	<div class="column is-two-fifths">
	  <p>${description}</p>
	</div>
	<div class="column">
	  <div class="control">
	    <button class="button is-danger" onclick="removePrediction(event)">Remove</button>
	  </div>
	</div>
      </div>
    </div>
  `;

	container.insertAdjacentHTML('beforeend', htmlString);
}

async function searchStock(e) {
	const metadata = e.target.closest('.cell');
	const keywords = metadata.querySelector('#search_stock_ticker');
	let count = parseInt(metadata.dataset.count, 10);

	if (!keywords.value.trim()) {
		showNotification('Empty search!', 'is-info');
		return;
	}

	if (count >= 10) {
		showNotification('No more than 10 stockpicks allowed!', 'is-info');
		return;
	}

	const data = { "keywords": keywords.value.trim() };
	// Submit the data
	const response = await fetch('/api/stocks/search', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	});
	const result = await response.json();
	// Process the data
	if (response.ok) {
		console.log(result);
		result.data.forEach((option) => {
			addStockCard(e, option["symbol"], option["name"], option["exchangeFullName"]);
		});
		keywords.value = "";
	}
};

function addStockCard(e, ticker, name, exchange) {
	const container = e.target.closest('.is-widget-label');

	var htmlString = `
    <div id="${ticker}" class="card">
      <div class="columns">
	<div class="column">
	  <p>${ticker}</p>
	</div>
	<div class="column">
	  <p>${name}</p>
	</div>
	<div class="column">
	  <p>${exchange}</p>
	</div>
	<div class="column">
	  <div class="control">
	    <button class="button is-primary" onclick="addStock(event)">Buy</button>
	  </div>
	</div>
      </div>
    </div>
  `;

	container.insertAdjacentHTML('beforeend', htmlString);
}

async function addStock(e) {
	const metadata = e.target.closest('.cell');
	let count = parseInt(metadata.dataset.count, 10);
	const symbol = e.target.closest('.card').id;

	if (count >= 10) {
		showNotification('No more than 10 stockpicks allowed!', 'is-info');
		return;
	}

	// Submit the data
	const response = await fetch('/api/stockpicks', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ "symbol": symbol })
	});
	const result = await response.json();
	// Process the data
	if (response.ok) {
		console.log(result);
		const { id, data } = result;
		const { symbol, name, industry, price } = data;
		console.log(industry);
		console.log(price);
		metadata.dataset.count = count + 1;
		metadata.style.setProperty('--count', `'${count + 1}'`);
		addOwnedStockCard(id, symbol, name, industry, price);
		showNotification('Stock added successfully!', 'is-success');
	}
};

function addOwnedStockCard(id, symbol, name, industry, price) {
	const container = document.getElementById("current_stocks");

	var htmlString = `
    <div id="{{ id }}"class="panel-block is-block">
      <div class="columns">
	<div class="column">
	  <div class="control">
	    <button class="button is-danger" onclick="removeStock(event)">Remove</button>
	  </div>
	</div>
	<div class="column">
	  <p>${symbol}</p>
	</div>
	<div class="column">
	  <p>${name}</p>
	</div>
	<div class="column">
	  <p>${industry}</p>
	</div>
	<div class="column">
	  <p>$ ${price}</p>
	</div>
      </div>
    </div>
  `;
	container.insertAdjacentHTML('beforeend', htmlString);
}

async function removeStock(e) {
	try {
		// Get the data
		const metadata = e.target.closest('.cell');
		let count = parseInt(metadata.dataset.count, 10);

		const row = e.target.closest('.panel-block');
		const prediction_id = row.id;
		// Submit the data
		const response = await fetch(`/api/stockpicks/${prediction_id}`, {
			method: 'DELETE',
			headers: { 'Content-Type': 'application/json' }
		});
		const result = await response.json();
		// Process the data
		if (response.ok) {
			row.remove();
			metadata.dataset.count = count - 1;
			metadata.style.setProperty('--count', `'${count - 1}'`);
			showNotification('Prediction removed!', 'is-success');
			// Update your UI count here if needed
		} else {
			showNotification(result.error || 'Something went wrong', 'is-danger');
		}
	} catch (error) {
		showNotification('Network error. Please try again.', 'is-danger');
	}
}
