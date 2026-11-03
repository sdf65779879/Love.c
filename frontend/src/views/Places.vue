<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { allMemories, dateLabel, type Entry } from "../api";
import { loadAtlas, type Atlas } from "../atlas";
import Icon from "../components/Icon.vue";
import Modal from "../components/Modal.vue";
import "../memories.css";

const atlas = ref<Atlas>(), entries = ref<Entry[]>([]), busy = ref(true), error = ref("");
const region = ref(""), city = ref(""), photo = ref<Entry | null>(null);
const nationalView = "0 -10 660 640";
const viewBox = ref(nationalView), svg = ref<SVGSVGElement>();
const cityIndex = computed(() => new Map(atlas.value?.cities.map(c => [c.id, c])));
const visited = computed(() => new Set(entries.value.map(item => item.city_id)));
const litRegions = computed(() => new Set([...visited.value].map(id => cityIndex.value.get(id || "")?.region)));
const markers = computed(() => atlas.value?.cities.filter(c => visited.value.has(c.id) && (!region.value || c.region === region.value)) || []);
const visible = computed(() => entries.value.filter(item => (!region.value || cityIndex.value.get(item.city_id || "")?.region === region.value) && (!city.value || item.city_id === city.value)));
const regionName = computed(() => atlas.value?.regions.find(r => r.id === region.value)?.name);
function selectRegion(id: string) {
  region.value = id;
  city.value = "";
  const path = id && svg.value?.querySelector<SVGGraphicsElement>(`[data-region="${id}"]`);
  if (!path) { viewBox.value = nationalView; return; }
  const b = path.getBBox();
  const pad = Math.max(b.width, b.height) * 0.08;
  viewBox.value = [b.x - pad, b.y - pad, b.width + 2 * pad, b.height + 2 * pad].join(" ");
}
function selectCity(id: string) {
  selectRegion(cityIndex.value.get(id)?.region || "");
  city.value = id;
}
async function load() {
  busy.value = true; error.value = "";
  try { [atlas.value, entries.value] = await Promise.all([loadAtlas(), allMemories("places")]); }
  catch(e) { error.value = (e as Error).message; }
  finally { busy.value = false; }
}
onMounted(load);
</script>
<template>
  <div class="container page-container">
    <header class="page-title"><p class="section-kicker">OUR FOOTPRINTS</p><h1>走过的地方</h1><p>把一路上的风景，收进我们两个人的地图。</p></header>
    <p v-if="busy" class="status-block">正在展开地图…</p>
    <div v-else-if="error" class="status-block" role="alert">{{ error }}<button class="button secondary" @click="load">重试</button></div>
    <template v-else-if="atlas">
      <div class="travel-layout">
        <section class="panel atlas-paper">
          <div class="memory-summary"><div><p class="section-kicker">TRAVEL JOURNAL</p><h2>{{ regionName || '我们的足迹地图' }}</h2></div><button v-if="region" class="text-link" @click="selectRegion('')">← 全国地图</button></div>
          <svg ref="svg" class="travel-map" :viewBox="viewBox" role="group" aria-label="中国足迹地图，点击省份查看旅行记录">
            <path v-for="r in atlas.regions" :key="r.id" :d="r.path" :data-region="r.id" :class="{lit:litRegions.has(r.id), selected:region===r.id}" fill-rule="evenodd" vector-effect="non-scaling-stroke" @click="selectRegion(r.id)"><title>{{ r.name }}</title></path>
            <path v-if="!region" :d="atlas.outline" class="map-outline" vector-effect="non-scaling-stroke" />
            <circle v-for="c in markers" :key="c.id" :cx="c.point[0]" :cy="c.point[1]" :r="region ? Math.max(0.08, Number(viewBox.split(' ')[2])/100) : 3.7" @click.stop="selectCity(c.id)"><title>{{ c.name }}</title></circle>
          </svg>
          <p class="map-legend"><i/> 已点亮 {{ litRegions.size }} 个地区 · {{ visited.size }} 座城市</p>
        </section>
        <section class="panel travel-list">
          <p class="section-kicker">POSTCARDS</p><h2>旅行手记 <small>{{ visible.length }} 条</small></h2>
          <div class="memory-filters"><label>地区<select :value="region" @change="selectRegion(($event.target as HTMLSelectElement).value)"><option value="">全部地区</option><option v-for="r in atlas.regions" :key="r.id" :value="r.id">{{ r.name }}</option></select></label>
          <label>城市<select v-model="city"><option value="">全部城市</option><option v-for="c in markers" :key="c.id" :value="c.id">{{ c.name }}</option></select></label></div>
          <p v-if="!visible.length" class="memory-empty">{{ entries.length ? '这个地区还没有手记。' : '地图还是空白的。去后台「走过的地方」，记下你们一起抵达的第一站吧。' }}</p>
          <article v-for="item in visible" :key="item.id" class="travel-entry"><small>{{ dateLabel(item.date) }} · {{ cityIndex.get(item.city_id || '')?.name }}</small><h3>{{ item.title }}</h3><p class="preserve">{{ item.description }}</p><button v-if="item.image" class="place-photo" @click="photo=item"><img :src="item.image" :alt="item.title" loading="lazy" /></button></article>
        </section>
      </div>
    </template>
    <Modal v-if="photo" :title="photo.title" @close="photo=null"><img :src="photo.image" :alt="photo.title" /></Modal>
  </div>
</template>
