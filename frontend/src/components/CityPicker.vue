<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { loadAtlas, type Atlas } from "../atlas";
const props = defineProps<{ modelValue: string; region?: string }>();
const emit = defineEmits<{ "update:modelValue": [value: string]; "update:region": [value: string] }>();
const atlas = ref<Atlas>(), region = ref(props.region || ""), error = ref("");
const cities = computed(() => atlas.value?.cities.filter(c => c.region === region.value) || []);
async function load() {
  try {
    atlas.value = await loadAtlas();
    region.value = atlas.value.cities.find(c => c.id === props.modelValue)?.region
      || (atlas.value.regions.some(r => r.id === props.region) ? props.region! : "");
    error.value = "";
  } catch(e) { error.value = (e as Error).message; }
}
onMounted(load);
</script>
<template>
  <div class="couple-fields city-picker">
    <label>省份 / 地区<select v-model="region" required @change="emit('update:region', region); emit('update:modelValue','')"><option disabled value="">请选择地区</option><option v-for="r in atlas?.regions" :key="r.id" :value="r.id">{{ r.name }}</option></select></label>
    <label>城市<select required :value="modelValue" @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"><option disabled value="">请选择城市</option><option v-for="c in cities" :key="c.id" :value="c.id">{{ c.name }}</option></select></label>
    <p v-if="error" role="alert">{{ error }} <button type="button" @click="load">重试</button></p>
  </div>
</template>
<style scoped>select { width:100%; padding:11px; border:1px solid var(--line); border-radius:8px; background:#fffdfa; color:inherit; font:inherit }</style>
