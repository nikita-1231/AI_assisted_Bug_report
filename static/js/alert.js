function showAlert(message, type = "success") {
    console.log("showAlert called");

    const alertBox = document.getElementById("customAlert");
    const alertMsg = document.getElementById("alertMessage");

    alertMsg.innerText = message;

    alertBox.classList.remove("hidden");
    alertBox.classList.remove("error");

    if (type === "error") {
        alertBox.classList.add("error");
    }


    setTimeout(() => {
        alertBox.classList.add("hidden");
    }, 3000);
}
console.log("alert.js loaded");
