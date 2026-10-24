'use strict';

// CLI-only observations. Never call guestClock.ticks(): tracing must not spend
// a guest clock probe. IDs identify observations, not inferred MSG provenance.
function createInputConsumptionTrace({ enabled, logs, snapshot, limit = 1000 }) {
  let count = 0;
  let dequeueId = 0;
  let lastDequeueId = null;
  let enqueueId = 0;
  const enqueued = new WeakMap();
  const emit = (prefix, detail) => {
    if (!enabled) return;
    if (count >= limit) {
      if (count++ === limit) logs.push('[input-timing] trace limit reached; further observations suppressed');
      return;
    }
    count++;
    const s = snapshot();
    logs.push(`${prefix} ${detail} batch=${s.batch} guestMs=${s.guestMs}`
      + ` clock=${s.clock} lastGuestTick=${s.lastGuestTick}`);
  };
  const hex = n => `0x${(n >>> 0).toString(16)}`;
  return {
    schedule: ev => emit('[input-schedule]',
      `scheduledBatch=${ev.batch} action=${ev.action || 'raw'} correlation=unavailable`),
    enqueue: (evt, ev) => {
      if (enabled) {
        const id = ++enqueueId;
        enqueued.set(evt, { id, batch: ev.batch });
        emit('[input-enqueue]', `enqueueId=${id} scheduledBatch=${ev.batch}`);
      }
      return evt;
    },
    dequeue: (evt, source) => {
      if (!enabled) return;
      lastDequeueId = ++dequeueId;
      const origin = enqueued.get(evt);
      emit('[input-dequeue]', `dequeueId=${lastDequeueId} source=${source}`
        + (origin ? ` enqueueId=${origin.id} scheduledBatch=${origin.batch}` : ' enqueueId=unavailable')
        + ` hwnd=${hex(evt.hwnd)} msg=${hex(evt.msg)} wParam=${hex(evt.wParam)} lParam=${hex(evt.lParam)}`);
    },
    route: (focusHwnd, hwnd) => {
      if (lastDequeueId !== null) emit('[input-dequeue-route]',
        `dequeueId=${lastDequeueId} focusHwnd=${hex(focusHwnd)} hwnd=${hex(hwnd)}`);
    },
    dispatch: (api, hwnd, msg, wp, lp) => emit('[dispatch-input]',
      `${api} hwnd=${hex(hwnd)} msg=${hex(msg)} wParam=${hex(wp)} lParam=${hex(lp)}`
      + ' correlation=unavailable'),
  };
}

module.exports = { createInputConsumptionTrace };
