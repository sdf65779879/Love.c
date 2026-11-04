<script setup lang="ts">
import { computed, reactive, watch } from "vue";

const props = defineProps<{ modelValue: string; label: string; required?: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();
const parts = reactive({ year: "", month: "", day: "" });
const hasValue = computed(() => !!(parts.year || parts.month || parts.day));
const daysInMonth = computed(() => {
  const year = Number(parts.year);
  const month = Number(parts.month);
  if (month === 2) return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0) ? 29 : 28;
  return [4, 6, 9, 11].includes(month) ? 30 : 31;
});
const dateValue = computed(() => {
  const year = Number(parts.year);
  if (!Number.isInteger(year) || year < 1 || year > 9999 || !parts.month || !parts.day) return "";
  return `${String(year).padStart(4, "0")}-${parts.month.padStart(2, "0")}-${parts.day.padStart(2, "0")}`;
});

watch(() => props.modelValue, value => {
  // An incomplete edit emits an empty value while retaining its selected parts.
  if (value === dateValue.value) return;
  const [year = "", month = "", day = ""] = value.split("-");
  Object.assign(parts, { year, month: month ? String(Number(month)) : "", day: day ? String(Number(day)) : "" });
}, { immediate: true });

function update(part: keyof typeof parts, event: Event) {
  parts[part] = (event.target as HTMLInputElement | HTMLSelectElement).value;
  if (Number(parts.day) > daysInMonth.value) parts.day = String(daysInMonth.value);
  emit("update:modelValue", dateValue.value);
}

function clear() {
  Object.assign(parts, { year: "", month: "", day: "" });
  emit("update:modelValue", "");
}
</script>

<template>
  <fieldset class="date-field">
    <legend>{{ label }}</legend>
    <div class="date-parts">
      <label>年<input
        :value="parts.year"
        type="number"
        inputmode="numeric"
        min="1"
        max="9999"
        step="1"
        placeholder="YYYY"
        :required="required || hasValue"
        @input="update('year', $event)"
        @change="update('year', $event)"
      /></label>
      <label>月<select :value="parts.month" :required="required || hasValue" @change="update('month', $event)">
        <option value="">选择月</option>
        <option v-for="month in 12" :key="month" :value="String(month)">{{ month }} 月</option>
      </select></label>
      <label>日<select :value="parts.day" :required="required || hasValue" @change="update('day', $event)">
        <option value="">选择日</option>
        <option v-for="day in daysInMonth" :key="day" :value="String(day)">{{ day }} 日</option>
      </select></label>
    </div>
    <div class="date-summary">
      <span aria-live="polite">{{ dateValue || (hasValue ? '请补全日期' : '未设置日期') }}</span>
      <button v-if="!required && hasValue" type="button" class="text-link" @click="clear">清空日期</button>
    </div>
  </fieldset>
</template>

<style scoped>
.date-field { min-width: 0; margin: 0; padding: 0; border: 0; }
.date-field legend { padding: 0; margin-bottom: 10px; font-size: 13px; }
.date-parts { display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 10px; }
.date-parts label { min-width: 0; font-size: 12px; }
.date-parts input, .date-parts select {
  width: 100%; min-width: 0; min-height: 44px; margin-top: 6px; padding: 10px 8px;
  border: 1px solid var(--line); border-radius: 8px; background: #fffdfa; color: inherit; font-size: 16px;
}
.date-summary { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; margin-top: 8px; font-size: 12px; }
.date-summary > span { font-variant-numeric: tabular-nums; color: var(--muted); }
.date-summary button { min-height: 36px; }
</style>
