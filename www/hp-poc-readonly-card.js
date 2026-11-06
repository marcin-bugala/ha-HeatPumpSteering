/* Native HA cards with hover preserved and activation suppressed. No services. */
class HpPocReadonlyCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    const style = document.createElement('style');
    style.textContent = ':host{display:block;min-width:0} #content{min-width:0}';
    this._content = document.createElement('div');
    this._content.id = 'content';
    this.shadowRoot.append(style, this._content);
    const stop = (event) => {
      event.preventDefault();
      event.stopImmediatePropagation();
    };
    for (const type of ['click', 'dblclick', 'contextmenu', 'action', 'hass-action', 'hass-more-info']) {
      this.addEventListener(type, stop, { capture: true });
    }
    this.addEventListener('keydown', (event) => {
      if (['Enter', ' ', 'Spacebar'].includes(event.key)) stop(event);
    }, { capture: true });
    this._revision = 0;
  }

  setConfig(config) {
    if (!config.card || typeof config.card.type !== 'string') {
      throw new Error('Karta tylko do odczytu wymaga konfiguracji card.type.');
    }
    this._build(config.card, ++this._revision);
  }

  async _build(config, revision) {
    try {
      const helpers = await window.loadCardHelpers();
      if (revision !== this._revision) return;
      const card = helpers.createCardElement(config);
      if (this._hass) card.hass = this._hass;
      this._card = card;
      this._content.replaceChildren(card);
      this.dispatchEvent(new Event('card-size-changed', { bubbles: true, composed: true }));
    } catch (error) {
      if (revision !== this._revision) return;
      this._card = undefined;
      const message = document.createElement('ha-card');
      message.style.padding = '20px';
      message.textContent = `Nie udało się wczytać wykresów: ${error.message}`;
      this._content.replaceChildren(message);
    }
  }

  set hass(hass) {
    this._hass = hass;
    if (this._card) this._card.hass = hass;
  }

  async getCardSize() {
    if (!this._card) return 6;
    await customElements.whenDefined(this._card.localName);
    return this._card.getCardSize?.() ?? 6;
  }

  getGridOptions() {
    return { columns: 'full', rows: 'auto' };
  }
}

if (!customElements.get('hp-poc-readonly-card')) {
  customElements.define('hp-poc-readonly-card', HpPocReadonlyCard);
}
