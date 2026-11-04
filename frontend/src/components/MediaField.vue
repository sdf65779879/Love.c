<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";
import { api, ApiError } from "../api";
import Icon from "./Icon.vue";
defineProps<{ modelValue: string; label: string; required?: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();
const busy = ref(false),
  error = ref("");
const status = ref("");
const preview = ref("");
const uploadedUrl = ref("");
let controller: AbortController | undefined;
onBeforeUnmount(() => {
  controller?.abort();
  URL.revokeObjectURL(preview.value);
});

async function prepareImage(file: File, signal: AbortSignal): Promise<Blob> {
  if (
    file.size <= 512 * 1024 ||
    !["image/jpeg", "image/png", "image/webp"].includes(file.type)
  ) return file;
  const image = await createImageBitmap(file);
  try {
    signal.throwIfAborted();
    if (image.width * image.height > 50000000) {
      throw new Error("图片不能超过 5000 万像素");
    }
    const scale = Math.min(1, 2560 / Math.max(image.width, image.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(image.width * scale));
    canvas.height = Math.max(1, Math.round(image.height * scale));
    const context = canvas.getContext("2d");
    if (!context) return file;
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    let compressed = await new Promise<Blob | null>(resolve =>
      canvas.toBlob(resolve, "image/webp", 0.78),
    );
    signal.throwIfAborted();
    if (compressed && compressed.size > 768 * 1024) {
      // Detailed photos need more reduction to avoid a multi-megabyte upload.
      const smallerScale = Math.min(scale, 1920 / Math.max(image.width, image.height));
      canvas.width = Math.max(1, Math.round(image.width * smallerScale));
      canvas.height = Math.max(1, Math.round(image.height * smallerScale));
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      compressed = await new Promise<Blob | null>(resolve =>
        canvas.toBlob(resolve, "image/webp", 0.72),
      );
      signal.throwIfAborted();
    }
    return compressed && compressed.size < file.size ? compressed : file;
  } finally {
    image.close();
  }
}

async function upload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file || busy.value) return;
  error.value = "";
  if (file.size > 30 * 1024 * 1024) {
    error.value = "图片不能超过 30MB";
    input.value = "";
    return;
  }
  busy.value = true;
  status.value = "正在处理图片…";
  const requestController = new AbortController();
  controller = requestController;
  let timedOut = false;
  const timeout = window.setTimeout(() => {
    timedOut = true;
    requestController.abort();
  }, 120000);
  try {
    const image = await prepareImage(file, requestController.signal);
    requestController.signal.throwIfAborted();
    status.value = `正在上传…（${Math.max(1, Math.round(image.size / 1024))} KB）`;
    const data = new FormData();
    data.append("file", image, image === file ? file.name : "upload.webp");
    const result = await api<{ url: string }>("/admin/upload", {
      method: "POST",
      body: data,
      signal: requestController.signal,
    });
    requestController.signal.throwIfAborted();
    URL.revokeObjectURL(preview.value);
    preview.value = URL.createObjectURL(image);
    uploadedUrl.value = result.url;
    emit("update:modelValue", result.url);
  } catch (e) {
    if (requestController.signal.aborted) {
      error.value = timedOut
        ? "上传超过两分钟，已停止。请检查网络后重新选择图片。"
        : "已取消上传，可以重新选择图片。";
    } else if (e instanceof TypeError || (e instanceof ApiError && e.status >= 500)) {
      error.value = "上传连接中断，请稍后重新选择图片。";
    } else {
      error.value = (e as Error).message;
    }
  } finally {
    window.clearTimeout(timeout);
    controller = undefined;
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
      <img v-if="modelValue" :src="modelValue === uploadedUrl ? preview : modelValue" alt="图片预览" /><label
        class="button secondary upload-button"
        ><Icon name="upload" :size="16" />{{
          busy ? status : "选择并上传图片"
        }}<input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          :disabled="busy"
          @change="upload" /></label
      ><button
        v-if="busy"
        type="button"
        class="button secondary small"
        @click="controller?.abort()"
      >取消上传</button>
      <small>JPG / PNG / WebP，最大 30MB、5000 万像素，大图自动压缩</small>
    </div>
    <p v-if="error" class="error-text" role="alert">{{ error }}</p>
  </div>
</template>
