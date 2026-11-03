<script setup lang="ts">
withDefaults(defineProps<{ name: string; size?: number }>(), { size: 20 });
const paths: Record<string, string[]> = {
  heart: [
    "M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z",
  ],
  arrow: ["M5 12h14", "m12 5 7 7-7 7"],
  chevron: ["m9 5 7 7-7 7"],
  down: ["m6 9 6 6 6-6"],
  book: [
    "M4 3h6a3 3 0 0 1 3 3v15a4 4 0 0 0-4-2H3V4a1 1 0 0 1 1-1Z",
    "M13 6a3 3 0 0 1 3-3h5v16h-5a3 3 0 0 0-3 2",
  ],
  camera: [
    "M9 4 7 7H3v14h18V7h-4l-2-3Z",
    "M16 13a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z",
  ],
  message: [
    "M21 11a9 9 0 0 1-9 9H4l-3 2 2-7a9 9 0 1 1 18-4Z",
    "M8 11h.01M12 11h.01M16 11h.01",
  ],
  list: ["M9 6h12M9 12h12M9 18h12", "m2 5 2 2 3-4m-5 8 2 2 3-4m-5 8 2 2 3-4"],
  gift: [
    "M3 8h18v4H3zM5 12v9h14v-9M12 8v13",
    "M12 8H7a3 3 0 1 1 3-3l2 3Zm0 0h5a3 3 0 1 0-3-3l-2 3Z",
  ],
  sparkles: ["m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3Z", "M20 2v4m-2-2h4"],
  calendar: ["M3 5h18v16H3zM3 10h18M7 3v4M17 3v4"],
  menu: ["M4 6h16M4 12h16M4 18h16"],
  close: ["m6 6 12 12M6 18 18 6"],
  check: ["m5 12 4 4L19 6"],
  plus: ["M12 5v14M5 12h14"],
  edit: ["m16 3 5 5L8 21H3v-5L16 3Zm-2 2 5 5"],
  trash: ["M3 6h18M5 6l1 15h12l1-15M9 6V3h6v3M10 10v7M14 10v7"],
  upload: ["M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6"],
  logout: ["M9 3H3v18h6M10 12h11m-5-5 5 5-5 5"],
  lock: ["M5 10h14v11H5zM8 10V6a4 4 0 0 1 8 0v4"],
  home: ["m3 10 9-8 9 8M5 9v12h5v-7h4v7h5V9"],
  pin: [
    "M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0Z",
    "M15 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z",
  ],
};
</script>
<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path v-for="(d, i) in paths[name] || paths.heart" :key="i" :d="d" />
  </svg>
</template>
