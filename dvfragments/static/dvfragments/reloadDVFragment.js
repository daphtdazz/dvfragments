window.reloadDVFragment = (name) => {
  function fragmentUpdater () {
    if (this.status !== 200) {
      console.warn(`Unable to update fragment '${name}': ${this.status} ${this.statusText}'`);
      return;
    }

    const ele = document.querySelector(`[x-dvfragment-id=${name}]`);
    const parser = new DOMParser();
    const newDoc = parser.parseFromString(this.responseText, 'text/html');
    ele.replaceWith(newDoc.body.firstChild);
  }

  const fragmentURL = new URL(window.location);
  fragmentURL.searchParams.append('fragment', name);

  const oReq = new XMLHttpRequest();
  oReq.addEventListener("load", fragmentUpdater);
  oReq.open("GET", fragmentURL);
  oReq.send();
}
