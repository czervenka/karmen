const BASE_URL = window.env.BACKEND_BASE;

export const getPrinters = (fields = []) => {
  return fetch(`${BASE_URL}/printers?fields=${fields.join(',')}`)
    .then((response) => {
      if (response.status !== 200) {
        console.error(`Cannot get list of printers: ${response.status}`);
        return;
      }
      return response.json();
    }).catch((e) => {
      console.error(`Cannot get list of printers: ${e}`);
      return [];
    });
}

export const getPrinter = (ip, fields = []) => {
  return fetch(`${BASE_URL}/printers/${ip}?fields=${fields.join(',')}`)
    .then((response) => {
      if (response.status !== 200) {
        console.error(`Cannot get a printer: ${response.status}`);
        return;
      }
      return response.json();
    }).catch((e) => {
      console.error(`Cannot get a printer: ${e}`);
      return {};
    })
}

export const addPrinter = (ip, name) => {
  return fetch(`${BASE_URL}/printers`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ip, name}),
  })
    .then((response) => {
      if (response.status !== 201) {
        console.error(`Cannot add a printer: ${response.status}`);
      }
      return response.status;
    }).catch((e) => {
      console.error(`Cannot add a printer: ${e}`);
      return 500;
    })
}

export const patchPrinter = (ip, data) => {
  return fetch(`${BASE_URL}/printers/${ip}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
    .then((response) => {
      if (response.status !== 204) {
        console.error(`Cannot patch a printer: ${response.status}`);
      }
      return response.status;
    }).catch((e) => {
      console.error(`Cannot patch a printer: ${e}`);
      return 500;
    })
}


export const deletePrinter = (ip) => {
  return fetch(`${BASE_URL}/printers/${ip}`, {
    method: 'DELETE',
  })
    .then((response) => {
      if (response.status !== 204) {
        console.error(`Cannot remove a printer: ${response.status}`);
      }
      return response.status;
    }).catch((e) => {
      console.error(`Cannot remove a printer: ${e}`);
      return 500;
    })
}

export const changeSettings = (settings) => {
  return fetch(`${BASE_URL}/settings`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(settings),
  })
    .then((response) => {
      if (response.status !== 201) {
        console.error(`Cannot change a setting: ${response.status}`);
      }
      return response.status;
    }).catch((e) => {
      console.error(`Cannot change a setting: ${e}`);
      return 500;
    })
}

export const getSettings = (settings) => {
  return fetch(`${BASE_URL}/settings`)
    .then((response) => {
      if (response.status !== 200) {
        console.error(`Cannot get settings: ${response.status}`);
        return [];
      }
      return response.json();
    }).catch((e) => {
      console.error(`Cannot get settings: ${e}`);
      return [];
    })
}