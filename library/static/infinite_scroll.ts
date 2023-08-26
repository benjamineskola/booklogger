function InfiniteScroll(): any {
  function updateScrollPosition(this: HTMLElement): void {
    Array.from(document.querySelectorAll('h2')).forEach(function (el) {
      const height = window.innerHeight;

      const top = window.pageYOffset;
      const offsetTop =
        el.getBoundingClientRect().top +
        top -
        document.documentElement.clientTop;
      const distance = top - offsetTop;

      const hash = el.getAttribute('href');

      if (Math.abs(distance) < height * 0.75) {
        if (window.location.hash !== hash) {
          if (history.pushState !== undefined) {
            history.pushState(null, '', hash);
          } else if (typeof hash !== 'undefined' && hash !== null) {
            window.location.hash = hash;
          }
        }
      } else if (-distance > height && hash === window.location.hash) {
        const year = hash.split('-').pop();
        let newYear;
        if (year === 'sometime') {
          newYear = 2004;
        } else {
          newYear = parseInt(String(year)) + 1;
        }
        const newHash = `#read-${newYear}`;
        if (history.pushState !== undefined) {
          history.pushState(null, '', newHash);
        } else {
          window.location.hash = newHash;
        }
      }
    });
  }

  return { updateScrollPosition };
}

export default InfiniteScroll;
export { InfiniteScroll };
