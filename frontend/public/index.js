window.onload = function() {
  enableButton();

var sidebar = document.getElementById("sidebar");
var toggleSidebarButton = document.getElementById("toggle-sidebar");

toggleSidebarButton.addEventListener("click", function () {
  if (sidebar.classList.contains("show")) {
      sidebar.classList.remove("show");
  } else {
      sidebar.classList.add("show");
  }
});

function toggleElement(id) {
  const element = document.getElementById(id);
  if (element.style.maxHeight) {
      element.style.maxHeight = null;
  } else {
      element.style.maxHeight = element.scrollHeight + "px";
  }
}

function handleControllerClick(e) {
  const controllerName = e.target.textContent;

  // Remove the selected class from any previously selected controller
  const controllers = document.querySelectorAll('#controller-window ul');
  controllers.forEach(controller => {
    controller.classList.remove('selected');
  });

  // Add the selected class to the clicked controller
  e.target.classList.add('selected');

  // Fetch the devices
  fetch('https://controllerbackend.herokuapp.com/getDeviceList', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    credentials: 'include',
    body: JSON.stringify({ controllerName: 'default' })
  })
  .then(response => {
    // If the response indicates failure, throw an error
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    // Handle devices
    console.log(data);
    const deviceWindow = document.getElementById('device-window');
    deviceWindow.textContent = ''; // Clear the window
    data.forEach(device => {
      const card = document.createElement('div');
      card.classList.add('device-card');
      card.style.display = 'flex';
      card.style.justifyContent = 'space-between';

      const img = document.createElement('div');
      img.classList.add('device-card-img');
      card.appendChild(img);

      const info = document.createElement('div');
      info.style.textAlign = 'left';

      const name = document.createElement('div');
      name.classList.add('device-card-name');
      name.style.fontWeight = 'bold';
      name.textContent = device.name;
      info.appendChild(name);

      const description = document.createElement('div');
      description.textContent = device.info;
      info.appendChild(description);

      const buttons = document.createElement('div');

      const configureButton = document.createElement('button');
      configureButton.textContent = 'Configure';
      configureButton.addEventListener('click', function() {
          // Open the modal
          const modal = document.getElementById('device-config-modal');
          modal.style.display = "block";

          // Switch the settings button to a save button
          const settingsButton = document.getElementById('settings-button');
          settingsButton.textContent = "Settings";

          // Make the name and info editable
          const nameInput = document.getElementById('device-config-name-input');
          const infoInput = document.getElementById('device-config-info-input');
          nameInput.value = device.name;
          infoInput.value = device.info;

          // Make the inputs readonly
          nameInput.readOnly = true;
          infoInput.readOnly = true;

          // Clear any previous command buttons and info fields
          const modalContent = document.querySelector('.modal-content');
          const oldCommands = modalContent.querySelectorAll('.command-container');
          oldCommands.forEach(command => command.remove());

          // Create command buttons and info fields
          device.commands.forEach(command => {
            const commandContainer = document.createElement('div');
            commandContainer.classList.add('command-container');

            const commandButton = document.createElement('button');
            commandButton.textContent = command.command;
            commandButton.addEventListener('click', function() {
              fetch(`https://controllerbackend.herokuapp.com/getCommand/${device.name}/${command.command}`, {
                  method: 'GET',
                  credentials: 'include',
              })
              .then(response => {
                  if (!response.ok) {
                      throw new Error(`HTTP error! status: ${response.status}`);
                  }
                  return response.json();
              })
              .then(data => {
                  // The command string is now in data.command
                  // You can send it to the Raspberry Pi here
                  console.log(data.command);
              })
              .catch(error => {
                  console.error('There was an error!', error);
              });
          });

            commandContainer.appendChild(commandButton);

            const commandInfoInput = document.createElement('input');
            commandInfoInput.type = 'text';
            commandInfoInput.value = command.com_info;
            commandInfoInput.classList.add('command-info');
            commandInfoInput.readOnly = true;  // Info is not editable until Settings button is clicked
            commandContainer.appendChild(commandInfoInput);

            modalContent.appendChild(commandContainer);  // Add the command to the modal content
        });

          settingsButton.onclick = function() {
            if(settingsButton.textContent === "Settings") {
                settingsButton.textContent = "Save";
                // Make the inputs editable
                nameInput.readOnly = false;
                infoInput.readOnly = false;

                // Make command info fields editable
                const commandInfoFields = modalContent.querySelectorAll('.command-info');
                commandInfoFields.forEach(field => field.readOnly = false);
            } else {
                // The button was in the 'Save' state, so the information can now be saved.
                settingsButton.textContent = "Settings";
                // Make the inputs readonly again
                nameInput.readOnly = true;
                infoInput.readOnly = true;

                // Make command info fields read-only again
                const commandInfoFields = modalContent.querySelectorAll('.command-info');
                commandInfoFields.forEach(field => {
                    field.readOnly = true;

                    // Get the command name from the previous sibling button
                    const commandName = field.previousSibling.textContent;

                    // Send a request to the updateCommandInfo endpoint
                    fetch('https://controllerbackend.herokuapp.com/updateCommandInfo', {
                        method: 'POST',
                        credentials: 'include',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            deviceName: device.name,
                            command: commandName,
                            newComInfo: field.value
                        }),
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.status !== 'success') {
                            // Handle error
                            console.error('Failed to update command info: ' + data.message);
                        }
                    })
                    .catch(error => {
                        console.error('There was an error!', error);
                    });
                });
              }
          };
      });

      // When the user clicks on <span> (x), close the modal
      document.getElementsByClassName('close-button')[0].onclick = function() {
          document.getElementById('device-config-modal').style.display = "none";
      }

      // When the user clicks anywhere outside of the modal, close it
      window.onclick = function(event) {
          if (event.target == document.getElementById('device-config-modal')) {
              document.getElementById('device-config-modal').style.display = "none";
          }
      }

      buttons.appendChild(configureButton);

      info.appendChild(buttons);
      card.appendChild(info);

      deviceWindow.appendChild(card);
  });
});

// Fetch the logs
fetch('https://controllerbackend.herokuapp.com/getLogs/' + controllerName, {
method: 'POST',
credentials: 'include',
headers: {
  'Content-Type': 'application/json',
},
body: JSON.stringify({ controllerName })
})
.then(response => {
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
})
.then(data => {
  const logsArea = document.getElementById('logs-area');
  logsArea.value = data.join('\n');
})
.catch(error => {
  console.error('There was an error!', error);
});
}





function enableButton() {
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const loginButton = document.querySelector('.login-button');

  if (username !== '' && password !== '') {
      loginButton.disabled = false;
      loginButton.classList.remove("button-disabled");
  } else {
      loginButton.disabled = true;
      loginButton.classList.add("button-disabled");
  }
}



document.getElementById('username').addEventListener('input', enableButton);
document.getElementById('password').addEventListener('input', enableButton);


document.getElementById('login').addEventListener('click', function() {
  toggleElement('login-window');
});

document.getElementById('controller').addEventListener('click', function() {
  toggleElement('controller-window');
});

document.getElementById('logs').addEventListener('click', function() {
  toggleElement('logs-window');
});

document.querySelector('.login-button').addEventListener('click', function() {
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;

  fetch('https://controllerbackend.herokuapp.com/login', {
    method: 'POST',
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  })

  .then(response => {
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    if (data.status === 'success') {
        const controllerWindow = document.getElementById('controller-window');
        controllerWindow.textContent = ''; // Clear the window
        const ul = document.createElement('ul');
        data.controllers.forEach(controllerName => {
            const li = document.createElement('li');
            li.textContent = controllerName;
            li.addEventListener('click', handleControllerClick); // Attach the event listener here
            ul.appendChild(li);
        });
        controllerWindow.appendChild(ul);
        // Disable the confirm button
        document.getElementById('confirm-button').disabled = true;
    } else {
        document.getElementById('error-message').innerText = 'Failed to login: ' + data.message;
    }
  })
  .catch((error) => {
    document.getElementById('error-message').innerText = 'Problem: ' + error.message;
  });
});
};
