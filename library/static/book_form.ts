function BookForm (): object {
  function init (): void {
    for (const elementId of ['acquired', 'alienated', 'ebook_acquired']) {
      addSetDateTodayButton(elementId);
    }

    isbnFieldPasteFilter('#id_isbn');
    isbnFieldPasteFilter('#id_ebook_isbn');
  }

  function addSetDateTodayButton (elementId: string): void {
    const template = document.createElement('template');
    template.innerHTML = `<a href="#" id="${elementId}_date_set_today">Set to today</a>`;

    document
      .querySelector(`#div_id_${elementId}_date`)
      ?.append(template.content.children[0]);

    document
      .querySelector(`#${elementId}_date_set_today`)
      ?.addEventListener('click', ev => {
        setDateToday(ev, elementId);
      });
  }

  function isbnFieldPasteFilter (selector: string): void {
    const element: HTMLInputElement = document.querySelector(selector)!;
    element.addEventListener('paste', function (ev: ClipboardEvent) {
      ev.preventDefault();
      const pastedText = ev.clipboardData?.getData('text/plain');
      this.value = pastedText?.replace(/\D/g, '') ?? '';
    });

    element.addEventListener('input', function (ev: Event) {
      ev.preventDefault();
      this.value = this.value.replace(/\D/g, '');
    });
  }

  function setDateToday (event: Event, elementId: string): void {
    event.preventDefault();

    const date = new Date();

    const monthField: HTMLInputElement = document.querySelector(
      `#id_${elementId}_date_month`
    )!;
    monthField.value = String(date.getMonth() + 1);
    monthField.dispatchEvent(new Event('change', { bubbles: true }));

    const yearField: HTMLInputElement = document.querySelector(
      '#id_' + elementId + '_date_year'
    )!;
    yearField.value = String(date.getFullYear());
    yearField.dispatchEvent(new Event('change', { bubbles: true }));

    const dayField: HTMLInputElement = document.querySelector(
      '#id_' + elementId + '_date_day'
    )!;
    dayField.value = String(date.getDate());
    dayField.dispatchEvent(new Event('change', { bubbles: true }));
  }

  return { init };
}

export default BookForm;
export { BookForm };
