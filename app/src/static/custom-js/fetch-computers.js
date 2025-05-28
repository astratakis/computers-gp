document.addEventListener("DOMContentLoaded", function () {
  let offset = 0;
  const limit = 10;
  let isSearching = false;
  let totalComputers = 0;
  let searchQuery = "";

  // Element references
  const tableBody = document.querySelector("tbody");
  const pageNumbers = document.querySelector(".pagination");
  const showingInfo = document.querySelector(".card-footer p");
  const searchInput = document.getElementById("searchInput");

  // Button references (used for initial button styling)
  const prevButton = document.querySelector(".page-item:first-child a");
  const nextButton = document.querySelector(".page-item:last-child a");

  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function highlightMatch(text, query) {
    if (!query) return text;
    let regex;
    const macRegex = /^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$/;
    if (macRegex.test(text) && !query.includes(":")) {
      const escapedQuery = query.split("").map(escapeRegExp).join(":?");
      regex = new RegExp(escapedQuery, "gi");
    } else {
      regex = new RegExp(escapeRegExp(query), "gi");
    }
    const highlightColor =
      localStorage.getItem("tablerTheme") === "dark"
        ? getComputedStyle(document.documentElement)
            .getPropertyValue("--tblr-orange")
            .trim()
        : getComputedStyle(document.documentElement)
            .getPropertyValue("--tblr-yellow")
            .trim();

    if (localStorage.getItem("tablerTheme") === "dark") {
      return String(text).replace(
        regex,
        (match) => `<span style="color: ${highlightColor};">${match}</span>`
      );
    } else {
      return String(text).replace(
        regex,
        (match) =>
          `<span style="background-color: ${highlightColor};">${match}</span>`
      );
    }
  }

  async function fetchTotalCount() {
    const url = isSearching
      ? `/api/v1/computers/generic/count?search=${encodeURIComponent(
          searchQuery
        )}`
      : `/api/v1/computers/count`;

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      totalComputers = data.result.count;
      return data.result.count;
    } catch (error) {
      console.error("Error fetching total count:", error);
      totalComputers = 0;
      return 0;
    }
  }

  async function fetchComputers() {
    if (isSearching) {
      const url = `/api/v1/computers/generic?search=${encodeURIComponent(
        searchQuery
      )}&offset=${offset}&limit=${limit}`;
      const response = await fetch(url);
      const data = await response.json();

      if (response.status === 200) {
        tableBody.innerHTML = "";
        updatePagination();
        if (data.result.count > 0) {
          data.result.computers.forEach((computer) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td><span class="text-secondary">${highlightMatch(
                  computer.uuid_label,
                  searchQuery
                )}</span></td>
                <td><a href="/computers/${
                  computer.uuid_label
                }" class="text-reset" tabindex="-1">${highlightMatch(
              computer.host_name,
              searchQuery
            )}</a></td>
                <td>${highlightMatch(computer.mac_address, searchQuery)}</td>
                <td>${highlightMatch(computer.ipv4_address, searchQuery)}</td>
                <td>${highlightMatch(computer.secseal, searchQuery)}</td>
                <td>${highlightMatch(
                  computer.network_adapter,
                  searchQuery
                )}</td>
                <td>${highlightMatch(
                  computer.pc_serialnumber,
                  searchQuery
                )}</td>
                `;
            tableBody.appendChild(row);
          });
          showingInfo.innerHTML = `Showing ${offset + 1} to ${
            offset + data.result.count
          } of ${totalComputers} search results`;
        } else {
          showingInfo.innerHTML = `Showing 0 to 0 of 0 search results`;
          tableBody.innerHTML =
            '<tr><td colspan="8" class="text-center">No search results</td></tr>';
        }
      } else if (response.status === 403 && data.error) {
        window.location.href = `/403?message=${data.error.name}`;
      }
    } else {
      const url = `/api/v1/computers/?offset=${offset}&limit=${limit}`;

      const response = await fetch(url);
      const data = await response.json();

      if (response.status === 200) {
        tableBody.innerHTML = "";
        updatePagination();
        if (data.result.count > 0) {
          data.result.computers.forEach((computer) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td><span class="text-secondary">${computer.uuid_label}</span></td>
                <td><a href="/computers/${computer.uuid_label}" class="text-reset" tabindex="-1">${computer.host_name}</a></td>
                <td>${computer.mac_address}</td>
                <td>${computer.ipv4_address}</td>
                <td>${computer.secseal}</td>
                <td>${computer.network_adapter}</td>
                <td>${computer.pc_serialnumber}</td>
                `;
            tableBody.appendChild(row);
          });

          showingInfo.innerHTML = `Showing ${offset + 1} to ${
            offset + data.result.count
          } of ${totalComputers} computers`;
        } else {
          showingInfo.innerHTML = `Showing 0 to 0 of 0 computers`;
          tableBody.innerHTML =
            '<tr><td colspan="8" class="text-center">No computers found</td></tr>';
        }
      } else if (response.status === 403 && data.error) {
        window.location.href = `/403?message=${data.error.name}`;
      }
    }
  }

  function updatePagination() {
    const currentPage = Math.floor(offset / limit) + 1;

    if (prevButton && nextButton && pageNumbers) {
      prevButton.parentElement.classList.toggle("disabled", offset === 0);
      nextButton.parentElement.classList.toggle(
        "disabled",
        offset + limit >= totalComputers
      );
    }
  }

  nextButton.addEventListener("click", function (event) {
    event.preventDefault();

    if (offset + limit < totalComputers) {
      offset += limit;
    }

    fetchComputers().then(() => {
      updatePagination();
    });
  });

  prevButton.addEventListener("click", function (event) {
    event.preventDefault();

    if (offset > 0) {
      offset -= limit;
    }

    fetchComputers().then(() => {
      updatePagination();
    });
  });

  searchInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
      searchQuery = searchInput.value.trim();
      offset = 0;

      if (searchQuery !== "") {
        isSearching = true;
      } else {
        isSearching = false;
      }

      fetchTotalCount().then(() => {
        fetchComputers();
      });
    }
  });

  fetchTotalCount().then(() => {
    fetchComputers();
  });
});
