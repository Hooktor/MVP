(() => {
  const root = document.querySelector('[data-matching-workbench]');
  if (!root) return;

  const storageKey = 'orbit-matching-shortlist-v1';
  const panel = document.querySelector('[data-shortlist-panel]');
  const list = panel.querySelector('[data-shortlist-items]');
  const empty = panel.querySelector('[data-shortlist-empty]');
  const clear = panel.querySelector('[data-shortlist-clear]');
  const count = panel.querySelector('[data-shortlist-count]');
  const compareCount = panel.querySelector('[data-compare-count]');
  const compareButton = panel.querySelector('[data-shortlist-compare]');
  const dialog = document.querySelector('[data-compare-dialog]');
  const compareBody = dialog.querySelector('[data-compare-body]');
  const compareHead = dialog.querySelector('thead tr');

  const readItems = () => {
    try {
      const items = JSON.parse(sessionStorage.getItem(storageKey) || '[]');
      return Array.isArray(items) ? items : [];
    } catch (_) {
      return [];
    }
  };
  let items = readItems();

  const save = () => {
    try { sessionStorage.setItem(storageKey, JSON.stringify(items)); } catch (_) { /* Shortlisting still works for this page view. */ }
  };
  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const initials = (name) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase();

  const capture = (row) => ({
    id: row.dataset.expertId,
    name: row.dataset.expertName,
    role: row.dataset.expertRole,
    subsidiary: row.dataset.expertSubsidiary,
    availability: row.dataset.expertAvailability,
    rate: row.dataset.expertRate,
    rating: row.dataset.expertRating,
    domains: row.dataset.expertDomains,
    skills: row.dataset.expertSkills,
    match: row.dataset.expertMatch,
    reasons: row.dataset.expertReasons,
    profile: row.dataset.expertProfile,
    solicit: row.dataset.expertSolicit,
  });

  const render = () => {
    const ids = new Set(items.map((item) => String(item.id)));
    document.querySelectorAll('[data-expert-id]').forEach((row) => {
      const selected = ids.has(String(row.dataset.expertId));
      row.classList.toggle('is-shortlisted', selected);
      const checkbox = row.querySelector('[data-shortlist-toggle]');
      if (checkbox) checkbox.checked = selected;
    });
    list.replaceChildren();
    items.forEach((item) => {
      const li = element('li', 'shortlist-item');
      const head = element('div', 'shortlist-item-head');
      head.append(element('span', 'avatar tint', initials(item.name)));
      const copy = element('span', 'shortlist-item-copy');
      copy.append(element('strong', '', item.name), element('small', '', item.role));
      head.append(copy);
      const remove = element('button', 'shortlist-remove', '×');
      remove.type = 'button';
      remove.setAttribute('aria-label', `Retirer ${item.name} de la shortlist`);
      remove.dataset.removeExpert = item.id;
      head.append(remove);
      li.append(head);
      const facts = element('div', 'shortlist-item-facts');
      facts.append(element('span', '', item.subsidiary), element('span', '', item.rate));
      li.append(facts);
      const actions = element('div', 'shortlist-item-actions');
      const profile = element('a', '', 'Voir le profil');
      profile.href = item.profile;
      actions.append(profile);
      if (item.solicit) {
        const solicit = element('a', 'button primary', 'Solliciter');
        solicit.href = item.solicit;
        actions.append(solicit);
      }
      li.append(actions);
      list.append(li);
    });
    const total = items.length;
    count.textContent = String(total);
    compareCount.textContent = String(total);
    compareButton.disabled = total < 2;
    clear.hidden = total === 0;
    empty.hidden = total > 0;
  };

  const updateCompare = () => {
    compareHead.replaceChildren(element('th', '', 'Critère'));
    compareHead.firstElementChild.scope = 'col';
    compareBody.replaceChildren();
    items.forEach((item) => {
      const th = element('th', '', item.name);
      th.scope = 'col';
      compareHead.append(th);
    });
    const criteria = [
      ['Fonction', (item) => item.role],
      ['Filiale', (item) => item.subsidiary],
      ['Disponibilité', (item) => item.availability],
      ['TJM indicatif', (item) => item.rate],
      ['Évaluation', (item) => item.rating ? `${item.rating} / 5` : 'Non évaluée'],
      ['Pertinence', (item) => item.match],
      ['Domaines', (item) => item.domains || 'Non renseignés'],
      ['Compétences', (item) => item.skills || 'Non renseignées'],
      ['Adéquation', (item) => item.reasons],
    ];
    criteria.forEach(([label, value]) => {
      const tr = document.createElement('tr');
      const rowHeading = element('th', '', label);
      rowHeading.scope = 'row';
      tr.append(rowHeading);
      items.forEach((item) => tr.append(element('td', '', value(item))));
      compareBody.append(tr);
    });
  };

  document.addEventListener('change', (event) => {
    const checkbox = event.target.closest('[data-shortlist-toggle]');
    if (!checkbox) return;
    const row = checkbox.closest('[data-expert-id]');
    const profile = capture(row);
    if (checkbox.checked) {
      if (!items.some((item) => String(item.id) === String(profile.id))) items.push(profile);
    } else {
      items = items.filter((item) => String(item.id) !== String(profile.id));
    }
    save();
    render();
  });

  document.addEventListener('click', (event) => {
    const remove = event.target.closest('[data-remove-expert]');
    if (remove) {
      items = items.filter((item) => String(item.id) !== String(remove.dataset.removeExpert));
      save();
      render();
      return;
    }
    if (event.target.closest('[data-shortlist-clear]')) {
      items = [];
      save();
      render();
      return;
    }
    if (event.target.closest('[data-shortlist-compare]') && items.length > 1) {
      updateCompare();
      dialog.showModal();
      return;
    }
    if (event.target.closest('[data-compare-close]')) dialog.close();
  });

  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
  document.body.addEventListener('htmx:afterSwap', (event) => {
    if (event.detail.target.id === 'results') render();
  });
  render();
})();
