// Send and receive data from Python backend
async function callAPI(endpoint, method, data = {}) {
    var url = window.origin + "/api/" + endpoint;
    var response;
    if (method == "POST") {
        response = await window.fetch(url, {
            method: method,
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });
    } else {
        response = await window.fetch(url, {
            method: method,
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            }
        });
    }
    var responseData = await response.json();
    return responseData;
}

// Scrape data
function getData(dataType) {
    var user = document.getElementById("user-input").value;
    resp = callAPI("get-data", "POST", {"user": user, "type": dataType});
    console.log(resp);
}

// On load
window.onload = function(event) {
    document.getElementById("user-input").value = "";
}