/* Dashboard interactions: WYSIWYG editor, live image previews, alerts. */
(() => {
  'use strict';

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ---------- WYSIWYG rich text editor ---------- */

  const richFields = $$('textarea[data-richtext]');

  if (richFields.length && window.tinymce) {
    tinymce.init({
      selector: 'textarea[data-richtext]',
      height: 340,
      menubar: false,
      branding: false,
      promotion: false,
      convert_urls: false,
      plugins: 'lists link table code paste wordcount',
      toolbar:
        'undo redo | blocks | bold italic underline | ' +
        'bullist numlist | link table | removeformat code',
      content_style:
        'body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:15px;line-height:1.6}',
      /* Keep the form in sync so nothing is lost on submit. */
      setup(editor) {
        editor.on('change keyup', () => editor.save());
      },
    });
  }

  /* ---------- Live preview before saving ---------- */

  const previewFor = (input, file) => {
    let box = input.closest('.dash-field')?.querySelector('.dash-preview');
    if (!box) {
      box = document.createElement('div');
      box.className = 'dash-preview';
      input.insertAdjacentElement('afterend', box);
    }

    box.innerHTML = '';
    const img = document.createElement('img');
    img.src = URL.createObjectURL(file);
    img.alt = 'Selected image preview';
    box.appendChild(img);

    const note = document.createElement('span');
    note.className = 'dash-preview-note';
    note.textContent = 'Preview of the image you are about to upload';
    box.appendChild(note);
  };

  $$('input[type=file]').forEach(input => {
    input.addEventListener('change', () => {
      const file = input.files && input.files[0];
      if (!file || !file.type.startsWith('image/')) return;
      previewFor(input, file);
    });
  });

  /* ---------- Dismissible alerts ---------- */

  $$('.dash-alert-close').forEach(btn => {
    btn.addEventListener('click', () => btn.closest('.dash-alert')?.remove());
  });

  /* ---------- Mobile sidebar ---------- */

  const toggle = $('[data-dash-toggle]');
  if (toggle) {
    toggle.addEventListener('click', () =>
      document.body.classList.toggle('dash-nav-open'));
  }

  /* ---------- Confirm destructive actions ---------- */

  $$('[data-confirm]').forEach(el => {
    el.addEventListener('click', event => {
      if (!window.confirm(el.dataset.confirm)) event.preventDefault();
    });
  });
})();
