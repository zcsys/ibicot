/*
 * Worker bridge: makes phase0_economy_engine_app.js talk to the Python kernel
 * over WebSocket instead of a browser Web Worker.  It replaces the global
 * `Worker` constructor before app.js loads, keeping the app's postMessage /
 * onmessage protocol unchanged.
 *
 * Load this after engine/model.js and before phase0_economy_engine_app.js.
 */
(function () {
  'use strict';
  const proto = location.protocol === 'https:' ? 'wss://' : 'ws://';
  const WS_URL = proto + location.host + '/ws';

  class RemoteWorker {
    constructor(url) {
      this.onmessage = null;
      this.onerror = null;
      this._listeners = {};
      this._ready = false;
      this._queue = [];
      this._ws = new WebSocket(WS_URL);
      const self = this;
      this._ws.onopen = () => {
        self._ready = true;
        const q = self._queue;
        self._queue = [];
        for (const m of q) self._ws.send(JSON.stringify(m));
      };
      this._ws.onmessage = (ev) => {
        let data;
        try {
          data = JSON.parse(ev.data);
        } catch (err) {
          return;
        }
        if (typeof self.onmessage === 'function') self.onmessage({ data });
        const cbs = self._listeners['message'];
        if (cbs) for (const cb of cbs) cb({ data });
      };
      this._ws.onerror = () => {
        if (typeof self.onerror === 'function') self.onerror({ message: 'Backend connection error' });
      };
    }
    postMessage(msg) {
      if (this._ready) this._ws.send(JSON.stringify(msg));
      else this._queue.push(msg);
    }
    addEventListener(type, cb) {
      (this._listeners[type] = this._listeners[type] || []).push(cb);
    }
    removeEventListener(type, cb) {
      const cbs = this._listeners[type];
      if (cbs) this._listeners[type] = cbs.filter((f) => f !== cb);
    }
    terminate() {
      try {
        this._ws.close();
      } catch (err) {
        /* noop */
      }
    }
  }

  window.Worker = RemoteWorker;
})();
