window.reloadDVFragment = (name) => {
  function fragmentUpdater () {
    const ele = document.querySelector(`[x-dvfragment-id=${name}]`);
    console.log(this.responseText);
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
