<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import Icon from "./Icon.vue";
defineProps<{ title: string; wide?: boolean }>();
const emit = defineEmits<{ close: [] }>();
const dialog = ref<HTMLDialogElement>();
const previousFocus = document.activeElement as HTMLElement | null;
onMounted(() => {
  dialog.value?.showModal();
  document.body.style.overflow = "hidden";
});
onUnmounted(() => {
  document.body.style.overflow = "";
  previousFocus?.focus();
});
</script>
<template>
  <Teleport to="body"
    ><dialog
      ref="dialog"
      :class="['modal', { wide }]"
      aria-labelledby="modal-title"
      @cancel.prevent="emit('close')"
      @click="$event.target === dialog && emit('close')"
    >
      <div class="modal-head">
        <h2 id="modal-title">{{ title }}</h2>
        <button
          class="icon-button"
          aria-label="关闭弹窗"
          @click="emit('close')"
        >
          <Icon name="close" />
        </button>
      </div>
      <slot /></dialog
  ></Teleport>
</template>
