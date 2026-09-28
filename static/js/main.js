/* Public site behaviour. Every block is guarded so any page can include it. */
(() => {
  'use strict';

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  const csrf = $('meta[name=csrf]')?.content;
  const waNum = $('#wa-number')?.dataset.number;


  /* ---------- Sticky nav shadow ---------- */

  const nav = $('#nav');
  if (nav) {
    const onScroll = () => nav.classList.toggle('scrolled', scrollY > 30);
    addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }


  /* ---------- Reveal on scroll + animated counters ---------- */

  const countUp = el => {
    const end = Number(el.dataset.count) || 0;
    const suffix = el.dataset.suffix || '';
    const start = performance.now();

    const step = now => {
      const progress = Math.min((now - start) / 1400, 1);
      el.textContent =
        Math.round(end * (1 - Math.pow(1 - progress, 3))).toLocaleString('en-IN') + suffix;
      if (progress < 1) requestAnimationFrame(step);
    };

    requestAnimationFrame(step);
  };

  const revealEls = $$('.reveal');
  if (revealEls.length) {
    const io = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('show');
      io.unobserve(entry.target);
      $$('[data-count]', entry.target).forEach(countUp);
    }), { threshold: 0.12 });

    revealEls.forEach(el => io.observe(el));
  }


  /* ---------- Toast ---------- */

  const toast = message => {
    const node = $('#toastOk');
    if (!node || !window.bootstrap) return;
    $('#toastBody').textContent = message;
    bootstrap.Toast.getOrCreateInstance(node).show();
  };


  /* =====================================================================
     Enquiry forms.

     These rules mirror clean_lead() in core/views.py — keep both in sync.
     ===================================================================== */

  const NAME_RE = /^[A-Za-z][A-Za-z .'-]{2,}$/;
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const PHONE_RE = /^[6-9]\d{9}$/;

  // "+91 90000 00000" / "919000000000" / "9000000000" -> "9000000000"
  const cleanPhone = raw => {
    let digits = String(raw ?? '').replace(/\D/g, '');
    if (digits.length > 10 && digits.startsWith('91')) digits = digits.slice(2);
    return digits;
  };

  const commonRules = ({ dateMin }) => ({
    full_name: value => {
      const text = String(value ?? '').trim();
      if (!text) return 'Please enter your full name.';
      if (text.length < 3) return 'Full name must be at least 3 letters.';
      if (!NAME_RE.test(text)) return "Only letters, spaces and . ' - are allowed.";
      return '';
    },
    email: value => {
      const text = String(value ?? '').trim();
      if (!text) return 'Please enter your email address.';
      if (!EMAIL_RE.test(text)) return 'Please enter a valid email address.';
      return '';
    },
    phone: value => {
      const digits = cleanPhone(value);
      if (!digits) return 'Please enter your mobile number.';
      if (digits.length !== 10) return 'Phone number must be exactly 10 digits (excluding +91).';
      if (!PHONE_RE.test(digits)) return 'Enter a valid mobile number starting with 6, 7, 8 or 9.';
      return '';
    },
    destination: value => String(value ?? '').trim() ? '' : 'Please select a destination.',
    travel_date: value => {
      const date = String(value ?? '').trim();
      if (!date) return 'Please choose your travel date.';
      if (dateMin && date < dateMin) return 'Travel date must be today or a future date.';
      return '';
    },
    travelers: value => {
      const raw = String(value ?? '').trim();
      if (!raw) return 'Please enter the number of travelers.';
      const count = Number(raw);
      if (!Number.isInteger(count) || count < 1) return 'Please enter at least 1 traveler.';
      if (count > 50) return 'For more than 50 travelers, please contact us directly.';
      return '';
    },
  });


  function initEnquiryForm(form) {
    const simple = form.dataset.mode === 'simple';
    const dateMin = form.elements.travel_date?.min || '';
    const allRules = commonRules({ dateMin });

    const rules = simple
      ? { full_name: allRules.full_name, email: allRules.email, phone: allRules.phone }
      : allRules;

    const setFieldError = (name, message) => {
      const input = form.elements[name];
      if (!input) return;
      input.classList.toggle('is-invalid', Boolean(message));
      input.setAttribute('aria-invalid', message ? 'true' : 'false');
      const box = $(`[data-error-for="${name}"]`, form);
      if (box) box.textContent = message;
    };

    const clearErrors = () => Object.keys(rules).forEach(name => setFieldError(name, ''));

    const validate = () => {
      let firstBad = null;
      Object.keys(rules).forEach(name => {
        const input = form.elements[name];
        const message = rules[name](input?.value);
        setFieldError(name, message);
        if (message && !firstBad) firstBad = input;
      });
      firstBad?.focus();
      return !firstBad;
    };

    Object.keys(rules).forEach(name => {
      const input = form.elements[name];
      if (!input) return;

      input.addEventListener('input', () => {
        if (name === 'phone') {
          const digits = input.value.replace(/\D/g, '').slice(0, 10);
          if (digits !== input.value) input.value = digits;
        }
        if (input.classList.contains('is-invalid')) {
          setFieldError(name, rules[name](input.value));
        }
      });

      input.addEventListener('blur', () => setFieldError(name, rules[name](input.value)));
    });

    form.addEventListener('submit', async event => {
      event.preventDefault();

      const msg = $('.form-msg', form);
      const button = form.querySelector('button[type=submit]');
      const data = Object.fromEntries(new FormData(form));

      data.phone = cleanPhone(data.phone);
      if (msg) { msg.textContent = ''; msg.className = 'form-msg small mt-3'; }

      if (!validate()) {
        if (msg) {
          msg.className = 'form-msg small mt-3 text-danger';
          msg.textContent = 'Please fix the highlighted fields above before submitting.';
        }
        return;
      }

      button.disabled = true;

      try {
        const response = await fetch('/api/inquiry/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
          body: JSON.stringify(data),
        });

        const json = await response.json();

        if (!json.ok) {
          if (json.errors) Object.entries(json.errors).forEach(([f, m]) => setFieldError(f, m));
          throw new Error(json.error || 'Please check the highlighted fields.');
        }

        form.reset();
        clearErrors();

        if (msg) {
          msg.className = 'form-msg small mt-3 text-success';
          msg.textContent = json.message;
        }
        toast(json.message);

      } catch (error) {
        if (msg) {
          msg.className = 'form-msg small mt-3 text-danger';
          msg.textContent = error.message || 'Something went wrong. Please try WhatsApp.';
        }
      }

      button.disabled = false;
    });

    return form;
  }

  const enquiryForms = $$('form.enquiry-form').map(initEnquiryForm);
  const primaryForm = enquiryForms.find(f => f.dataset.mode !== 'simple') || enquiryForms[0];


  /* ---------- Hero search: validate, filter, prefill ---------- */

  const searchForm = $('#searchForm');
  const searchMsg = $('#searchMsg');

  const showSearchError = message => {
    if (!searchMsg) return;
    searchMsg.textContent = message;
    searchMsg.className = message ? 'small text-danger mt-2' : 'small mt-2';
  };

  if (searchForm) {
    searchForm.addEventListener('submit', event => {
      event.preventDefault();

      const destination = $('#sDest').value;
      const date = $('#sDate').value;
      const travelers = $('#sTrav').value;

      if (!destination) return showSearchError('Please select a destination to search.');
      if (!date) return showSearchError('Please choose your travel date.');
      if (date < $('#sDate').min) return showSearchError('Travel date must be today or a future date.');
      if (!travelers) return showSearchError('Please select the number of travelers.');

      showSearchError('');

      $$('.pkg-col').forEach(card => {
        card.style.display = (!card.dataset.cat || card.dataset.cat === destination) ? '' : 'none';
      });

      if (primaryForm) {
        if (primaryForm.elements.destination) primaryForm.elements.destination.value = destination;
        if (primaryForm.elements.travel_date) primaryForm.elements.travel_date.value = date;
        if (primaryForm.elements.travelers) primaryForm.elements.travelers.value = travelers;
      }

      $('#packages')?.scrollIntoView();
    });
  }


  /* ---------- Package quick view modal ---------- */

  const modalEl = $('#pkgModal');

  if (modalEl && window.bootstrap) {
    const modal = new bootstrap.Modal(modalEl);
    let current = null;

    $$('.btn-details').forEach(button => {
      button.addEventListener('click', async () => {
        button.disabled = true;
        try {
          const response = await fetch(`/api/packages/${button.dataset.slug}/`);
          if (!response.ok) throw new Error('not found');

          const pkg = current = await response.json();

          $('#mImg').src = pkg.image;
          $('#mImg').alt = pkg.title;
          $('#mTitle').textContent = pkg.title;
          $('#mDur').textContent = pkg.duration;
          $('#mPrice').textContent = '\u20b9' + pkg.price;
          $('#mFull').href = `/packages/${pkg.slug}/`;

          const fill = (listId, items) => {
            const list = $(listId);
            list.innerHTML = '';
            items.forEach(item => {
              const li = document.createElement('li');
              li.textContent = item;
              list.appendChild(li);
            });
          };

          fill('#mHigh', pkg.highlights);
          fill('#mInc', pkg.inclusions);

          $('#mWa').href = `https://wa.me/${waNum}?text=${encodeURIComponent(
            `Hi SMT Holidays, I am interested in the ${pkg.title} (${pkg.duration}).`)}`;

          modal.show();
        } catch {
          toast('Could not load package details. Please try again.');
        }
        button.disabled = false;
      });
    });

    $('#mQuote')?.addEventListener('click', event => {
      // Pages without the enquiry section (e.g. /packages/) let the link follow
      // through to the quote form on the contact page.
      const enquiry = document.getElementById('enquiry');
      if (!current || !primaryForm || !enquiry) return;

      event.preventDefault();

      primaryForm.elements.source.value = 'package: ' + current.title;

      const option = [...(primaryForm.elements.destination?.options || [])]
        .find(o => o.value === current.category);
      if (option) primaryForm.elements.destination.value = option.value;

      modal.hide();

      setTimeout(() => {
        enquiry.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 350);
    });
  }

})();
