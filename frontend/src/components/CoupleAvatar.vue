<script setup lang="ts">
import { computed, ref, watch } from "vue";

const props = defineProps<{ qq?: string; custom?: string; partner: "boy" | "girl"; alt: string }>();
const emit = defineEmits<{ unavailable: [unavailable: boolean] }>();
const sources = computed(() => {
  const account = props.qq?.trim() || "";
  const qqUrl = /^[1-9][0-9]{4,10}$/.test(account)
    ? `https://q1.qlogo.cn/g?b=qq&nk=${account}&s=100` : "";
  return [...new Set([qqUrl, props.custom, `/images/${props.partner}.svg`].filter(Boolean))] as string[];
});
const index = ref(0);
watch(sources, () => { index.value = 0; emit("unavailable", false); }, { flush: "sync" });
function fallback() {
  if (index.value === 0 && sources.value[0]?.startsWith("https://q1.qlogo.cn/"))
    emit("unavailable", true);
  if (index.value < sources.value.length - 1) index.value++;
}
</script>
<template>
  <img :key="sources[index]" :src="sources[index]" :alt="alt" referrerpolicy="no-referrer" @error="fallback" />
</template>
