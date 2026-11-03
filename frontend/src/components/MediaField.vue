<script setup lang="ts">
import { ref } from "vue";
import { api } from "../api";
import Icon from "./Icon.vue";
defineProps<{ modelValue: string; label: string; required?: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();
const busy = ref(false),
  error = ref("");
async function upload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  error.value = "";
  if (file.size > 8 * 1024 * 1024) {
    error.value = "图片不能超过 8MB";
    input.value = "";
    return;
  }
  busy.value = true;
  try {
    const data = new FormData();
    data.append("file", file);
    const result = await api<{ url: string }>("/admin/upload", {
      method: "POST",
      body: data,
    });
    emit("update:modelValue", result.url);
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    busy.value = false;
    input.value = "";
  }
}
</script>
<template>
  <div class="media-field">
    <label
      >{{ label
      }}<input
        :value="modelValue"
        :required="required"
        maxlength="500"
        placeholder="上传图片，或输入 https:// 图片地址"
        @input="
          emit('update:modelValue', ($event.target as HTMLInputElement).value)
        "
    /></label>
    <div class="media-controls">
      <img v-if="modelValue" :src="modelValue" alt="图片预览" /><label
        class="button secondary upload-button"
        ><Icon name="upload" :size="16" />{{
          busy ? "正在上传…" : "选择并上传图片"
        }}<input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          :disabled="busy"
          @change="upload" /></label
      ><small>JPG / PNG / WebP，最大 8MB</small>
    </div>
    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
  </div>
</template>
