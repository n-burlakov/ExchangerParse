function getTurnstileParams() {
  console.log('getTurnstileParams has started');
  if (window.turnstile) {
    console.log(window.turnstile)
    clearInterval(i)
    window.turnstile.render = (a, b) => {
      let p = {
        method: "turnstile",
        sitekey: b.sitekey,
        pageurl: window.location.href,
        data: b.cData,
        pagedata: b.chlPageData,
        action: b.action,
        json: 1
      }
      console.log(JSON.stringify(p))
      window.tsCallback = b.callback
      return 'foo'
    }

  }
}
const i = setInterval(() => {
  getTurnstileParams();
}, 50);

