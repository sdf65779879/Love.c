import { reactive, ref, watch } from "vue";

type DraftForm = Record<string, string | boolean>;

export function useEditorDraft() {
  const form = reactive<DraftForm>({});
  const hasDraft = ref(false);
  const restored = ref(false);
  const persistent = ref(true);
  // Keep drafts usable within this page even when browser storage is unavailable.
  const cache = new Map<string, string | null>();
  let activeKey = "";
  let baseline = "";

  function clear(key = activeKey) {
    if (!key) return;
    cache.set(key, null);
    try {
      window.localStorage.removeItem(key);
    } catch {
      persistent.value = false;
    }
    if (key === activeKey) {
      activeKey = "";
      hasDraft.value = false;
      restored.value = false;
    }
  }

  function begin(key: string, initial: DraftForm) {
    // Do not save initialization or restoration over another record's draft.
    activeKey = "";
    baseline = JSON.stringify(initial);
    let serialized = cache.get(key);
    try {
      const stored = window.localStorage.getItem(key);
      if (serialized === undefined) serialized = stored;
      persistent.value = stored === serialized;
    } catch {
      persistent.value = false;
    }
    if (serialized !== undefined) cache.set(key, serialized);
    const values = { ...initial };
    if (serialized) {
      try {
        const saved: unknown = JSON.parse(serialized);
        if (saved && typeof saved === "object" && !Array.isArray(saved)) {
          for (const field of Object.keys(initial)) {
            const value = (saved as Record<string, unknown>)[field];
            if (typeof value === typeof initial[field])
              values[field] = value as string | boolean;
          }
        }
      } catch {
        // An invalid or outdated draft must not prevent opening the editor.
      }
    }
    for (const field of Object.keys(form)) delete form[field];
    Object.assign(form, values);
    hasDraft.value = JSON.stringify(values) !== baseline;
    restored.value = hasDraft.value;
    activeKey = key;
  }

  watch(form, () => {
    if (!activeKey) return;
    const serialized = JSON.stringify(form);
    hasDraft.value = serialized !== baseline;
    restored.value = false;
    cache.set(activeKey, hasDraft.value ? serialized : null);
    try {
      if (hasDraft.value) window.localStorage.setItem(activeKey, serialized);
      else window.localStorage.removeItem(activeKey);
      persistent.value = true;
    } catch {
      persistent.value = false;
    }
  }, { deep: true, flush: "sync" });

  return { form, hasDraft, restored, persistent, begin, clear };
}
