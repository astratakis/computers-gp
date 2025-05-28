document.addEventListener("DOMContentLoaded", function () {
  const tableBody = document.querySelector("tbody");

  async function fetchComputerData(label) {
    try {
      const response = await fetch(
        `/api/v1/computers/label/${label}?offset=0&limit=3`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();

      const hostName = data.result.computer.host_name;
      document.getElementById("hostname").textContent = hostName;

      const uuid_label = data.result.computer.uuid_label;
      document.getElementById("uuid_label").textContent = uuid_label;

      if (data.result.entries.count > 0) {
        data.result.entries.history.forEach((entry) => {
          const row = document.createElement("tr");
          row.innerHTML = `
                  <td><span class="text-secondary">${entry.uuid}</span></td>
                  <td>${entry.created_by}</td>
                  <td>${entry.created_at}</td>
                  <td>${entry.reason}</td>
                  <td>${entry.signed_by}</td>
                  <td>${entry.signed_at}</td>
              `;
          tableBody.appendChild(row);
        });
      } else {
        tableBody.innerHTML =
          '<tr><td colspan="8" class="text-center">No history found</td></tr>';
      }

      updateDatagrid(data.result.computer);
    } catch (error) {
      console.error("Error fetching computer data:", error);
    }
  }

  function updateDatagrid(computer) {
    const mappings = {
      "IPv4 Address": computer.ipv4_address,
      "MAC Address": computer.mac_address,
      Make: computer.make,
      Model: computer.model,
      "PC Serial Number": computer.pc_serialnumber,
      Network: computer.network,
      "Network Adapter": computer.network_adapter,
      "Network Adapter Serial Number": computer.net_adapter_serialnumber,
      "Operating System": computer.os,
      "Security Seal": computer.secseal,
      User: computer.user_name,
      "UUID Label": computer.uuid_label,
      YAT: computer.yat,
      Subdivision: computer.office_location,
      "Office Number": computer.office_number,
      Telephone: computer.telephone,
    };

    document.querySelectorAll(".datagrid-item").forEach((item) => {
      const titleElement = item.querySelector(".datagrid-title");
      const contentElement = item.querySelector(".datagrid-content");

      if (titleElement && contentElement) {
        const key = titleElement.textContent.trim();
        let content =
          mappings[key] !== undefined && mappings[key] !== null
            ? mappings[key]
            : "-";

        // Add SVG icon next to Operating System if it's Linux or Ubuntu
        if (key === "Operating System") {
          if (content.toLowerCase() === "linux") {
            const osIcon = `
                      <img src="/static/icons/ubuntu.svg" alt="Linux/Ubuntu" style="width: 20px; height: 20px; vertical-align: middle; margin-left: 5px;" />
                  `;
            content = content + osIcon; // Append the icon to the content
          } else if (content.toLowerCase() === "windows") {
            const osIcon = `
                      <img src="/static/icons/windows.svg" alt="Linux/Ubuntu" style="width: 20px; height: 20px; vertical-align: middle; margin-left: 5px;" />
                  `;
            content = content + osIcon; // Append the icon to the content
          }
        } else if (key == "Network Adapter") {
          if (content.toLowerCase() === "ethernet") {
            const osIcon = `
                      <img src="/static/icons/ethernet.svg" class="icon-dark-mode" alt="Ethernet" style="width: 20px; height: 20px; vertical-align: middle; margin-left: 5px;" />
                  `;
            content = content + osIcon; // Append the icon to the content
          } else if (content.toLowerCase() === "optical") {
            const osIcon = `
                      <img src="/static/icons/optical.svg" class="icon-dark-mode" alt="Optical" style="width: 20px; height: 20px; vertical-align: middle; margin-left: 5px;" />
                  `;
            content = content + osIcon; // Append the icon to the content
          }
        }

        contentElement.innerHTML = content;
      }
    });
  }

  // Set Label Dynamically (Replace with actual label)
  const label = window.location.pathname.split("/").pop();
  fetchComputerData(label);
});
