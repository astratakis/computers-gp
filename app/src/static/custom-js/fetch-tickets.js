document.addEventListener("DOMContentLoaded", () => {
  const ticketsBody = document.getElementById("ticketsBody");
  const totalTicketsEl = document.getElementById("totalTickets");
  const rangeStartEl = document.getElementById("rangeStart");
  const rangeEndEl = document.getElementById("rangeEnd");

  const chkOpen = document.getElementById("chkOpen");
  const chkClosed = document.getElementById("chkClosed");
  const chkInProgress = document.getElementById("chkInProgress");
  const chkAwaiting = document.getElementById("chkAwaiting");

  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");
  const prevPage = document.getElementById("prevPage");
  const nextPage = document.getElementById("nextPage");

  let offset = 0;
  const limit = 10;

  // Fetch tickets from your API
  async function fetchTickets() {
    try {
      // Build query parameters
      const params = new URLSearchParams();
      params.append("offset", offset);
      params.append("limit", limit);

      if (chkOpen.checked) {
        params.append("status", "open");
      }
      if (chkClosed.checked) {
        params.append("status", "closed");
      }
      if (chkInProgress.checked) {
        params.append("status", "in-progress");
      }
      if (chkAwaiting.checked) {
        params.append("status", "awaiting");
      }

      const response = await fetch(`/api/v1/tickets/?${params.toString()}`);
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await response.json();

      const tickets = data.result.tickets;
      const total = data.result.count;

      // Clear the table first
      ticketsBody.innerHTML = "";

      // Populate the table
      tickets.forEach((ticket) => {
        let priorityMarkup;
        switch (ticket.priority) {
          case "1":
            // Very High => red
            priorityMarkup = `<span class="bg-transparent text-red fw-bold">Very High</span>`;
            break;
          case "2":
            // High => a lighter red or orange
            priorityMarkup = `<span class="bg-transparent text-orange fw-bold">High</span>`;
            break;
          case "3":
            // Normal => plain (white badge with dark text)
            priorityMarkup = `<span class="bg-transparent fw-bold">Normal</span>`;
            break;
          case "4":
            // Low => blue
            priorityMarkup = `<span class="bg-transparent text-azure fw-bold">Low</span>`;
            break;
          default:
            // Fallback if unexpected priority value
            priorityMarkup = `<span class="badge bg-secondary">Unknown</span>`;
        }

        // Status label + color
        let statusMarkup;
        switch (ticket.status) {
          case "open":
            // Purple
            statusMarkup = `<span class="badge text-white bg-purple">Open</span>`;
            break;
          case "in-progress":
            // Brown
            statusMarkup = `<span class="badge text-white bg-blue">In Progress</span>`;
            break;
          case "awaiting":
            // Light blue
            statusMarkup = `<span class="badge text-white bg-teal">Awaiting Reply</span>`;
            break;
          case "closed":
            // Green
            statusMarkup = `<span class="badge text-white bg-red">Closed</span>`;
            break;
          default:
            // Fallback
            statusMarkup = `<span class="badge bg-secondary">Unknown</span>`;
        }

        // Build the row
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${ticket.id}</td>
          <!-- Title links to /tickets/<ticket.id> -->
          <td><a class="text-reset" href="/tickets/${ticket.id}">${ticket.title}</a></td>
          <td>${ticket.created_at}</td>
          <td>${priorityMarkup}</td>
          <td>${statusMarkup}</td>
          `;
        ticketsBody.appendChild(row);
      });

      // Update pagination text
      totalTicketsEl.textContent = total;
      if (tickets.length > 0) {
        rangeStartEl.textContent = offset + 1;
        rangeEndEl.textContent = offset + tickets.length;
      } else {
        // If no tickets returned, show 0
        rangeStartEl.textContent = 0;
        rangeEndEl.textContent = 0;
      }

      // Enable/disable pagination buttons
      // If offset=0, disable the "Prev" button
      if (offset === 0) {
        prevPage.classList.add("disabled");
      } else {
        prevPage.classList.remove("disabled");
      }
      // If offset+limit >= total, disable the "Next" button
      if (total < limit) {
        nextPage.classList.add("disabled");
      } else {
        nextPage.classList.remove("disabled");
      }
    } catch (error) {
      console.error("Error fetching tickets:", error);
    }
  }

  // Event listeners for checkboxes => reload tickets
  [chkOpen, chkClosed, chkInProgress, chkAwaiting].forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      offset = 0; // reset back to first page whenever filters change
      fetchTickets();
    });
  });

  // Pagination controls
  prevBtn.addEventListener("click", (event) => {
    event.preventDefault();
    if (offset >= limit) {
      offset -= limit;
      fetchTickets();
    }
  });

  nextBtn.addEventListener("click", (event) => {
    event.preventDefault();
    // We'll let fetchTickets check if it exceeds total
    offset += limit;
    fetchTickets();
  });

  // Initial fetch
  fetchTickets();
});
